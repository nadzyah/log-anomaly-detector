"""AutoEncoder model"""
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.losses import msle
import numpy as np
import pandas as pd

class AutoEncoderModel(Model):
    """
    Parameters
    ----------
    output_units: int
      Number of output units

    code_size: int
      Number of units in bottle neck
    """

    def __init__(self, output_units, code_size=8):
        super().__init__()
        self.encoder = Sequential([
          Dense(64, activation='relu'),
          Dropout(0.1),
          Dense(32, activation='relu'),
          Dropout(0.1),
          Dense(16, activation='relu'),
          Dropout(0.1),
          Dense(code_size, activation='relu')
        ])
        self.decoder = Sequential([
          Dense(16, activation='relu'),
          Dropout(0.1),
          Dense(32, activation='relu'),
          Dropout(0.1),
          Dense(64, activation='relu'),
          Dropout(0.1),
          Dense(output_units, activation='sigmoid')
        ])

    def call(self, inputs):
        encoded = self.encoder(inputs)
        decoded = self.decoder(encoded)
        return decoded

    def train(self, scaled_data):
        self.compile(loss='msle', metrics=['mse'], optimizer='adam')
        self.fit(scaled_data, scaled_data, epochs=20, batch_size=512)

    def find_threshold(self, scaled_data):
        reconstructions = self.predict(scaled_data)
        # provides losses of individual instances
        reconstruction_errors = msle(reconstructions, scaled_data)
        # threshold for anomaly scores
        threshold = np.mean(reconstruction_errors.numpy()) \
            + np.std(reconstruction_errors.numpy())
        return threshold

    def get_predictions(self, scaled_data, threshold):
        predictions = self.predict(scaled_data)
        # provides losses of individual instances
        errors = msle(predictions, scaled_data)
        # 1 = anomaly, 0 = normal
        anomaly_mask = pd.Series(errors) > threshold
        preds = anomaly_mask.map(lambda x: 1 if x == True else 0)
        return preds, errors
