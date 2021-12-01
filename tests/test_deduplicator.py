import pytest

from anomaly_detector.config import Configuration
from anomaly_detector.core.deduplicator import LogDeduplicator
from anomaly_detector.storage.storage_attribute import MGStorageAttribute
from anomaly_detector.storage.mongodb_storage import MongoDBDataStorageSource

@pytest.fixture()
def config():
    """Initialize configurations before testing."""
    cfg = Configuration()
    cfg.MG_HOST = "172.17.18.83"
    cfg.MG_PORT = 27017
    cfg.MG_CERT_DIR = ""
    cfg.MG_INPUT_DB = "anomalydb"
    cfg.MG_INPUT_COL = "utm_anomaly"
    cfg.HOSTNAME_INDEX = "hostname"
    cfg.DATETIME_INDEX = "timestamp"
    cfg.MG_USER = ''
    cfg.MG_PASSWORD = ''
    cfg.DEDUP_EPS = 0.05
    cfg.DEDUP_MIN_SAMPLES = 2
    return cfg

@pytest.fixture()
def getlogs(config):
    mg_attr = MGStorageAttribute(2592000, 1000)
    mg = MongoDBDataStorageSource(config)
    logs = mg.retrieve(mg_attr)[1]
    return logs

def test_encoder(config, getlogs):
    dedup = LogDeduplicator(config)
    dedup.encode_logs(getlogs)
    assert len(dedup.vectors) > 0

def test_clustering(config, getlogs):
    dedup = LogDeduplicator(config)
    dedup.encode_logs(getlogs)
    dedup.add_clusters()

    outliers = len(dedup.df_logs.loc[dedup.df_logs["clusters"] == -1])
    total = len(dedup.df_logs)
    # True if outliers number is less that 0.1%
    assert outliers/total <= 0.001*total
