# WebCheck scripts

## How does it work
Hostname/IP/Port/HTTPS collections sit in AWs/DynamoDB table

Cron script scans the table, runs nagios/check_http command against the web

 server on specified IP/port and reports output status to AWS/CloudWatch

 metrics

AWS/CloudWatch alarms looks at metrics over past 5 minutes, averages

 response statuses and sends notification to AWS/SNS topic (Email, SMS)


## Installation
* git clone this repo
* modify etc/config.json according to your needs and environment
* run ./install.sh
* watch how the magic happens


