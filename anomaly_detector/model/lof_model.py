"""Local Outlier Factor model"""
from anomaly_detector.model.base_model import BaseModel
import numpy as np
import logging
from sklearn.neighbors import LocalOutlierFactor

_LOGGER = logging.getLogger(__name__)

class LOFModel(BaseModel):
    """LOF Model implementation based on the original one"""

    def __init__(self, config=None):
        """Construct with configurations for customization"""
        super().__init__(config)
        self.config = config

    def train(self, X, neighbors, metric, parallelism):
        """Train the LOF model"""
        lof = LocalOutlierFactor(n_neighbors=neighbors,
                                 metric=metric,
                                 novelty=True,
                                 n_jobs=parallelism
                                 )
        lof.fit(X)
        self.model = lof

    def predict(self, logs):
        """Make inference according new logs"""
        if isinstance(logs[0], float):
            logs = [logs]
        preds = self.model.predict(logs)
        scores = abs(self.model.score_samples(logs))
        return list(zip(preds, scores))
