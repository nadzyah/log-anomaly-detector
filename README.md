# Log Anomaly Detector

**This project is a fork of [https://github.com/AICoE/log-anomaly-detector/](https://github.com/AICoE/log-anomaly-detector/)**

Log anomaly detector is an open-source project that can connect to streaming sources and produce predictions of abnormal log lines. Internally it uses unsupervised machine learning. We incorporate several machine learning models to achieve this result. In addition, it includes a human in the loop feedback system.

Changes from the original project:
- Python v3.8 support
- MongoDB as a data source and  data sink support
- Run analysis for a specific host
- UI and Prometheus support was removed

---

**Table of Contents:**
- [Installation](#installation)
  * [Step 1. Install the package](#step-1-install-the-package)
  * [Step 2. Create a configuration file in yaml syntax](#step-2-create-a-configuration-file-in-yaml-syntax)
  * [Step 3. Run it as a daemon](#step-3-run-it-as-a-daemon)
- [How it works](#how-it-works)


# Installation
This installation process was tested on Ubuntu Server LTS 20.04, Python v3.8.10 and MongoDB v5.0.3.

**Each MongoDB document with a log message MUST have the "message" fields (case sensitive).**

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
     <td>MG_USER</td>
     <td>MongoDB username</td>
  </tr>
  <tr>
     <td>MG_PASSWORD</td>
     <td>MongoDB password</td>
  </tr>
  <tr>
     <td>MG_USE_SSL</td>
     <td>Boolean variable that defines if SSL should be used for connection</td>
  </tr>
  <tr>
     <td>MG_CERT_DIR</td>
     <td>Server certificate location</td>
  </tr>
  <tr>
     <td>MG_VERIFY_CERT</td>
     <td>Boolean variable that defines if server's certificate should be verified</td>
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
     <td>MG_TARGET_COL</td>
     <td>MongoDB collection where anomaly logs from specified hosts will be pushed to</td>
  </tr>
  <tr>
     <td>LOG_SOURCES</td>
     <td>multiple MG_INPUT_COL +  multiple HOSTNAMES + multiple MG_TARGET_COL</td>
  </tr>
  <tr>
     <td>HOSTNAME_INDEX</td>
     <td>The name of the index where hostname is specified</td>
  </tr>
  <tr>
     <td>DATETIME_INDEX</td>
     <td>The name of the index where event time is specified</td>
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
In this example MongoDB server has 172.17.18.83 IP address and 27017 port. It has two databases:
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
$ sudo systemctl status anomaly_detector
```
For process monitoring, check `/var/log/anomaly_detector/error.log` file.

# How it works

Read about the ML Core here: [https://log-anomaly-detector.readthedocs.io/en/latest/model.html](https://log-anomaly-detector.readthedocs.io/en/latest/model.html)

The daemon itself creates *n* parallel processes, where *n* is the number of hosts. Each process retrieves logs in the last 30 days for a specified host from the collection and trains the model. Then it periodically checks the DB for new log entries. If the new entry appears, the process checks if it's an anomaly. If the log message is an anomaly, it is pushed to the collection in the target database.
