# Log Anomaly Detector

**This project is a fork of [https://github.com/AICoE/log-anomaly-detector/](https://github.com/AICoE/log-anomaly-detector/)**

Log anomaly detector is an open source project that can connect to streaming sources and produce predictions of abnormal log lines. Internally it uses unsupervised machine learning. We incorporate a number of machine learning models to achieve this result. In addition it includes a human in the loop feedback system.

Changes from the original project:
- Python v3.8 support
- MongoDB as data source and  data sink support
- Run analysis for specific host
- UI and Prometeus support was removed

---

**Table of Contents:**
- [Installation](#installation)
  * [Step 1. Install the package](#step-1-install-the-package)
  * [Step 2. Create a configuration file in yaml syntax](#step-2-create-a-configuration-file-in-yaml-syntax)
  * [Step 3. Run it as a daemon](#step-3-run-it-as-a-daemon)
- [How it works](#how-it-works)


# Installation
This installation process was tested on Ubuntu Server LTS 20.04, Python v3.8.10 and MongoDB v5.0.3.

**Each MongoDB document with a log message MUST have the "Message" and "Hostname" fields.**

## Step 1. Install the package

Copy the `install.sh` script and run it as sudo:
```bash
$ wget http://git.solidex.minsk.by:3000/nhryshalevich/log-anomaly-detector/raw/master/install.sh
$ chmod +x install.sh
$ sudo ./install.sh
```

## Step 2. Create a configuration file in yaml syntax
The config variables are defined here: [https://log-anomaly-detector.readthedocs.io/en/latest/configinfo.html](https://log-anomaly-detector.readthedocs.io/en/latest/configinfo.html)
Since it supports MongoDB and single-host running, there're some additional variables here:

<table>
  <thead>
    <tr>
      <th>Config field</th>
      <th>Details</th>
    </tr>
  </thead>
  <tbody>
  <tr>
    <td>MG_HOST</td>
    <td>MongoDB server IP address</td>
  </tr>
  <tr>
     <td>MG_PORT</td>
     <td>MongoDB server port</td>
  </tr>
  <tr>
     <td>MG_INPUT_DB</td>
     <td>MongoDB database where log entries will be pulled from</td>
  </tr>
  <tr>
     <td>MG_TARGET_DB</td>
     <td>MongoDB database where log entries will be pushed to</td>
  </tr>
  <tr>
     <td>HOSTNAMES</td>
     <td>List of log sources hostames for which the logs will be analysed</td>
  </tr>
  <tr>
     <td>MG_INPUT_COL</td>
     <td>MongoDB collection where logs from specified hosts are stored</td>
  </tr>
  <tr>
     <td>MG_TARGET_LOG</td>
     <td>MongoDB collection where anomaly logs from specified hosts will be pushed to</td>
  </tr>
  <tr>
     <td>LOG_SOURCES</td>
     <td>multiple MG_INPUT_COL +  multiple HOSTNAMES + multiple MG_TARGET_COL</td>
  </tr>
  </tbody>
</table>

Open `/opt/anomaly_detector/multihost.yaml` file and see an example of the config file:
```yaml
STORAGE_DATASOURCE: "mg"
STORAGE_DATASINK: "mg"
MG_HOST: "172.17.18.83"
MG_PORT: 27017
MG_INPUT_DB: "logstoredb"
MG_TARGET_DB: "anomalydb"
LOG_SOURCES:
  "network_logs":
    HOSTNAMES:
      - "cumulus"
      - "EXOS-VM"
      - "172.17.18.178"
    MG_TARGET_COL: "network_anomaly"
  "web_logs":
    HOSTNAMES:
      - "dataform"
    MG_TARGET_COL: "web_anomaly"
  "utm_logs":
    HOSTNAMES:
      - "172.17.18.56"
      - "172.17.31.10"
    MG_TARGET_COL: "utm_anomaly"
```
In this example MongoDB server has 172.17.18.83 IP address and 20217 port. It has two databases:
- *logstoredb*, where the original log entries are stored
- *anomalydb*, where the anomaly log files will be pushed to.

The logstoredb has three collections:
- *network_logs*, where logs from the network devices with the hostnames *cumulus*, *EXOS_VM* and *172.17.18.178* are stored
- *web_logs*, where logs from the web-server with the hostname *dataform* are stored
- *utm_logs*, where logs from the UTM devices with the hostnames *172.17.18.56* and *172.17.31.10* are stored

You can modify this file, keeping its stricture.

## Step 3. Run it as a daemon
Enable and start the service.
```bash
$ sudo systemctl enable anomaly_detector.service
$ sudo systemctl start anomaly_detector.service
```
Optionally check that it's running: `sudo systemctl status anomaly_detector`

# How it works

You can read about the ML Core here: [https://log-anomaly-detector.readthedocs.io/en/latest/model.html](https://log-anomaly-detector.readthedocs.io/en/latest/model.html)

The daemon itself creates *n* parallel processes, where *n* is the number of hosts. Each process retrieves logs in the last 30 days for specified host for the collection and train the model. Then it periodically checks the db for new log entries. If the new entry appears, the process checks if it's an anomaly. If the log message is an anomaly, it is pushed to the collection in the target database.
