#!/bin/bash
set -x

apt install -y python3-pip
pip3 install boto3

install -m 0644 cron.d/webchecks /etc/cron.d/webchecks
install -m 0644 logrotate.d/webchecks /etc/logrotate.d/webchecks

