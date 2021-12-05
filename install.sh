#!/bin/bash

echo "Installing pip3"
sudo apt-get update
sudo apt-get install -y python3-pip

echo "Installing the LAD package"
sudo pip3 install git+http://git.solidex.minsk.by:3000/nhryshalevich/log-anomaly-detector.git
echo "Installing the Log Aggregator package"
sudo pip3 install git+http://git.solidex.minsk.by:3000/nhryshalevich/log-aggregator.git

echo "Creating lad user"
#adduser --disabled-password --gecos "" lad
useradd --system lad

echo "Creating /var/run/anomaly_detector/ directory"
mkdir /var/run/anomaly_detector
chown lad:lad /var/run/anomaly_detector

echo "Creating log directory"
mkdir /var/log/anomaly_detector/
touch /var/log/anomaly_detector/error.log
chown -R lad:lad /var/log/anomaly_detector/

echo "Creating /opt/anomaly_detector/ directory"
mkdir /opt/anomaly_detector/
mkdir /opt/anomaly_detector/models/
mkdir /opt/anomaly_detector/configs/
wget "http://git.solidex.minsk.by:3000/nhryshalevich/log-anomaly-detector/raw/master/multihost_config.py" -O /opt/anomaly_detector/multihost_config.py
echo "Export default config file"
wget "http://git.solidex.minsk.by:3000/nhryshalevich/log-anomaly-detector/raw/master/config_files/multihost.yaml" -O /opt/anomaly_detector/multihost.yaml
chmod +w /opt/anomaly_detector/multihost.yaml
chown -R lad:lad /opt/anomaly_detector/

echo "Create files for running it as daemon"
wget "http://git.solidex.minsk.by:3000/nhryshalevich/log-anomaly-detector/raw/master/daemon/anomaly_detector_start" -O /usr/bin/anomaly_detector_start
chmod +x /usr/bin/anomaly_detector_start
wget "http://git.solidex.minsk.by:3000/nhryshalevich/log-anomaly-detector/raw/master/daemon/anomaly_detector_stop" -O /usr/bin/anomaly_detector_stop
chmod +x /usr/bin/anomaly_detector_stop
wget "http://git.solidex.minsk.by:3000/nhryshalevich/log-anomaly-detector/raw/master/daemon/anomaly_detector.service" -O /lib/systemd/system/anomaly_detector.service

echo "Schedule cron to restart anomaly_detector service every midnight"
echo "0  0  * * * root  service anomaly_detector restart" >> /etc/crontab

echo "Adding aggregation condfig"
wget "http://git:3000/nhryshalevich/log-aggregator/raw/master/configs/aggregator.yaml" -O /opt/anomaly_detector/aggregator.yaml
chown lad:lad /opt/anomaly_detector/aggragator.yaml
echo "Schedule cron to run aggregation script every day at 3:00 p.m."
echo "0  15 * * * lad   log-aggregator run --config-yaml /opt/anomaly_detector/aggregator.yaml" >> /etc/crontab

