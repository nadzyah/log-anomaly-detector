"""Use these code to plugin different models and storage providers."""
from anomaly_detector.adapters.base_model_adapter import BaseModelAdapter
from anomaly_detector.adapters.base_storage_adapter import BaseStorageAdapter
from anomaly_detector.adapters.feedback_strategy import FeedbackStrategy
from anomaly_detector.adapters.som_storage_adapter import SomStorageAdapter
from anomaly_detector.adapters.som_model_adapter import SomModelAdapter
from anomaly_detector.adapters.lof_storage_adapter import LOFStorageAdapter
from anomaly_detector.adapters.lof_model_adapter import LOFModelAdapter

__all__ = ['BaseModelAdapter', 'BaseStorageAdapter',
           'FeedbackStrategy',
           'SomStorageAdapter', 'SomModelAdapter',
           'LOFStorageAdapter', 'LOFModelAdapter'
           ]
