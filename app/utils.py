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

import requests
import itertools as it

from urllib2 import urlopen
from datetime import datetime as dt
from ijson import items
from tabutils.process import merge


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
            all_countries = (g['type'] for g in r.json()['grouping'])
        else:
            all_countries = (g['country'] for g in r.json())

        func = lambda x: x not in black_list
        country_set = set(it.ifilter(func, all_countries))

        if country_set:
            countries = '"%s"' % '","'.join(country_set)
        else:
            countries = 'N/A'

    return countries


def gen_data(start_year=None, end_year=None, mode=False, **kwargs):
    """Generates historical or current data"""
    end_year = int(end_year or dt.now().year) + 1
    start_year = start_year or end_year - 1
    years = range(start_year, end_year)

    appeals_mode = mode.startswith('A')
    cluster_mode = mode.startswith('C')
    emergency_mode = mode.startswith('E')

    base = kwargs['BASE_URL']
    suffix = kwargs['SUFFIX']

    for year in years:
        appeals = urlopen('%s/appeal/year/%s%s' % (base, year, suffix))
        emergencies = urlopen('%s/emergency/year/%s%s' % (
            base, year, suffix))

        if appeals_mode or cluster_mode:
            data_items = items(appeals, kwargs['DATA_LOCATION'])
            emergency_items = items(
                emergencies, kwargs['DATA_LOCATION'])
            emergency_lookup = {
                e['id']: e['title'] for e in emergency_items}
        else:
            data_items = items(emergencies, kwargs['DATA_LOCATION'])

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
