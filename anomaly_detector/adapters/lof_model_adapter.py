"""LOF Model apapter - Working with custom implementation of LOF"""
import logging
from sklearn.preprocessing import MinMaxScaler
from anomaly_detector.decorator.utils import latency_logger
from anomaly_detector.adapters.base_model_adapter import BaseModelAdapter
from anomaly_detector.model import W2VModel, LOFModel, AutoEncoderModel

class LOFModelAdapter(BaseModelAdapter):
    """Local outlier factor custom logic to train model. Includes logic to train and predict anomalies in logs."""

    def __init__(self, storage_adapter):
        self.storage_adapter = storage_adapter
        self.model = LOFModel(config=storage_adapter.config)
        self.w2v_model = W2VModel(config=storage_adapter.config)

    def load_w2v_model(self):
        """Load in w2v model."""
        try:
            self.w2v_model.load(self.storage_adapter.W2V_MODEL_PATH)
        except ModelLoadException as ex:
            logging.error("Failed to load W2V model: %s" % ex)
            raise

    def load_lof_model(self):
        try:
            self.model.load(self.storage_adapter.LOF_MODEL_PATH)
        except ModelLoadException as ex:
            logging.error("Failed to load LOF model: %s" % ex)
            raise

    @latency_logger("LOFModelAdapter")
    def preprocess(self, config_type, recreate_model):
        """Load data and train."""
        dataframe, raw_data = self.storage_adapter.load_data(config_type)
        if dataframe is not None:
            if not recreate_model:
                self.w2v_model.update(dataframe)
            else:
                self.w2v_model.create(dataframe,
                                      self.storage_adapter.TRAIN_VECTOR_LENGTH,
                                      self.storage_adapter.TRAIN_WINDOW)
            try:
                self.w2v_model.save(self.storage_adapter.W2V_MODEL_PATH)
            except ModelSaveException as ex:
                logging.error("Failed to save W2V model: %s" % ex)
                raise

        return dataframe, raw_data

    @latency_logger("LOFModelAdapter")
    def train(self, data, json_logs):
        """Train LOF model after creating vectors from words using w2v model."""
        vectors = self.w2v_model.one_vector(data)
        # The model is always recreated
        self.model.train(vectors, self.storage_adapter.LOF_NEIGHBORS,
                         self.storage_adapter.LOF_METRIC,
                         self.storage_adapter.PARALLELISM)

        # AutoEncoder for model Ensebmling
        min_max_scaler = MinMaxScaler(feature_range=(0, 1))
        self.scaled_data = min_max_scaler.fit_transform(vectors.copy())
        self.ae_model = AutoEncoderModel(output_units=self.scaled_data.shape[1])
        self.ae_model.train(self.scaled_data)

        score_pairs = self.predict(vectors, json_logs)
        try:
            self.model.save(self.storage_adapter.LOF_MODEL_PATH)
        except ModelSaveException as ex:
            logging.error("Failed to save LOF model: %s" % ex)
            raise
        return score_pairs

    @latency_logger(name="LOFModelAdapter")
    def predict(self, data, json_logs):
        """Predict from provided data and flag it an anomaly or not."""
        scores = self.process_scores(data)

        ae_threshold = self.ae_model.find_threshold(self.scaled_data)
        ae_pred, ae_errors = self.ae_model.get_predictions(self.scaled_data, ae_threshold)
        ae_errors = list(map(float, ae_errors))

        f = []
        hist_count = 0
        logging.info("Max score: %f" % max([x[1] for x in scores]))

        for i in range(len(data)):
            s = json_logs[i]
            #if scores[i][0] == -1:
            if ae_errors[i] > ae_threshold and scores[i][1] > 1:
                s["anomaly"] = 1
                s["anomaly_score"] = 0.5*(scores[i][1] + ae_errors[i])
                logging.warning("Anomaly found (score: %f): %s" % (s["anomaly_score"],
                                                                   s["message"]))
                hist_count += 1
            else:
                s["anomaly"] = 0
            f.append(s)
        logging.info("Anomaly percentage: %f percents", 100*hist_count/len(data))
        return f

    def process_scores(self, vectors):
        """Generate scores from some. To be used for inference."""
        if isinstance(vectors[0][0], str):
            vectors = self.w2v_model.one_vector(vectors)
        scores = self.model.predict(vectors)
        return scores
