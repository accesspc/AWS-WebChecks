# WebChecks scripts

## How does it work
Hostname/IP/Port/HTTPS collections sit in AWS/DynamoDB table

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

## config.json
* "aws_region": AWS region name (eu-west-1)
* "aws_profile_name": Leave blank to use EC2 role or default `aws configure` profile
* "dynamodb_table": DynamoDB Table name
* "dynamodb_namespace": DynamoDB Namespace
* "sns_topic_alarm_arn": SNS topic for ALARM notifications
* "sns_topic_ok_arn": SNS topic for OK notifications (usually the same, can be other or empty[TBD])

## TBD
* lambda snsToSlack deployment script
* If config fields are empty
* Make it totally serverless - not quite possible due to nagios-plugins/check_http package/file

