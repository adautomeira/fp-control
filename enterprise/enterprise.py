#!/usr/bin/env python
"""Lambda function to process Enterprise Entities"""

import os
from datetime import datetime
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

if os.getenv('RDS_HOST') is not None:
    DB_HOST = os.environ['RDS_HOST']
else:
    DB_HOST = 'db-pf-control-dev.cr1aajft55dd.us-east-1.rds.amazonaws.com'

DB_NAME = 'pf_control_enterprise'
DB_USER = 'usr_pf_master'
DB_PASS = os.environ['SECRET']
DB_CONNECTOR = 'mysql+mysqlconnector'
DB_URI = '%s://%s:%s@%s/%s' % (DB_CONNECTOR, DB_USER, DB_PASS, DB_HOST,
                               DB_NAME)
APP = Flask(__name__)
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
APP.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
DB = SQLAlchemy(APP)
MA = Marshmallow(APP)


class Enterprise(DB.Model):
    """Class used to connect to the source"""
    id = DB.Column(DB.Integer, primary_key=True)
    referer = DB.Column(DB.String(36), nullable=False)
    name = DB.Column(DB.String(255), nullable=False)
    created_at = DB.Column(DB.DateTime, nullable=False,
                           default=datetime.utcnow)
    modified = DB.Column(DB.DateTime)


class EnterpriseSchema(MA.ModelSchema):
    """Class used to hold all the logic"""
    class Meta:
        """SO META! SO LOGIC!"""
        model = Enterprise


ENTERPRISE_SCHEMA = EnterpriseSchema()
ENTERPRISES_SCHEMA = EnterpriseSchema(many=True)


@APP.route('/api/enterprise')
def enterprises():
    """Function to list all existent Enterprises"""
    all_enterprises = Enterprise.query.all()
    result = ENTERPRISES_SCHEMA.dump(all_enterprises)
    return jsonify(result.data)


@APP.route('/api/enterprise/<ref>')
def get(ref):
    """Function to show a Enterprise by its referer"""
    enterprise = Enterprise.query.filter_by(referer=ref).first()
    return ENTERPRISE_SCHEMA.jsonify(enterprise)
