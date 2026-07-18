import json
import os
from flask import Flask
import pytest
import logging
import responses
from routes.flaskr import create_app

log = logging.getLogger(__name__)

app = Flask(__name__)
create_app(app)


@pytest.fixture
def client():
    app.config['TESTING'] = True

    with app.test_client() as fclient:
        yield fclient


def test_handle_default_route(client):
    request = client.get('/')
    data = json.loads(request.data)
    assert (data['status'] == "OK")


@responses.activate
def test_handle_items_fetch(client):
    mock_response = {
        "docs": [
            {
                "_id": "customer:123456789",
                "_rev": "1-123456789",
                "subscription": "PREMIUM",
                "type": "paid_customer",
                "name": "John Mike",
                "occupation": "Software Eng",
            }
        ],
        "bookmark": "g1123123424211233221",
    }
    responses.add(
        responses.POST,
        '{}/customers/_find'.format(os.environ.get("COUCHDB_URL")),
        json=mock_response,
        status=200,
    )

    request = client.get('/api/customer')
    data = json.loads(request.data)
    assert (data['status'] == 'OK')
    assert 'customers' in data
    assert '_id' in data['customers'][0]


@responses.activate
def test_handle_items_post(client):
    responses.add(
        responses.POST,
        '{}/customers/_bulk_docs'.format(os.environ.get("COUCHDB_URL")),
        status=201,
    )

    request = client.post('/api/customer', json={
        'name': 'John Mike',
        'occupation': 'Software Eng'
    })

    response_data = json.loads(request.data)
    assert response_data['status'] == "USER CREATED"


@responses.activate
def test_handle_items_delete(client):
    mock_customer_id = 'customer:123456789'

    responses.add(
        responses.HEAD,
        '{0}/customers/{1}'.format(os.environ.get("COUCHDB_URL"), mock_customer_id),
        status=200,
    )

    request = client.delete('/api/customer', json={
        'id': mock_customer_id,
    })

    response_data = json.loads(request.data)
    assert request.status_code == 200
    assert response_data['status'] == "DOCUMENT DELETED"
