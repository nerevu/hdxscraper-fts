# -*- coding: utf-8 -*-
"""
    app.models
    ~~~~~~~~~~

    Provides the SQLAlchemy models
"""
from __future__ import (
    absolute_import, division, print_function, with_statement,
    unicode_literals)

import savalidation.validators as val

from datetime import datetime as dt
from app import db
from savalidation import ValidationMixin


class Emergency(db.Model, ValidationMixin):
    # auto keys
    id = db.Column(db.Integer, primary_key=True)
    utc_created = db.Column(db.DateTime, nullable=False, default=dt.utcnow())
    utc_updated = db.Column(
        db.DateTime, nullable=False, default=dt.utcnow(), onupdate=dt.utcnow())

    # other keys
    emergency_id = db.Column(
        db.String(16), nullable=False, index=True)
    emergency_name = db.Column(db.String(32), nullable=False)
    countries = db.Column(db.String(256), nullable=False)
    year = db.Column(db.String(4), nullable=False)
    funding = db.Column(db.Numeric, nullable=False)

    # validation
    val.validates_constraints()

    def __repr__(self):
        return ('<Emergency(%r)>' % (self.emergency_id))


class Appeal(db.Model, ValidationMixin):
    # auto keys
    id = db.Column(db.Integer, primary_key=True)
    utc_created = db.Column(db.DateTime, nullable=False, default=dt.utcnow())
    utc_updated = db.Column(
        db.DateTime, nullable=False, default=dt.utcnow(), onupdate=dt.utcnow())

    # other keys
    emergency_id = db.Column(db.String(16), nullable=False)
    emergency_name = db.Column(db.String(32), nullable=False)
    countries = db.Column(db.String(256), nullable=False)
    year = db.Column(db.String(4), nullable=False)
    funding = db.Column(db.Numeric, nullable=False)
    appeal_id = db.Column(
        db.String(16), nullable=False, index=True)
    appeal_name = db.Column(db.String(32), nullable=False)
    requirement = db.Column(db.Numeric, nullable=False)
    coverage = db.Column(db.Numeric, nullable=False)
    funding_type = db.Column(db.String(16), nullable=False)

    # validation
    val.validates_constraints()

    def __repr__(self):
        return ('<Appeal(%r)>' % (self.appeal_name))


class Cluster(db.Model, ValidationMixin):
    # auto keys
    id = db.Column(db.Integer, primary_key=True)
    utc_created = db.Column(db.DateTime, nullable=False, default=dt.utcnow())
    utc_updated = db.Column(
        db.DateTime, nullable=False, default=dt.utcnow(), onupdate=dt.utcnow())

    # other keys
    emergency_id = db.Column(db.String(16), nullable=False)
    emergency_name = db.Column(db.String(32), nullable=False)
    countries = db.Column(db.String(256), nullable=False)
    year = db.Column(db.String(4), nullable=False)
    funding = db.Column(db.Numeric, nullable=False)
    appeal_id = db.Column(db.String(16), nullable=False, index=True)
    appeal_name = db.Column(db.String(32), nullable=False)
    requirement = db.Column(db.Numeric, nullable=False)
    coverage = db.Column(db.Numeric, nullable=False)
    funding_type = db.Column(db.String(16), nullable=False)
    cluster = db.Column(db.String(32), nullable=False)

    # validation
    val.validates_constraints()

    def __repr__(self):
        return ('<Cluster(%r, %r)>' % (self.appeal_name, self.cluster))
