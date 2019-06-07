import os
from flask import Flask

if os.environ['RDS_USERNAME'] is set:
    db_username = os.environ['RDS_USERNAME']
else:
    db_username = 'usr_pf_master'

app = Flask(__name__, instance_relative_config=True)


@app.route('/enterprise')
def list():
    return 'Hello, World!'


@app.route('/enterprise/<id>')
def get():
    return 'Hello, World!'
