
# Log Anomaly Detector

**This project is a fork of [https://github.com/AICoE/log-anomaly-detector/](https://github.com/AICoE/log-anomaly-detector/)**

Log anomaly detector is an open-source project that can connect to streaming sources and produce predictions of abnormal log lines. Internally it uses unsupervised machine learning. We incorporate several machine learning models to achieve this result. In addition, it includes a human in the loop feedback system.

Changes from the original project:
- Python v3.8 support
- MongoDB as a data source and  data sink support
- Run analysis for a specific host
- UI and Prometheus support was removed
- The usage Word2Vec algorithm was improved

---

**Table of Contents:**

- [Installation](#installation)
  * [Step 1. Install the package](#step-1-install-the-package)
  * [Step 2. Create a configuration file in yaml syntax](#step-2-create-a-configuration-file-in-yaml-syntax)
  * [Step 3. Configure log aggregation](#step-3-configure-log-aggregation)
  * [Step 4. Run it as a daemon](#step-4-run-it-as-a-daemon)
- [How it works](#how-it-works)
  * [Log anomaly detector](#log-anomaly-detector)
    + [Word2Vec](#word2vec)
    + [The daemon](#the-daemon)
  * [Anomaly log aggregator](#anomaly-log-aggregator)
- [Troubleshooting](#troubleshooting)
  * [Failed to start after reboot](#failed-to-start-after-reboot)

# Installation
This installation process was tested on Ubuntu Server LTS 20.04, Python v3.8.10 and MongoDB v5.0.3.

**Each MongoDB document with a log message MUST have the "message" field (case sensitive).**

## Step 1. Install the package

Clone the repo and run `install.sh` script as sudo:

```bash
$ cd ~/
$ git clone <repo url>
$ chmod +x ./log-anomaly-detector/install.sh
$ sudo ./log-anomaly-detector/install.sh
```

Then you can delete the repo: `rm -rf ~/log-anomaly-detector`

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
     <td>MongoDB username (optional)</td>
  </tr>
  <tr>
     <td>MG_PASSWORD</td>
     <td>MongoDB password (optional)</td>
  </tr>
  <tr>
     <td>MG_CA_CERT</td>
     <td>CA certificate location for TLS encryption (optional)</td>
  </tr>
  <tr>
     <td>MG_VERIFY_CERT</td>
     <td>Boolean variable that defines if server's certificate should be verified (optional)</td>
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
  network_logs:
    HOSTNAMES:
      - "cumulus"
      - "EXOS-VM"
      - "172.17.18.178"
    MG_TARGET_COL: "network_anomaly"
  web_logs:
    HOSTNAMES:
      - "dataform"
    MG_TARGET_COL: "web_anomaly"
  utm_logs:
    HOSTNAMES:
      - "172.17.18.56"
      - "172.17.31.10"
    MG_TARGET_COL: "utm_anomaly"
```
In this example, MongoDB server has 172.17.18.83 IP address and 27017 port. It has two databases:
- *logstoredb*, where the original log entries are stored
- *anomalydb*, where the anomaly log files will be pushed to.

The logstoredb has three collections:
- *network_logs*, where logs from the network devices with the hostnames *cumulus*, *EXOS_VM* and *172.17.18.178* are stored
- *web_logs*, where logs from the web-server with the hostname *dataform* are stored
- *utm_logs*, where logs from the UTM devices with the hostnames *172.17.18.56* and *172.17.31.10* are stored

You can modify this file, keeping its stricture.

## Step 3. Configure log aggregation

We also provide a script to aggregate anomaly logs. Check it [here](http://172.17.17.198:3000/nhryshalevich/log-aggregator) To configure it open `/opt/anomaly_detector/aggregator.yaml` file. See the example below:

```yaml
DATETIME_INDEX: timestamp
HOSTNAME_INDEX: hostname
MG_HOST: 172.17.18.83
MG_PORT: 27017
MG_INPUT_DB: anomalydb
MG_INPUT_COLS: 
  - web_anomaly
  - utm_anomaly
  - network_anomaly
MG_TARGET_COLS: 
  - web_aggregated
  - utm_aggregated
  - network_aggregated
MG_TARGET_DB: anomalydb
STORAGE_DATASINK: mg
STORAGE_DATASOURCE: mg
AGGR_TIME_SPAN: 86400
AGGR_EPS: 0.01
AGGR_MIN_SAMPLES: 2
AGGR_VECTOR_LENGTH: 25
AGGR_WINDOW: 5
```

You must be already familiar with some of the options. See the description to the additional ones:

<table>
  <thead>
    <tr>
      <th>Config field</th>
      <th>Details</th>
    </tr>
  </thead>
  <tbody>
  <tr>
    <td>MG_INPUT_COLS</td>
    <td>MongoDB collections, where the anomaly logs are located</td>
  </tr>
  <tr>
    <td>MG_TARGET_COLS</td>
    <td>MongoDB collections, where the aggregated logs should be pushed to</td>
  </tr>
  <tr>
    <td>AGGR_TIME_SPAN</td>
    <td>Number of seconds specifying how far to the past to go to load log entries for aggregation</td>
  </tr>
  <tr>
    <td>AGGR_EPS</td>
    <td>The same as "eps" parameter in DBSCAN algorithm. <b>MODIFY ONLY IF YOU KNOW WHAT YOU'RE DOING</b></td>
  </tr>
  <tr>
    <td>AGGR_MIN_SAMPLES</td>
    <td>The same as "min_samples" parameter in DBSCAN algorithm. <b>MODIFY ONLY IF YOU KNOW WHAT YOU'RE DOING</b></td>
  </tr>
  <tr>
    <td>AGGR_VECTOR_LENGTH</td>
    <td>The same as "size" parameter in Word2Vec algorithm. <b>MODIFY ONLY IF YOU KNOW WHAT YOU'RE DOING</b></td>
  </tr>
  <tr>
    <td>AGGR_WINDOW</td>
    <td>The same as "window" parameter in Word2Vec algorithm. <b>MODIFY ONLY IF YOU KNOW WHAT YOU'RE DOING</b></td>
  </tr>
  </tbody>
</table>

For example, in the config file all the anomaly logs from `web_anomaly` collection will be pushed to `web_aggregated` collection, thus it's important to follow the input-target order.

The aggregation script is run every day at 3:00 p.m. You can change the time in the `/etc/crontab` file.

If you want to aggregate logs right now, execute the next command: `log-aggregator run --config-yaml /opt/anomaly_detector/aggregator.yaml`

## Step 4. Run it as a daemon
Enable and start the service.
```bash
$ sudo systemctl enable anomaly_detector.service
$ sudo systemctl start anomaly_detector.service
$ sudo systemctl status anomaly_detector
```

# How it works

## Log anomaly detector

Read about the ML Core here: [https://log-anomaly-detector.readthedocs.io/en/latest/model.html](https://log-anomaly-detector.readthedocs.io/en/latest/model.html)

### Word2Vec

Here we improved Word2Vec. In the original approach, each log message was considered as a word, but since w2v uses context to vectorize words, this approach gives us very strict similarities between logs, which are initialized with random numbers.

In our approach, we vectorize each word in each log message. The vector of a log message is the mean vector of all the vectors that represent the log message (the mean for each coordinate is calculated separately).

### The daemon

The daemon itself creates *n* parallel processes, where *n* is the number of hosts. Each process retrieves logs in the last 30 days for a specified host from the collection and trains the model. Then it periodically checks the DB for new log entries. If the new entry appears, the process checks if it's an anomaly. If the log message is an anomaly, it is pushed to the collection in the target database.

Also the LAD process is restarted to train the model using new logs every day at midnight.

## Anomaly log aggregator

Each message is represeted as a vector with the usage of Word2Vec library. Then we apply DBSCAN to find similar logs.

Aggregated logs are pushed to the MongoDB in the next format:
```json
{
  "message": "Aggeregated *** log message",
  "total_logs": 3,
  "timestamp": {
    "$date": "1970-01-01T00:00:00.000tZ"
  },
  "original_messages": [
    "Aggregated 1 log message",
    "Aggregated 2 log message",
    "Aggregated 3 log message"
  ]
}
```
Parameters explanation:
- all different words and parameters are substituted with `***`. 
- original_messages -- the list of the original anomaly logs. 
- timestamp is calculated as the mean of all timestamps of the original logs.
- total_logs -- the number of all the original logs

The real example:
```json
{
  "_id": {
    "$oid": "61a9dae97a2eb3c99ac49d16"
  },
  "message": "<86>Dec 1 *** cumulus *** pam_unix(cron:session): session opened for user root by (uid=0)",
  "total_logs": 11,
  "timestamp": {
    "$date": "2021-12-01T16:05:26.953Z"
  },
  "original_messages": [
    "<86>Dec  1 17:15:01 cumulus CRON[25368]: pam_unix(cron:session): session opened for user root by (uid=0)",
    "<86>Dec  1 17:00:01 cumulus CRON[25252]: pam_unix(cron:session): session opened for user root by (uid=0)",
    "<86>Dec  1 16:45:01 cumulus CRON[25136]: pam_unix(cron:session): session opened for user root by (uid=0)",
    "<86>Dec  1 16:30:01 cumulus CRON[25019]: pam_unix(cron:session): session opened for user root by (uid=0)",
    "<86>Dec  1 16:17:01 cumulus CRON[24915]: pam_unix(cron:session): session opened for user root by (uid=0)",
    "<86>Dec  1 16:15:01 cumulus CRON[24880]: pam_unix(cron:session): session opened for user root by (uid=0)",
    "<86>Dec  1 16:00:01 cumulus CRON[24765]: pam_unix(cron:session): session opened for user root by (uid=0)",
    "<86>Dec  1 15:45:01 cumulus CRON[24649]: pam_unix(cron:session): session opened for user root by (uid=0)",
    "<86>Dec  1 15:30:01 cumulus CRON[24533]: pam_unix(cron:session): session opened for user root by (uid=0)",
    "<86>Dec  1 11:30:01 cumulus CRON[22581]: pam_unix(cron:session): session opened for user root by (uid=0)",
    "<86>Dec  1 11:17:01 cumulus CRON[22478]: pam_unix(cron:session): session opened for user root by (uid=0)",
  ]
}
```

# Troubleshooting

For process monitoring, check `/var/log/anomaly_detector/error.log` file.
	
## Failed to start after reboot

It usually happens because `/var/run/anomaly_detector/` directory is removed after reboot.

To fix it:
1. Create the `/var/run/anomaly_detector/` directory:

	```bash
	$ sudo mkdir /var/run/anomaly_detector/
	```

2. Transfer the ownership to the lad user:

	```bash
	$ sudo chown lad:lad /var/run/anomaly_detector/
	```

