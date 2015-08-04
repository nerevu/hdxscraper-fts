#!/usr/bin/env python
from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals)

import requests
import os.path as p
import itertools as it

from subprocess import call
from datetime import datetime as dt
from urllib2 import urlopen

from pprint import pprint
from ijson import items
from flask import current_app as app
from flask.ext.script import Manager
from app import create_app, db, utils
from app.models import Data

manager = Manager(create_app)
manager.add_option('-m', '--mode', dest='mode', default='Development')
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
    try:
        requirement = obj['current_requirements']
    except KeyError:
        requirement = obj['current_requirement']


    funding = obj['funding']
    coverage = funding / requirement if requirement else 0

    requirements = {
        'requirement': requirement,
        'funding': funding,
        'coverage': coverage,
    }

    return requirements


def gen_data(start_year=None, end_year=None):
    """Generates historical or current data"""
    end_year = int(end_year or dt.now().year) + 1
    start_year = start_year or end_year - 1

    years = range(start_year, end_year)

    with app.app_context():
        base = app.config['BASE_URL']
        suffix = app.config['SUFFIX']

        for year in years:
            appeals = urlopen('%s/appeal/year/%s%s' % (base, year, suffix))
            emergencies = urlopen('%s/emergency/year/%s%s' % (
                base, year, suffix))

            emergency_items = items(emergencies, app.config['DATA_LOCATION'])
            lookup = {e['id']: e['title'] for e in emergency_items}

            for appeal in items(appeals, app.config['DATA_LOCATION']):
                countries = appeal['country']
                emergency_id = appeal['emergency_id']
                appeal_id = appeal['id']

                if not countries or countries in ['Region', 'none']:
                    url = '%s/project/appeal/%s%s' % (base, appeal_id, suffix)
                    r = requests.get(url)
                    all_countries = (p['country'] for p in r.json())
                    country_set = set(it.ifilter(None, all_countries))

                    if country_set:
                        countries = '"%s"' % '","'.join(country_set)
                    else:
                        countries = 'N/A'

                record = {
                    'emergency_id': emergency_id,
                    'emergency_name': lookup.get(emergency_id, 'N/A'),
                    'countries': countries,
                    'year': appeal['year'],
                    'appeal_id': appeal_id,
                    'appeal_name': appeal['title'],
                    'funding_type': appeal['type'],
                }

                yield utils.merge(record, _make_requirements(appeal))
                url = '%s/cluster/appeal/%s%s' % (base, appeal_id, suffix)
                r = requests.get(url)

                for cluster in r.json():
                    additional_cluster = _make_requirements(cluster)
                    additional_cluster['cluster'] = cluster['name']
                    yield utils.merge(record, additional_cluster)

@manager.option('-s', '--start', help='the start year', default=1999)
@manager.option('-e', '--end', help='the end year', default=None)
def backfill(start, end):
    """Populates db with historical data"""
    limit = 0

    with app.app_context():
        row_limit = app.config['ROW_LIMIT']
        chunk_size = min(row_limit or 'inf', app.config['CHUNK_SIZE'])
        debug = app.config['DEBUG']
        test = app.config['TESTING']

        if test:
            createdb()

        for records in utils.chunk(gen_data(start, end), chunk_size):
            count = len(records)
            limit += count

            if debug:
                print('Inserting %s records into the database...' % count)

            if test:
                pprint(records)

            db.engine.execute(Data.__table__.insert(), records)

            if row_limit and limit >= row_limit:
                break

        if debug:
            print('Successfully inserted %s records into the database!' % limit)


@manager.command
def run():
    """Populates db with most recent data"""
    limit = 0

    with app.app_context():
        row_limit = app.config['ROW_LIMIT']
        chunk_size = min(row_limit or 'inf', app.config['CHUNK_SIZE'])
        debug = app.config['DEBUG']
        test = app.config['TESTING']

        if test:
            createdb()

        for records in utils.chunk(gen_data(), chunk_size):
            appeal_ids = [r['appeal_id'] for r in records]

            # delete records if already in db
            del_count = (
                Data.query.filter(Data.appeal_id.in_(appeal_ids))
                    .delete(synchronize_session=False))

            if debug:
                print('Deleted %s records from the database...' % del_count)

            in_count = len(records)
            limit += in_count

            if debug:
                print('Inserting %s records into the database...' % in_count)

            if test:
                pprint(records)

            db.engine.execute(Data.__table__.insert(), records)

            if row_limit and limit >= row_limit:
                break

        if debug:
            print('Successfully inserted %s records into the database!' % limit)

if __name__ == '__main__':
    manager.run()
