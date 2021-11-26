"""MongoDB storage interface"""
import datetime
import pandas
from pymongo import MongoClient
import ssl
import os
import logging
from bson.json_util import dumps
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
        if len(self.config.MG_CERT_DIR) and os.path.isdir(self.config.MG_CERT_DIR):
            _LOGGER.warning(
                "Using cert and key in %s for connection to %s (verify_certs=%s)."
                % (
                    self.config.MG_CERT_DIR,
                    self.MG_URI,
                    self.config.MG_VERIFY_CERTS,
                )
            )
            self.mg = MongoClient(
                self.MG_URI,
                ssl=True,
                ssl_certfile=MG_CERT_DIR,
                ssl_cert_reqs=ssl.CERT_REQUIRED,
                ssl_ca_certs=self.config.MG_CACERT_DIR,
            )
        else:
            _LOGGER.warning("Conecting to MongoDB without SSL/TLS encryption.")
            self.mg = MongoClient(
                self.MG_URI
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

         mg_input_db = self.mg[self.config.MG_INPUT_DB]
         now = datetime.datetime.now()

         mg_data = mg_input_db[self.config.MG_INPUT_COL]

         query = {
             self.config.DATETIME_INDEX:  {
                 '$gte': now - datetime.timedelta(seconds=storage_attribute.time_range),
                 #'$gte': now - datetime.timedelta(days=30),
                 '$lt': now
             },
             self.config.HOSTNAME_INDEX: self.config.LOGSOURCE_HOSTNAME
         }

         mg_data = mg_data.find(query).sort(self.config.DATETIME_INDEX, -1).limit(storage_attribute.number_of_entries)
         _LOGGER.info(
            "Reading %d log entries in last %d seconds from %s",
             mg_data.count(True),
             storage_attribute.time_range,
             self.MG_URI,
         )

         self.mg.close()

         if not mg_data.count:   # if it equials 0:
             return pandas.Dataframe(), mg_data

         mg_data = dumps(mg_data, sort_keys=False)

         mg_data_normalized = pandas.DataFrame(pandas.json_normalize(json.loads(mg_data)))
         _LOGGER.info("%d logs loaded in from last %d seconds", len(mg_data_normalized),
                      storage_attribute.time_range)

         self._preprocess(mg_data_normalized)

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
        mg_target_db = self.mg[self.config.MG_TARGET_DB]
        mg_target_col = mg_target_db[self.config.MG_TARGET_COL]
        normalized_data = []
        for x in data:
            if x['anomaly']:
                del x['_id']
                del x['e_message']
                del x['predict_id']
                del x['predictor_namespace']
                del x['inference_batch_id']
                del x['elast_alert']
                if isinstance(x[self.config.DATETIME_INDEX], dict):
                    x[self.config.DATETIME_INDEX] = datetime.datetime.fromtimestamp(x[self.config.DATETIME_INDEX]["$date"] / 1e3)
                normalized_data.append(x)

        if normalized_data:
            _LOGGER.info("Inderting data to MongoDB.")
            mg_target_col.insert_many(normalized_data)
        else:
            _LOGGER.info("No anomalies were detected.")
