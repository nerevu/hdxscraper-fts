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

import itertools as it

from termcolor import colored as color
from slugify import slugify


underscorify = lambda fields: [slugify(f, separator='_') for f in fields]


def prompt(ptype):
    dictionary = {
        'bullet': color(" →", "blue", attrs=['bold']),
        'error': color(" ERROR:", "red", attrs=['bold']),
        'success': color(" SUCCESS:", "green", attrs=['bold']),
        'warn': color(" WARN:", "yellow", attrs=['bold'])
    }

    return dictionary[ptype].decode('utf-8')


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
