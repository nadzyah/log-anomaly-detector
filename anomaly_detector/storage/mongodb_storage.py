"""MongoDB storage interface"""
import datetime
import pandas
from pymongo import MongoClient
import ssl
import os
from dateutil.parser import parse
import logging
from bson.json_util import dumps
from bson.objectid import ObjectId
from pandas.io.json import json_normalize
import json
from anomaly_detector.storage.storage import DataCleaner
from anomaly_detector.storage.storage_attribute import MGStorageAttribute
from anomaly_detector.storage.storage_source import StorageSource
from anomaly_detector.storage.storage_sink import StorageSink

_LOGGER = logging.getLogger(__name__)


class MongoDBStorage:
    """MongoDB storage backend."""

    NAME = "mg"
    _MESSAGE_FIELD_NAME = "_source.message"

    def __init__(self, config):
        """Initialize MongoDB storage backend."""
        self.config = config
        if (self.config.MG_USER and self.config.MG_PASSWORD):
            self.MG_URI = "mongodb://%s:%s@%s:%s"% (
                self.config.MG_USER,
                self.config.MG_PASSWORD,
                self.config.MG_HOST,
                self.config.MG_PORT
            )
        else:
            self.MG_URI = "mongodb://%s:%s"% (
                self.config.MG_HOST,
                self.config.MG_PORT
            )
        self._connect()

    def _connect(self):
        if len(self.config.MG_CA_CERT) and os.path.isfile(self.config.MG_CA_CERT):
            _LOGGER.warning(
                "Connection to MongoDB at %s with SSL/TLS using CA certificate in %s (verify=%s)."
                % (
                    self.config.MG_HOST,
                    self.config.MG_CA_CERT,
                    self.config.MG_VERIFY_CERT
                )
            )
            self.mg = MongoClient(
                self.MG_URI,
                tls=True,
                tlsCAFile=self.config.MG_CA_CERT,
                tlsAllowInvalidCertificates=self.config.MG_VERIFY_CERT,
                maxPoolSize=1
            )
        else:
            _LOGGER.warning("Conecting to MongoDB without SSL/TLS encryption.")
            self.mg = MongoClient(
                self.MG_URI,
                maxPoolSize=1
            )


class MongoDBDataStorageSource(StorageSource, DataCleaner, MongoDBStorage):
    """MongoDB data source implementation."""

    NAME = "mg.source"

    def __init__(self, config):
        """Initialize mongodb storage backend."""
        self.config = config
        MongoDBStorage.__init__(self, config)


    def retrieve(self, storage_attribute: MGStorageAttribute):
        """Retrieve data from MongoDB."""

        mg_db = self.mg[self.config.MG_DB]
        now = datetime.datetime.now()

        mg_data = mg_db[self.config.MG_COLLECTION]

        if self.config.LOGSOURCE_HOSTNAME != 'localhost':
            query = {
                self.config.DATETIME_INDEX:  {
                    '$gte': now - datetime.timedelta(seconds=storage_attribute.time_range),
                    #'$gte': now - datetime.timedelta(days=15),
                    '$lt': now
                },
                self.config.HOSTNAME_INDEX: self.config.LOGSOURCE_HOSTNAME
            }
        else:
            query = {
                self.config.DATETIME_INDEX:  {
                    '$gte': now - datetime.timedelta(seconds=storage_attribute.time_range),
                    #'$gte': now - datetime.timedelta(days=30),
                    '$lt': now
                }
            }

        mg_data = mg_data.find(query).sort(self.config.DATETIME_INDEX, -1).limit(storage_attribute.number_of_entries)
        _LOGGER.info(
            "Reading %d log entries in last %d seconds from %s",
            mg_data.count(True),
            storage_attribute.time_range,
            self.config.MG_HOST,
        )

        if not mg_data.count():   # if it equials 0:
            return pandas.DataFrame(), mg_data

        mg_data = dumps(mg_data, sort_keys=False)

        mg_data_normalized = pandas.DataFrame(pandas.json_normalize(json.loads(mg_data)))
        _LOGGER.info("%d logs loaded in from last %d seconds", len(mg_data_normalized),
                     storage_attribute.time_range)
        self._preprocess(mg_data_normalized)

        _LOGGER.info("Closing the connection to MongoDB")
        self.mg.close()

        return mg_data_normalized, json.loads(mg_data)


class MongoDBDataSink(StorageSink, DataCleaner, MongoDBStorage):
    """MongoDB data sink implementation."""

    NAME = "mg.sink"

    def __init__(self, config):
        """Initialize mongodb storage backend."""
        self.config = config
        MongoDBStorage.__init__(self, config)

    def store_results(self, data):
        """Store results back to MongoDB"""
        mg_db = self.mg[self.config.MG_DB]
        mg_col = mg_db[self.config.MG_COLLECTION]
        for x in data:
            if x["anomaly"]:
                mg_col.update_one({
                    '_id': ObjectId(x['_id']['$oid'])
                }, {
                    "$set": {
                        'is_anomaly': x['anomaly'],
                        "anomaly_score": x["anomaly_score"]
                    }
                }, upsert=False)
            else:
                mg_col.update_one({
                    '_id': ObjectId(x['_id']['$oid'])
                }, {
                    "$set": {
                        'is_anomaly': x['anomaly'],
                    }
                }, upsert=False)
        _LOGGER.info("Inserting data into MongoDB")
        self.mg.close()
