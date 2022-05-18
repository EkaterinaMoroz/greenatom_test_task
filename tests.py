import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import models
from database import Base
from main import app, get_db
from main import client as minio

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://tester:111@db:5432/tester"
# SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://tester:111@localhost:5432/tester"


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine


@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection)
    # db = Session(db_engine)
    yield db

    db.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c


url = 'http://localhost:8000/frames'
files = [('files', open('images1.jpeg', 'rb')),
         ('files', open('images2.jpeg', 'rb'))]


def test_upload(client):
    response = client.post(url=url, files=files)
    assert response.status_code == 200
    assert response.json()["filenames"] != []


def test_get_files(db, client):
    client.post(url=url, files=files)
    test_request_id = db.query(models.File).order_by(models.File.request_id.desc()).first().request_id
    response = client.get(url + '/' + f'{test_request_id}')
    assert response.status_code == 200
    assert response.json()["files"] != []


def test_delete_files(db, client):
    client.post(url=url, files=files)
    test_request_id = db.query(models.File).order_by(models.File.request_id.desc()).first().request_id
    response = client.delete(url + '/' + f'{test_request_id}')
    assert response.status_code == 200
    assert response.json() == {"removed": True}


def test_get_files_not_found(client):
    test_request_id = 0
    response = client.get(url + '/' + f'{test_request_id}')
    assert response.status_code == 400
    assert response.json() == {"detail": "No item found"}


def test_delete_files_not_found_in_db(client):
    test_request_id = 0
    response = client.delete(url + '/' + f'{test_request_id}')
    assert response.status_code == 404
    assert response.json() == {
        "removed": False,
        "error_message": "File not found in database"
    }


def test_delete_files_no_bucket(client, db):
    client.post(url=url, files=files)
    test_request_id = db.query(models.File).order_by(models.File.request_id.desc()).first().request_id
    bucketname = test_request_id[:10].replace('-', '')
    delete_object_list = [obj.object_name for obj in minio.list_objects(bucketname)]
    for obj in delete_object_list:
        minio.remove_object(bucketname, obj)
    minio.remove_bucket(bucketname)
    response = client.delete(url + '/' + f'{test_request_id}')
    assert response.status_code == 404
    assert response.json() == {"removed": False, "error_message": "No such Bucket!"}


def test_delete_files_not_found_in_bucket(client, db):
    client.post(url=url, files=files)
    test_request_id = db.query(models.File).order_by(models.File.request_id.desc()).first().request_id
    bucketname = test_request_id[:10].replace('-', '')
    delete_object_list = [obj.object_name for obj in minio.list_objects(bucketname)]
    for obj in delete_object_list:
        minio.remove_object(bucketname, obj)
    response = client.delete(url + '/' + f'{test_request_id}')
    assert response.status_code == 404
    assert response.json() == {
        "removed": False,
        "error_message": "File in bucket not found"
    }
