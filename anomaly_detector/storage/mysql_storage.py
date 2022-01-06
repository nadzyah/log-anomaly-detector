"""MySQL storage interface"""
import datetime
import pandas
import mysql.connector
import logging
import json
from anomaly_detector.storage.storage import DataCleaner
from anomaly_detector.storage.storage_source import StorageSource
from anomaly_detector.storage.stdout_sink import StorageSink
from anomaly_detector.storage.storage_attribute import MySQLStorageAttribute

_LOGGER = logging.getLogger(__name__)

class MySQLStorage:
    """MySQL storage backend."""

    NAME = "mysql"
    _MESSAGE_FIELD_NAME = "_source.message"

    def __init__(self, config, is_input=True):
        """Initialize MySQL storage backend."""
        self.config = config
        self._connect(is_input)

    def _connect(self, is_input):
        if is_input:
            _LOGGER.warning(
                "Connection to MySQL at %s" % (self.config.MYSQL_INPUT_HOST)
            )
            self.db = mysql.connector.connect(
                host=self.config.MYSQL_INPUT_HOST,
                port=self.config.MYSQL_INPUT_PORT,
                user=self.config.MYSQL_INPUT_USER,
                password=self.config.MYSQL_INPUT_PASSWORD,
                database=self.config.MYSQL_INPUT_DB
            )
            return
        _LOGGER.warning(
                "Connection to MySQL at %s" % (self.config.MYSQL_TARGET_HOST)
            )
        self.db = mysql.connector.connect(
            host=self.config.MYSQL_TARGET_HOST,
            port=self.config.MYSQL_TARGET_PORT,
            user=self.config.MYSQL_TARGET_USER,
            password=self.config.MYSQL_TARGET_PASSWORD,
            database=self.config.MYSQL_TARGET_DB
        )

class MySQLDataStorageSource(StorageSource, DataCleaner, MySQLStorage):
    """MySQL data source implementation."""

    NAME = "mysql.source"

    def __init__(self, config):
        """Initialize MySQL storage backend."""
        self.config = config
        MySQLStorage.__init__(self, config)

    def retrieve(self, storage_attribute: MySQLStorageAttribute):
        """Retrieve data from MySQL"""
        now = datetime.datetime.now()

        cursor = self.db.cursor()

        if self.config.LOGSOURCE_HOSTNAME:
            sql = "SELECT %s, %s, %s FROM %s WHERE (%s BETWEEN '%s' AND '%s' AND %s = '%s') ORDER BY %s DESC LIMIT %d" % (
                self.config.MESSAGE_INDEX,
                self.config.DATETIME_INDEX,
                self.config.HOSTNAME_INDEX,
                self.config.MYSQL_INPUT_TABLE,
                self.config.DATETIME_INDEX,
                (now - datetime.timedelta(seconds=storage_attribute.time_range)).strftime("%Y-%m-%d %H:%M:%S"),
                now.strftime("%Y-%m-%d %H:%M:%S"),
                self.config.HOSTNAME_INDEX,
                self.config.LOGSOURCE_HOSTNAME,
                self.config.DATETIME_INDEX,
                storage_attribute.number_of_entries
            )
        else:
            sql = "SELECT %s, %s FROM %s WHERE (%s BETWEEN %s AND %s) ORDER BY %s DESC LIMIT %d" % (
                self.config.MESSAGE_INDEX,
                self.config.DATETIME_INDEX,
                self.config.MYSQL_INPUT_TABLE,
                self.config.DATETIME_INDEX,
                (now - datetime.timedelta(seconds=storage_attribute.time_range)).strftime("%Y-%m-%d %H:%M:%S"),
                now.strftime("%Y-%m-%d %H:%M:%S"),
                self.config.DATETIME_INDEX,
                storage_attribute.number_of_entries
            )

        cursor.execute(sql)
        data = cursor.fetchall()
        json_data = []
        for x in data:
            tmp = {}
            tmp[self.config.MESSAGE_INDEX] = x[0]
            tmp[self.config.DATETIME_INDEX] = x[1]
            tmp[self.config.HOSTNAME_INDEX] = x[2]
            json_data.append(tmp)

        _LOGGER.info(
            "Reading %d log entries in last %d seconds from %s",
            len(json_data),
            storage_attribute.time_range,
            self.config.MYSQL_INPUT_HOST,
        )

        if not len(json_data):
            return pandas.DataFrame(), json_data

        json_data_normalized = pandas.DataFrame(pandas.json_normalize(json_data))

        _LOGGER.info("%d logs loaded in from last %d seconds", len(json_data_normalized),
                     storage_attribute.time_range)

        self._preprocess(json_data_normalized)

        cursor.close()

        return json_data_normalized, json_data

class MySQLDataSink(StorageSink, DataCleaner, MySQLStorage):
    """MySQL data sink implementation."""

    NAME = "mysql.sink"

    def __init__(self, config):
        """Initialize MySQL storage backend."""
        self.config = config
        MySQLStorage.__init__(self, config, False)

    def store_results(self, data):
        """Store results back to MySQL"""
        cursor = self.db.cursor()
        sql = ("INSERT INTO "
               + self.config.MYSQL_TARGET_TABLE
               + " (" + self.config.MESSAGE_INDEX + ", "
               + self.config.DATETIME_INDEX + ", "
               + self.config.HOSTNAME_INDEX
               + ", anomaly_score) VALUES (%s, %s, %s, %s)"
               )
        normalized_data = []
        for x in data:
            if x["anomaly"]:
                normalized_data.append((x[self.config.MESSAGE_INDEX],
                                        x[self.config.DATETIME_INDEX],
                                        x[self.config.HOSTNAME_INDEX],
                                        x["anomaly_score"])
                                       )
        if normalized_data:
            cursor.executemany(sql, normalized_data)
            _LOGGER.info("Inserting data into MySQL.")
            self.db.commit()
        else:
            _LOGGER.info("No anomalies were detected.")
        cursor.close()
