
import json
import random

from webob import Request


def make_request(data, method='POST'):
    """ Make a webob JSON Request """
    request = Request.blank('/')
    request.method = 'POST'
    data = json.dumps(data).encode('utf-8') if data is not None else b''
    request.body = data
    request.method = method
    return request


def generate_max_and_attempts(count=100):
    for _ in range(count):
        max_attempts = random.randint(1, 100)
        attempts = random.randint(0, 100)
        expect_validation_error = max_attempts <= attempts
        yield max_attempts, attempts, expect_validation_error
