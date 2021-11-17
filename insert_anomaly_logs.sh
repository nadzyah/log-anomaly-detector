#!/bin/bash

echo "<179>Nov  9 11:14:46 dataform  [Tue Nov 09 11:14:46.645337 2021] [core:error] [pid 1541542:tid 139663671027456] [client 45.146.164.110:56888] AH00126: Invalid URI in request POST /cgi-bin/.%2e/.%2e/.%2e/.%2e/bin/sh HTTP/1.1" | nc -v -q 1 172.17.18.82 514

echo "Nov 16 11:10:58 cumulus sudo: cumulus : TTY=pts/0 ; PWD=/home/cumulus ; USER=root ; COMMAND=/usr/bin/apt-key adv --keyserver by.ubuntu.com --recv-keys 4094092040214" | nc -v -q 1 172.17.18.82 514
