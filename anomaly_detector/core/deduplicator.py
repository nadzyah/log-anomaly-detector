import pandas as pd
import numpy as np
from anomaly_detector.core.encoder import LogEncoderCatalog
from sklearn.cluster import DBSCAN
from anomaly_detector.storage.storage import DataCleaner

class LogDeduplicator(DataCleaner):
    """Allows to aggreate similar logs in one"""

    def __init__(self, config):
        """Initialize the Deduplicator that allows to aggregate similar log messages in one event

        :param config: configuration of the application
        """
        self.config = config


    def encode_logs(self, log_data):
        """Encode message from log data to vectors

        :param log_data: list of dicts with logs
        """
        self.df_logs = pd.DataFrame(pd.json_normalize(log_data))
        self._preprocess(self.df_logs)

        self.encoder = LogEncoderCatalog('w2v_encoder', self.config)
        self.encoder.build()

        # Encode every message
        self.encoder.encode_log(self.df_logs)

        self.vectors = self.encoder.one_vector(self.df_logs)


    def add_clusters(self):
        """Clusterize logs and add cluster label to each dataframe
        """
        self.model = DBSCAN(eps=self.config.DEDUP_EPS,
                            min_samples=self.config.DEDUP_MIN_SAMPLES)
        clusters = self.model.fit_predict(self.vectors)
        self.df_logs['clusters'] = clusters

    def predict_new_log(self, X_new):
        # Result is noise by default
        y_new = np.ones(shape=len(X_new), dtype=int)*-1

        encoded_new = self.encoder.one_vector(pd.DataFrame(pd.json_normalize(X_new)))
        # Iterate all input samples for a label
        for j, x_new in enumerate(X_new):
            # Find a core sample closer than EPS
            for i, x_core in enumerate(self.model.components_):
                if metric(x_new, x_core) < self.model.eps:
                    # Assign label of x_core to x_new
                    y_new[j] = self.model.labels_[self.model.core_sample_indices_[i]]
                    break
