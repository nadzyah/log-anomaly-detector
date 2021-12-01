"""Test MongoDB module to read data."""
#import sys
#sys.path.append('/home/nadzya/Apps/log-anomaly-detector/')

import pytest
from anomaly_detector.storage.mongodb_storage import MongoDBDataStorageSource
from anomaly_detector.config import Configuration
from anomaly_detector.storage.storage_attribute import MGStorageAttribute


@pytest.fixture()
def config():
    """Initialize configurations before testing."""
    cfg = Configuration()
    cfg.MG_HOST = "172.17.18.83"
    cfg.MG_PORT = 27017
    cfg.MG_CERT_DIR = ""
    cfg.MG_INPUT_DB = "fluentdb"
    cfg.MG_INPUT_COL = "web_logs"
    cfg.HOSTNAME_INDEX = "hostname"
    cfg.DATETIME_INDEX = "timestamp"
    cfg.LOGSOURCE_HOSTNAME = "data.solidex.by"
    cfg.MG_USER = ''
    cfg.MG_PASSWORD = ''
    return cfg


def test_mg(config):
    """Test ability to read data from MongoDB"""
    mg_attr = MGStorageAttribute(86400, 90000)
    mg = MongoDBDataStorageSource(config)

    data = mg.retrieve(mg_attr)
    print(data[0], data[1])

    assert len(data[0]) > 0

def test_message_key(config):
    """Test if it can get message attribute from data"""
    mg_attr = MGStorageAttribute(2592000, 900000)
    mg = MongoDBDataStorageSource(config)
    mg_data_msg = mg.retrieve(mg_attr)[0]

    assert len(mg_data_msg['message']) > 0

def test_data_not_str_type(config):
    """Test if data from mongodb is in json-object format, not str"""
    mg_attr = MGStorageAttribute(2592000, 900000)
    mg = MongoDBDataStorageSource(config)
    mg_data = mg.retrieve(mg_attr)[1]

    assert not isinstance(mg_data, str)
