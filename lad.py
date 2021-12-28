"""Log Anomaly Detector."""
from prometheus_client import start_http_server
from anomaly_detector.config import Configuration
from anomaly_detector.facade import Facade
import click
import os
import hashlib
from getpass import getpass
import yaml

from multiprocessing import Pool, Process

CONFIGURATION_PREFIX = "LAD"


def hash_string(string):
    """
    Return a SHA-256 hash of the given string
    """
    return hashlib.sha256(string.encode('utf-8')).hexdigest()

def one_to_many_configs(config_file):
    result = []
    with open(config_file, 'r') as f:
        yaml_data = yaml.safe_load(f)
        config_data = yaml_data.copy()
        del config_data['LOG_SOURCES']
        if 'LOG_SOURCES' in yaml_data.keys():
            for input_col_name, input_info in yaml_data['LOG_SOURCES'].items():
                for host in input_info['HOSTNAMES']:
                    config_data = config_data.copy()
                    config_data['MG_INPUT_COL'] = input_col_name
                    config_data['LOGSOURCE_HOSTNAME'] = host
                    config_data['MG_TARGET_COL'] = input_info['MG_TARGET_COL']
                    result.append(config_data)
    return result

def anomaly_run(x, single_run=False):
    x.run(single_run=single_run)

@click.group()
@click.option("--metric-port", default=8080, help="sets up metrics to publish to custom port")
def cli(metric_port: int):
    """Cli bootstrap method.

    :param metric_port: 8080 by default and will start prometheus metrics endpoint
    :return: None
    """
    start_http_server(metric_port)
    click.echo("starting up log anomaly detectory with metric_port: {}".format(metric_port))


@cli.command("ui")
@click.option("--env", default="dev", help="Run Flask in dev mode or prod.", type=click.Choice(['dev', 'prod']))
@click.option("--workers", default=2, help="No. of Flask Gunicorn workers. Only applies to --env=prod")
@click.option("--debug", default=False, help="Sets flask in debug mode to true")
@click.option("--port", default=5001, help="Select the port number you would like to run the web ui ")
@click.option("--host", default="0.0.0.0", help="Select the host. ")
def ui(debug: bool, port: int, env: str, workers: int, host: str):
    """Start web ui for user feedback system.

    :param debug: enable debug mode for flask.
    :param port: port to use for flask app.
    :return: None
    """
    click.echo("Starting UI...")
    if env == "dev":
        app = create_app()
        app.run(debug=debug, port=port, host=host)
    else:
        options = {
                'bind': '%s:%s' % (host, port),
                'limit_request_field_size': 0,
                'limit_request_line': 0,
                'timeout': 60,
                'workers': workers,
            }
        GunicornFactstore(create_app(), options).run()


@cli.command("run")
@click.option(
    "--job-type",
    default="all",
    help="select either 'train', 'inference', 'all' by default it runs train and infer in loop", )
@click.option("--config-yaml", default=".env_config.yaml", help="configuration file used to configure service")
@click.option("--single-run", default=False, help="it will loop infinitely pause at interval if set to true")
@click.option("--tracing-enabled", default=False, help="allows you to expose tracing metrics using jaegar")
def run(job_type: str, config_yaml: str, single_run: bool, tracing_enabled: bool):
    """Perform machine learning model generation with input log data.

    :param job_type: provide user the ability to run one training or inference or both.
    :param config_yaml: provides path to the config file to load into application.
    :param single_run: for running the system a single time.
    :param tracing_enabled: enabling open tracing to see the performance.
    :return: None
    """
    click.echo("Starting...")
    config_dicts = one_to_many_configs(config_yaml)
    detectors = []

    for x in config_dicts:
        config = Configuration(prefix=CONFIGURATION_PREFIX, config_dict=x)
        detectors.append(Facade(config=config, tracing_enabled=tracing_enabled))

    click.echo("Created jobtype {}".format(job_type))
    pool = Pool(len(detectors))
    click.echo("Perform training and inference in loop...")
    pool.map(anomaly_run, detectors)
    pool.close()
    pool.join()

    #if job_type == "train":
    #    click.echo("Performing training...")
    #    anomaly_detector.train()
    #elif job_type == "inference":
    #    click.echo("Perform inference...")
    #    anomaly_detector.infer()
    #elif job_type == "all":
    #    click.echo("Perform training and inference in loop...")
    #    anomaly_detector.run(single_run=single_run)


if __name__ == "__main__":
    cli(auto_envvar_prefix="LAD")
