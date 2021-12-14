#!/usr/bin/env python3

import yaml
import os
from pprint import pprint

def one_to_many_configs(config_file, store_dir):
    with open(config_file, 'r') as f:
        yaml_data = yaml.safe_load(f)
        config_data = yaml_data.copy()
        del config_data['LOG_SOURCES']
        if 'LOG_SOURCES' in yaml_data.keys():
            for input_col_name, input_info in yaml_data['LOG_SOURCES'].items():
                for host in input_info['HOSTNAMES']:
                    config_data['MG_INPUT_COL'] = input_col_name
                    config_data['LOGSOURCE_HOSTNAME'] = host
                    config_data['MG_TARGET_COL'] = input_info['MG_TARGET_COL']
                    new_file = store_dir + host + ".yaml"
                    with open(new_file, 'w+') as outfile:
                        yaml.dump(config_data, outfile)

if __name__ == '__main__':
    one_to_many_configs("/opt/anomaly_detector/multihost.yaml", "/opt/anomaly_detector/configs/")
