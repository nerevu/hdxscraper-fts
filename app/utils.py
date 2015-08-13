#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: sw=4:ts=4:expandtab

"""
utils
~~~~~

Provides miscellaneous utility methods
"""

from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals)

import time
import schedule as sch
import smtplib
import logging
import requests
import itertools as it
import scraperwiki

from os import environ, path as p
from datetime import datetime as dt
from email.mime.text import MIMEText

from urllib2 import urlopen
from ijson import items
from termcolor import colored as color
from slugify import slugify

_basedir = p.dirname(__file__)
_parentdir = p.dirname(_basedir)
_schedule_time = '10:30'
_recipient = 'reubano@gmail.com'

logger = logging.getLogger('hdxscraper-fts')
underscorify = lambda fields: [slugify(f, separator='_') for f in fields]


def _make_requirements(obj):
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
    black_list = {'Region', 'none', '', None}

    if countries in black_list:
        r = requests.get(url)

        if 'grouping' in r.json():
            all_countries = (p['type'] for p in r.json()['grouping'])
        else:
            all_countries = (p['country'] for p in r.json())

        func = lambda x: x not in black_list
        country_set = set(it.ifilter(func, all_countries))

        if country_set:
            countries = '"%s"' % '","'.join(country_set)
        else:
            countries = 'N/A'

    return countries


def send_email(_to, _from=None, subject=None, text=None):
    user = environ.get('user')
    _from = _from or '%s@scraperwiki.com' % user
    subject = subject or 'scraperwiki box %s failed' % user
    text = text or 'https://scraperwiki.com/dataset/%s' % user
    msg = MIMEText(text)
    msg['Subject'], msg['From'], msg['To'] = subject, _from, _to

    # Send the message via our own SMTP server, but don't
    # include the envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(_from, [_to], msg.as_string())
    s.quit()


def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.exception(str(e))
            scraperwiki.status('error', 'Error collecting data')

            with open(p.join(_parentdir, 'http', 'log.txt'), 'rb') as f:
                send_email(_recipient, text=f.read())
        else:
            scraperwiki.status('ok')

    return wrapper


def run_or_schedule(job, schedule=False, exception_handler=None):
    job()

    if schedule:
        job = exception_handler(job) if exception_handler else job
        sch.every(1).day.at(_schedule_time).do(job)

        while True:
            sch.run_pending()
            time.sleep(1)


def gen_data(config, start_year=None, end_year=None, mode=False):
    """Generates historical or current data"""
    end_year = int(end_year or dt.now().year) + 1
    start_year = start_year or end_year - 1
    years = range(start_year, end_year)

    appeals_mode = mode.startswith('a')
    cluster_mode = mode.startswith('c')
    emergency_mode = mode.startswith('e')

    base = config['BASE_URL']
    suffix = config['SUFFIX']

    for year in years:
        appeals = urlopen('%s/appeal/year/%s%s' % (base, year, suffix))
        emergencies = urlopen('%s/emergency/year/%s%s' % (
            base, year, suffix))

        if appeals_mode or cluster_mode:
            data_items = items(appeals, config['DATA_LOCATION'])
            emergency_items = items(
                emergencies, config['DATA_LOCATION'])
            emergency_lookup = {
                e['id']: e['title'] for e in emergency_items}
        else:
            data_items = items(emergencies, config['DATA_LOCATION'])

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
                yield merge(record, _make_requirements(item))
            else:
                url = '%s/cluster/appeal/%s%s' % (base, appeal_id, suffix)
                r = requests.get(url)

                for cluster in r.json():
                    additional = _make_requirements(cluster)
                    additional['cluster'] = cluster['name']
                    yield merge(record, additional)


def prompt(ptype):
    dictionary = {
        'bullet': color(" →", "blue", attrs=['bold']),
        'error': color(" ERROR:", "red", attrs=['bold']),
        'success': color(" SUCCESS:", "green", attrs=['bold']),
        'warn': color(" WARN:", "yellow", attrs=['bold'])
    }

    return dictionary[ptype].decode('utf-8')


def merge(*args):
    return dict(it.chain.from_iterable(it.imap(dict.iteritems, args)))


def flatten_fields(record, key=None):
    try:
        for subkey, value in record.items():
            newkey = '%s_%s' % (key, subkey) if key else subkey

            for tup in flatten_fields(value, newkey):
                yield tup
    except AttributeError:
        yield (key, record)


def chunk(iterable, chunksize=0, start=0, stop=None):
    """Groups data into fixed-length chunks.
    http://stackoverflow.com/a/22919323/408556

    Args:
        iterable (iterable): Content to group into chunks.
        chunksize (Optional[int]): Number of chunks to include in a group (
            default: 0, i.e., all).

        start (Optional[int]): Starting item (zero indexed, default: 0).
        stop (Optional[int]): Ending item (zero indexed).

    Returns:
        Iter[List]: Chunked content.

    Examples:
        >>> chunk([1, 2, 3, 4, 5, 6], 2, 1).next()
        [2, 3]
    """
    i = it.islice(iter(iterable), start, stop)

    if chunksize:
        generator = (list(it.islice(i, chunksize)) for _ in it.count())
        chunked = it.takewhile(bool, generator)
    else:
        chunked = [list(i)]

    return chunked
