#!/usr/bin/env python
"""Script for testing"""

import requests


def test_healthcheck():
    response = requests.get('http://localhost:5000/')
    assert response.status_code == 200
    assert response.text == 'OK'
