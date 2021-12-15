"""LOF Storage Adapter for interfacing with custom storage for custom application."""
import logging
from anomaly_detector.adapters import BaseStorageAdapter
from anomaly_detector.decorator.utils import latency_logger
from anomaly_detector.storage import MGStorageAttribute
from anomaly_detector.storage.storage_proxy import StorageProxy

class LOFStorageAdapter(StorageProxy):
    """Custom storage interface for dealing with LOF model."""

    def __init__(self, config):
        """Initialize configuration for for storage interface."""
        self.config = config
        self.storage = StorageProxy(config)

    def retrieve_data(self, timespan, max_entry):
        """Fatch data from storage system"""
        data, raw = self.storage.retrieve(MGStorageAttribute(timespan,
                                                            max_entry))
        if len(data) == 0:
            logging.info("There are no logs in last %s seconds", timespan)
            return None, None
        data = list(data[self.config.MESSAGE_INDEX])
        return data, raw


    @latency_logger(name="LOFStorageAdapter")
    def load_data(self, config_type):
        """Load data from storage class depending on training vs inference."""
        if config_type == "train":
            return self.retrieve_data(timespan=self.config.TRAIN_TIME_SPAN,
                                      max_entry=self.config.TRAIN_MAX_ENTRIES)
        elif config_type == "infer":
            return self.retrieve_data(timespan=self.config.INFER_TIME_SPAN,
                                      max_entry=self.config.INFER_MAX_ENTRIES)
        else:
            raise Exception("Not Supported option, %s not in ['infer','train']"
                            % config_type)

    @latency_logger(name="LOFStorageadapter")
    def persist_data(self, df):
        """Abstraction around storage persistence class."""
        self.storage.store_results(df)

    def __getattr__(self, name):
        """Delegate all methods from config as a passthrough proxy into configurations."""
        return getattr(self.config, name)
