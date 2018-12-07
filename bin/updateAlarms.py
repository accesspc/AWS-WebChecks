#
# Update CloudWatch Alarms from DynamoDB Table
#
# @author: Robertas.Reiciunas
# @date: 20181207
#

# Imports
from __future__ import print_function
import boto3
import json
import os
from pprint import pprint

# Read configuration file
dirname = os.path.dirname(__file__)
with open(os.path.join(dirname, '../etc/config.json')) as config_json:
    config = json.load(config_json)

# Define objects for: DynamoDB and CloudWatch
session = boto3.Session(profile_name=config['aws_profile_name'], region_name=config['aws_region'])
ddb = session.resource('dynamodb')
cw = session.client('cloudwatch')

# Fetch / scan full table
table = ddb.Table(config['dynamodb_table'])
response = table.scan()

# Loop through items/rows
for i in response['Items']:
    print("%s,%s,%s,%s" % (i['Host'], i['Https'], i['IP'], i['Port']))

    alarmname = "Status %s / %s:%s" % (i['Host'], i['IP'], i['Port'])
    ip_port = ':'.join([i['IP'], i['Port']])
    
    response = cw.put_metric_alarm(
        AlarmName=alarmname,
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        MetricName='Status',
        Namespace=config['dynamodb_namespace'],
        Period=300,
        Statistic='Average',
        Threshold=0.2,
        ActionsEnabled=True,
        OKActions=[
            config['sns_topic_ok_arn']
        ],
        AlarmActions=[
            config['sns_topic_alarm_arn']
        ],
        AlarmDescription='',
        Dimensions=[
            {
                'Name': 'Hostname',
                'Value': i['Host']
            },
            {
                'Name': 'IP:Port',
                'Value': ip_port
            },
        ],
        Unit='Count'
    )

    pprint(response['ResponseMetadata']['HTTPStatusCode'])

