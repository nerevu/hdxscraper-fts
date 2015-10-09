#!/usr/bin/env python
from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals)

import os.path as p

from subprocess import call
from datetime import datetime as dt
from functools import partial

from pprint import pprint
from flask import current_app as app
from flask.ext.script import Manager
from tabutils.fntools import chunk

from app import create_app, db, utils, models

manager = Manager(create_app)
manager.add_option('-m', '--mode', default='Development')
manager.main = manager.run

_basedir = p.dirname(__file__)


@manager.command
def check():
    """Check staged changes for lint errors"""
    call(p.join(_basedir, 'bin', 'check-stage'), shell=True)


@manager.command
def lint():
    """Check style with flake8"""
    call('flake8', shell=True)


@manager.command
def pipme():
    """Install requirements.txt"""
    call('sudo pip install -r requirements.txt', shell=True)


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

        args = [app.config, start, end, dmode]
        for records in chunk(utils.gen_data(*args), chunk_size):
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


@manager.option(
    '-d', '--dmode', help='data mode', default='emergency',
    choices=['emergency', 'appeal', 'cluster'])
def populate(dmode):
    """Populates db with most recent data"""
    limit = 0
    table_name = dmode.capitalize()
    table = getattr(models, table_name)
    rid = 'emergency_id' if dmode.startswith('e') else 'appeal_id'

    with app.app_context():
        row_limit = app.config['ROW_LIMIT']
        chunk_size = min(row_limit or 'inf', app.config['CHUNK_SIZE'])
        debug, test = app.config['DEBUG'], app.config['TESTING']

        if test:
            createdb()

        data = utils.gen_data(app.config, mode=dmode)
        for records in chunk(data, chunk_size):
            # delete records if already in db
            ids = [r[rid] for r in records]
            q = table.query.filter(getattr(table, rid).in_(ids))
            del_count = q.delete(synchronize_session=False)

            # necessary to prevent `sqlalchemy.exc.OperationalError:
            # (sqlite3.OperationalError) database is locked` error
            db.session.commit()

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


@manager.command
def init():
    """Initializes db with historical data"""
    with app.app_context():
        func = partial(backfill, 1999, dt.now().year)
        job = partial(map, func, ['emergency', 'appeal', 'cluster'])
        utils.run_or_schedule(job, False, utils.exception_handler)


@manager.command
def run():
    """Populates all tables in db with most recent data"""
    with app.app_context():
        job = partial(map, populate, ['emergency', 'appeal', 'cluster'])
        utils.run_or_schedule(job, app.config['SW'], utils.exception_handler)


if __name__ == '__main__':
    manager.run()
