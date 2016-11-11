# -*- coding: utf-8 -*-
# vim: sw=4:ts=4:expandtab

"""
config
~~~~~~

Provides app configuration settings
"""

from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals)

from os import path as p

BASEDIR = p.dirname(__file__)
PARENTDIR = p.dirname(BASEDIR)
DB_NAME = 'scraperwiki.sqlite'
RECIPIENT = 'reubano@gmail.com'


class Config(object):
    BASE_URL = 'http://fts.unocha.org/api/v1'
    SUFFIX = '.json'
    TABLES = [
        {'name': 'emergency', 'rid': 'emergency_id', 'location': 'item'},
        {'name': 'appeal', 'rid': 'appeal_id', 'location': 'item'},
        {'name': 'cluster', 'rid': 'appeal_id', 'location': 'item'}]

    SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % p.join(BASEDIR, DB_NAME)
    LOGFILE = p.join(BASEDIR, 'http', 'log.txt')
    SW = False
    DEBUG = False
    TESTING = False
    PROD = False
    CHUNK_SIZE = 2 ** 14
    ROW_LIMIT = None


class Scraper(Config):
    PROD = True
    SW = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % p.join(PARENTDIR, DB_NAME)
    LOGFILE = p.join(PARENTDIR, 'http', 'log.txt')


class Production(Config):
    PROD = True


class Development(Config):
    DEBUG = True
    ROW_LIMIT = 50


class Test(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    DEBUG = True
    ROW_LIMIT = 10
    TESTING = True
