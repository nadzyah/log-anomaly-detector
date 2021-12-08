"""Word 2 vector model."""
import numpy as np
from gensim.models import Word2Vec
from anomaly_detector.model.base_model import BaseModel
import logging

_LOGGER = logging.getLogger(__name__)


class W2VModel(BaseModel):
    """Word2Vec model wrapper."""

    def __init__(self, config=None):
        """Construct with configurations for customizations."""
        super().__init__(config)
        self.config = config

    def update(self, words):
        """Update existing w2v model."""
        self.model.build_vocab(words, update=True)
        _LOGGER.info("Models Updated")

    def create(self, words, vector_length, window_size):
        """Create new word2vec model."""
        """
        self.model = {}
        for col in words.columns:
            if col in words:
                if not self.config:
                    self.model[col] = Word2Vec([list(words[col])], min_count=1, size=vector_length, window=window_size)
                else:
                    self.model[col] = Word2Vec([list(words[col])], min_count=self.config.W2V_MIN_COUNT,
                                               size=vector_length,
                                               window=window_size, iter=self.config.W2V_ITER,
                                               compute_loss=self.config.W2V_COMPUTE_LOSS,
                                               workers=self.config.W2V_WORKERS, seed=self.config.W2V_SEED)
            else:
                _LOGGER.warning("Skipping key %s as it does not exist in 'words'" % col)
        """
        if not self.config:
            self.model = Word2Vec(sentences=list(words), size=vector_length, window=window_size)
        else:
            self.model = Word2Vec(sentences=list(words),
                                  size=self.config.TRAIN_VECTOR_LENGTH,
                                  window=self.config.TRAIN_WINDOW)

    def get_vectors(self, logs):
        """Return logs as list of vectorized words"""
        vectors = []
        for x in logs:
            temp = []
            for word in x:
                if word in self.model.wv:
                    temp.append(self.model.wv[word])
                else:
                    temp.append(np.array([0]*self.config.TRAIN_VECTOR_LENGTH))
            vectors.append(temp)
        return vectors

    def _log_words_to_one_vector(self, log_words_vectors):
        result = []
        log_array_transposed = np.array(log_words_vectors, dtype=object).transpose()
        for coord in log_array_transposed:
            result.append(np.mean(coord))
        return result

    def _vectorized_logs_to_single_vectors(self, vectors):
        """Represent log messages as vectors according to the vectors
        of the words in these logs

        :params vectors: list of log messages, represented as list of words vectors
            [[wordvec11, wordvec12], [wordvec21, wordvec22], ...]
        """
        result = []
        for log_words_vector in vectors:
            result.append(self._log_words_to_one_vector(log_words_vector))
        return np.array(result)

    def one_vector(self, new_D: object) -> object:
        """Create a single vector from model."""
        """
        transforms = {}
        for col in self.model.keys():
            if col in new_D:
                transforms[col] = self.model[col].wv[new_D[col]]

        new_data = []

        for i in range(len(transforms["message"])):
            logc = np.array(0)
            for _, c in transforms.items():
                if c.item(i):
                    logc = np.append(logc, c[i])
                else:
                    logc = np.append(logc, [0, 0, 0, 0, 0])
            new_data.append(logc)

        return np.array(new_data, ndmin=2)
        """
        vectors = self.get_vectors(new_D)
        if len(new_D) == 1:
            return self._log_words_to_one_vector(vectors[0])
        return self._vectorized_logs_to_single_vectors(vectors)
