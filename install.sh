#!/bin/bash

echo "Installing pip3"
sudo apt-get update
sudo apt-get install -y python3-pip

cd ~/

echo "Installing the LAD package"
sudo pip3 install file://$HOME/log-anomaly-detector/
echo "Installing the Log Aggregator package"
sudo pip3 install git+https://github.com/nadzyah/log-aggregator.git

cd ~/log-anomaly-detector

echo "Creating lad user"
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
cp ./multihost_config.py /opt/anomaly_detector/multihost_config.py
echo "Export default config file"
cp ./config_files/multihost.yaml /opt/anomaly_detector/multihost.yaml
chmod +w /opt/anomaly_detector/multihost.yaml
chown -R lad:lad /opt/anomaly_detector/

echo "Create files for running it as daemon"
cp ./daemon/anomaly_detector_start /usr/bin/anomaly_detector_start
chmod +x /usr/bin/anomaly_detector_start
cp ./daemon/anomaly_detector_stop /usr/bin/anomaly_detector_stop
chmod +x /usr/bin/anomaly_detector_stop
cp ./daemon/anomaly_detector.service /lib/systemd/system/anomaly_detector.service

echo "Schedule cron to restart anomaly_detector service every midnight"
echo "0  0  * * * root  service anomaly_detector restart" >> /etc/crontab

echo "Adding aggregation condfig"
wget "https://github.com/nadzyah/log-aggregator/raw/master/configs/aggregator.yaml" -O /opt/anomaly_detector/aggregator.yaml
chown lad:lad /opt/anomaly_detector/aggragator.yaml
echo "Schedule cron to run aggregation script every day at 3:00 p.m."
echo "0  15 * * * lad   log-aggregator run --config-yaml /opt/anomaly_detector/aggregator.yaml" >> /etc/crontab

