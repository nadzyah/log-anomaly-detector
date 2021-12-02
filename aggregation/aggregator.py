import sys
sys.path.append('/home/nadzya/Apps/log-anomaly-detector/')

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
import json
import datetime
from pymongo import MongoClient
import yaml

from anomaly_detector.storage.mongodb_storage import MongoDBStorage, MongoDBDataStorageSource
from anomaly_detector.config import Configuration
from anomaly_detector.storage.storage_attribute import MGStorageAttribute
from anomaly_detector.core.encoder import LogEncoderCatalog
from anomaly_detector.storage.storage import DataCleaner

def get_configs(path_to_yaml_file):
    """Initialize configuration object from the yaml file"""
    configs = []
    with open(path_to_yaml_file, 'r') as f:
        yaml_data = yaml.safe_load(f)
        config_data = yaml_data.copy()
        del config_data["MG_INPUT_COLS"]
        del config_data["MG_TARGET_COLS"]
        for i in range(len(yaml_data["MG_INPUT_COLS"])):
            config_data["MG_INPUT_COL"] = yaml_data["MG_INPUT_COLS"][i]
            config_data["MG_TARGET_COL"] = yaml_data["MG_TARGET_COLS"][i]
            configs.append(Configuration(config_dict=config_data))
    return configs

def get_anomaly_logs(config):
    """Get logs from MongoDB database"""
    mg_attr = MGStorageAttribute(config.AGGR_TIME_SPAN, config.AGGR_MAX_ENTRIES)
    mg = MongoDBDataStorageSource(config)
    return mg.retrieve(mg_attr)

def log2vec(config, log_df):
    """Encode log messages to vectors with Word2Vec model usage"""
    encoder = LogEncoderCatalog('w2v_encoder', config)
    encoder.build()
    encoder.encode_log(log_df)
    return encoder.one_vector(log_df)

def set_cluster_labels(config, vectors, orig_df):
    """Clusterize logs and add cluster label to the dataframe.
    Return clusters array
    """
    dbscan = DBSCAN(eps=config.AGGR_EPS, min_samples=config.AGGR_MIN_SAMPLES)
    clusters = dbscan.fit_predict(vectors)
    orig_df['cluster'] = clusters
    return clusters

def get_mean_time(time_list):
    """Return mean time in ISO format
    """
    mean = np.mean(time_list)
    return datetime.datetime.fromtimestamp(mean / 1e3)

def aggregate_logs(df, df_json, clusters):
    """Return list of aggregated messages with aggregated parameters
    Result example:

    <190>date=2021-12-01 * ** *** logid="0100026003" type="event" subtype="system" level="information" vd="root" **** tz="+0300" logdesc="DHCP statistics" ***** ****** ******* msg="DHCP statistics"
    ... and the list of original messages

    """
    aggregated = []
    for cluster in np.unique(clusters):
        messages = []
        for i in list(df.loc[df['cluster'] == cluster].index):
            messages.append(df_json[i]["message"])

        if cluster == -1:
            for msg in messages:
                aggregated.append((msg, 1, []))
        else:
            splited_messages = [x.split() for x in messages]
            splited_transpose = [list(row) for row in zip(*splited_messages)]
            result_string = ""
            var_num = 0

            for x in splited_transpose:
                if len(set(x)) == 1:
                    result_string += x[0] + " "
                else:
                    result_string += "***" + " "

            msg_num = len(messages)
            aggregated.append((result_string[:-1], msg_num, messages))

    return aggregated

def aggregated_logs_to_json(config, aggregated_logs, orig_df):
    """Format each message to MongoDB dict with mean timestamp"""
    dates = np.array(orig_df[config.DATETIME_INDEX + ".$date"]).astype(np.int64)

    mean_time = get_mean_time(dates)

    result = []
    for msg, total_num, messages in aggregated_logs:
        data = {}
        data["message"] = msg
        data["total_logs"] = total_num
        data["timestamp"] = mean_time
        if messages:
            data["original_messages"] = messages
        result.append(data)

    return result

def write_logs_to_mg(config, logs):
    if (config.MG_USER and config.MG_PASSWORD):
        MG_URI = "mongodb://%s:%s@%s:%s"% (
            config.MG_USER,
            config.MG_PASSWORD,
            config.MG_HOST,
            config.MG_PORT
        )
    else:
        MG_URI = "mongodb://%s:%s"% (
            config.MG_HOST,
            config.MG_PORT
        )
    mg = MongoClient(MG_URI)
    db = mg[config.MG_TARGET_DB]
    col = db[config.MG_TARGET_COL]
    col.insert_many(logs)

def main():
    configs = get_configs("/home/nadzya/Apps/log-anomaly-detector/config_files/aggr_conf.yaml")
    for config in configs:
        logs_df, df_json = get_anomaly_logs(config)
        if df_json:
            vectors = log2vec(config, logs_df)
            clusters = set_cluster_labels(config, vectors, logs_df)
            aggr_logs = aggregate_logs(logs_df, df_json, clusters)
            aggr_json = aggregated_logs_to_json(config, aggr_logs, logs_df)
            write_logs_to_mg(config, aggr_json)

if __name__ == '__main__':
    main()
