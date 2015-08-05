#!/usr/bin/env python
from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals)

import requests
import scraperwiki
import os.path as p
import itertools as it

from subprocess import call
from datetime import datetime as dt
from urllib2 import urlopen
from functools import partial

from pprint import pprint
from ijson import items
from flask import current_app as app
from flask.ext.script import Manager
from app import create_app, db, utils
from app import models

manager = Manager(create_app)
manager.add_option('-m', '--mode', default='Development')
manager.main = manager.run


@manager.command
def check():
    """Check staged changes for lint errors"""
    call(p.join(_basedir, 'bin', 'check-stage'), shell=True)


@manager.command
def lint():
    """Check style with flake8"""
    call('flake8 app tests', shell=True)


@manager.command
def pipme():
    """Install requirements.txt"""
    call('pip install -r requirements.txt', shell=True)


@manager.command
def require():
    """Create requirements.txt"""
    cmd = 'pip freeze -l | grep -vxFf dev-requirements.txt > requirements.txt'
    call(cmd, shell=True)


@manager.command
def test():
    """Run nose and script tests"""
    call('nosetests -xv', shell=True)


@manager.command
def createdb():
    """Creates database if it doesn't already exist"""

    with app.app_context():
        db.create_all()
        print('Database created')


@manager.command
def cleardb():
    """Removes all content from database"""

    with app.app_context():
        db.drop_all()
        print('Database cleared')


@manager.command
def setup():
    """Removes all content from database and creates new tables"""

    with app.app_context():
        cleardb()
        createdb()

def _make_requirements(obj):
    has_requirement = True
    funding = obj['funding']

    if 'current_requirement' in obj or 'current_requirements' in obj:
        requirement = obj.get(
            'current_requirements', obj.get('current_requirement'))

        coverage = funding / requirement if requirement else 0
        requirements = {
            'requirement': requirement,
            'funding': funding,
            'coverage': coverage,
        }
    else:
        requirements = {'funding': funding}

    return requirements


def _find_countries(countries, url):
    if not countries or countries in ['Region', 'none']:
        r = requests.get(url)

        try:
            all_countries = (p['country'] for p in r.json())
        except TypeError:
            all_countries = (p['type'] for p in r.json()['grouping'])

        country_set = set(it.ifilter(None, all_countries))

        if country_set:
            countries = '"%s"' % '","'.join(country_set)
        else:
            countries = 'N/A'

    return countries


def gen_data(start_year=None, end_year=None, mode=False):
    """Generates historical or current data"""
    end_year = int(end_year or dt.now().year) + 1
    start_year = start_year or end_year - 1
    years = range(start_year, end_year)

    appeals_mode = mode.startswith('a')
    cluster_mode = mode.startswith('c')
    emergency_mode = mode.startswith('e')

    with app.app_context():
        base = app.config['BASE_URL']
        suffix = app.config['SUFFIX']

        for year in years:
            appeals = urlopen('%s/appeal/year/%s%s' % (base, year, suffix))
            emergencies = urlopen('%s/emergency/year/%s%s' % (
                base, year, suffix))

            if appeals_mode or cluster_mode:
                data_items = items(appeals, app.config['DATA_LOCATION'])
                emergency_items = items(
                    emergencies, app.config['DATA_LOCATION'])
                emergency_lookup = {
                    e['id']: e['title'] for e in emergency_items}
            else:
                data_items = items(emergencies, app.config['DATA_LOCATION'])

            for item in data_items:
                if appeals_mode or cluster_mode:
                    emergency_id = item['emergency_id']
                    emergency_name = emergency_lookup.get(emergency_id, 'N/A')
                    appeal_id = item['id']
                    url = '%s/project/appeal/%s%s' % (base, appeal_id, suffix)
                else:
                    emergency_id = item['id']
                    url = '%s/funding%s?groupby=country&emergency=%s' % (
                        base, suffix, emergency_id)
                    emergency_name = item['title']

                record = {
                    'emergency_id': emergency_id,
                    'emergency_name': emergency_name,
                    'countries': _find_countries(item['country'], url),
                    'year': item['year'],
                }

                if appeals_mode or cluster_mode:
                    record.update({
                        'appeal_id': appeal_id,
                        'appeal_name': item['title'],
                        'funding_type': item['type']})

                if appeals_mode or emergency_mode:
                    yield utils.merge(record, _make_requirements(item))
                else:
                    url = '%s/cluster/appeal/%s%s' % (base, appeal_id, suffix)
                    r = requests.get(url)
                    print(url)

                    for cluster in r.json():
                        additional = _make_requirements(cluster)
                        additional['cluster'] = cluster['name']
                        print('hi')
                        yield utils.merge(record, additional)

@manager.option('-s', '--start', help='the start year', default=1999)
@manager.option('-e', '--end', help='the end year', default=None)
@manager.option(
    '-d', '--dmode', help='data mode', default='emergency',
    choices=['emergency', 'appeal', 'cluster'])
def backfill(start, end, dmode):
    """Populates db with historical data"""
    limit = 0
    table_name = dmode.capitalize()
    table = getattr(models, table_name)

    with app.app_context():
        row_limit = app.config['ROW_LIMIT']
        chunk_size = min(row_limit or 'inf', app.config['CHUNK_SIZE'])
        debug, test = app.config['DEBUG'], app.config['TESTING']

        if test:
            createdb()

        for records in utils.chunk(gen_data(start, end, dmode), chunk_size):
            count = len(records)
            limit += count

            if debug:
                print(
                    'Inserting %s records into the %s table...' % (
                        count, table_name))

            if test:
                pprint(records)

            db.engine.execute(table.__table__.insert(), records)

            if row_limit and limit >= row_limit:
                break

        if debug:
            print(
                'Successfully inserted %s records into the %s table!' % (
                    limit, table_name))

        if app.config['PROD']:
            scraperwiki.status('ok')


@manager.option(
    '-d', '--dmode', help='data mode', default='emergency',
    choices=['emergency', 'appeal', 'cluster'])
def populate(dmode):
    """Populates db with most recent data"""
    limit = 0
    table_name = dmode.capitalize()
    table = getattr(models, table_name)
    attr = 'emergency_id' if dmode.startswith('e') else 'appeal_id'

    with app.app_context():
        row_limit = app.config['ROW_LIMIT']
        chunk_size = min(row_limit or 'inf', app.config['CHUNK_SIZE'])
        debug, test = app.config['DEBUG'], app.config['TESTING']

        if test:
            createdb()

        for records in utils.chunk(gen_data(mode=dmode), chunk_size):
            # delete records if already in db
            ids = [r[attr] for r in records]
            q = table.query.filter(getattr(table, attr).in_(ids))
            del_count = q.delete(synchronize_session=False)

            if debug:
                print(
                    'Deleted %s records from the %s table...' % (
                        del_count, table_name))

            in_count = len(records)
            limit += in_count

            if debug:
                print(
                    'Inserting %s records into the %s table...' % (
                        in_count, table_name))

            if test:
                pprint(records)

            db.engine.execute(table.__table__.insert(), records)

            if row_limit and limit >= row_limit:
                break

        if debug:
            print(
                'Successfully inserted %s records into the %s table!' % (
                    limit, table_name))

        if app.config['PROD']:
            print(app.config)
            scraperwiki.status('ok')


@manager.command
def init():
    """Initializes db with historical data"""
    with app.app_context():
        cleardb()
        createdb()

        func = partial(backfill, 1999, None)
        map(func, ['emergency', 'appeal', 'cluster'])


@manager.command
def run():
    """Populates all tables in db with most recent data"""
    with app.test_request_context():
        map(populate, ['emergency', 'appeal', 'cluster'])


if __name__ == '__main__':
    manager.run()
