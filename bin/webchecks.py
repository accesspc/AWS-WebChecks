#
# WebChecks script to poll websites and put stats into CloudWatch
#
# @author: Robertas.Reiciunas
# @date: 20181208
#

# Imports
from __future__ import print_function
import boto3
import json
import os, sys, subprocess
from pprint import pprint

# Read configuration file
dirname = os.path.dirname(__file__)
with open(os.path.join(dirname, '../etc/config.json')) as config_json:
    config = json.load(config_json)

# Configuration check and object definitions
if (len(config['aws_region']) == 0):
    config['aws_region'] = 'eu-west-1'
if (len(config['aws_profile_name']) == 0):
    session = boto3.Session(region_name=config['aws_region'])
else:
    session = boto3.Session(region_name=config['aws_region'], profile_name=config['aws_profile_name'])
if (len(config['dynamodb_table']) == 0):
    raise Exception("DynamoDB Table name not defined")

ddb = session.client('dynamodb')
cw = session.client('cloudwatch')

def add2DynamoDB(host = None, https = None, ip = None, port = None):
    if (port is not None):
        https = bool(https)
        print("Processing arg: %s / %s : %s" % (host, ip, port))
    elif (len(sys.argv) == 2):
        # Read input from command line
        host, https, ip, port = sys.argv[1].split(',')
        https = bool(https)
    else:
        raise Exception("Wrong argument(s) provided")
    siteid = host + ":" + port + "/" + ip
    print("New SiteId: %s (using %r)" % (siteid, https))

    # Put it in the table
    response = ddb.put_item(
        Item={
            'SiteId': {
                'S': siteid
            },
            'Host': {
                'S': host
            },
            'Https': {
                'BOOL': https
            },
            'IP': {
                'S': ip
            },
            'Port': {
                'S': port
            }
        },
        ReturnConsumedCapacity='TOTAL',
        TableName=config['dynamodb_table']
    )
    print("DynamoDB ack: %r" % response['ResponseMetadata']['HTTPStatusCode'])

    addAlarm2CloudWatch(host, https, ip, port)

def addAlarm2CloudWatch(host, https, ip, port):
    alarmname = "Status %s / %s:%s" % (host, ip, port)
    ip_port = ':'.join([ip, port])
    
    response = cw.put_metric_alarm(
        AlarmName=alarmname,
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        MetricName='Status',
        Namespace=config['dynamodb_namespace'],
        Period=300,
        Statistic='Average',
        Threshold=0.8,
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
                'Value': host
            },
            {
                'Name': 'IP:Port',
                'Value': ip_port
            },
        ],
        Unit='Count'
    )

    print("CloudWatch Alarm ack: %r" % response['ResponseMetadata']['HTTPStatusCode'])

def dumpDynamoDBTable():
    response = ddb.scan(TableName=config['dynamodb_table'])

    for i in response['Items']:
        host = i['Host']['S']
        https = i['Https']['BOOL']
        ip = i['IP']['S']
        port = i['Port']['S']
        siteid = i['SiteId']['S']

        print("'%s','%s','%s','%s'" % (host, https, ip, port))

def runChecks():
    # Fetch / scan full table
    response = ddb.scan(TableName=config['dynamodb_table'])

    # Loop through items/rows
    for i in response['Items']:
        host = i['Host']['S']
        https = i['Https']['BOOL']
        ip = i['IP']['S']
        port = i['Port']['S']
        siteid = i['SiteId']['S']

        cmd = ['/usr/lib/nagios/plugins/check_http -H', host, '-I', ip, '-p', port]

        # Add extra https flags
        if (https == True):
            cmd.append('-S')
            cmd.append('--sni')
        
        # Call check_http command
        p = subprocess.Popen(' '.join(cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        line = p.stdout.readline().decode("utf-8").strip()
        retval = p.wait()

        # Switch between return values and parse output
        if (retval == 0):
            # 0: OK
            print("%d: %s; %s" % (retval, siteid, line))
            stats = line.split('|')[1]
            resp_time = stats.split('=')[1].split(';')[0].split('s')[0]
            resp_size = stats.split('=')[2].split(';')[0].split('B')[0]

        elif (retval == 1):
            # 1: WARNING
            print("%d: %s" % (retval, line))

        elif (retval == 2):
            # 2: CRITICAL
            print("%d: %s" % (retval, line))
            
        else:
            # ?: undefined
            print("%d: %s" % (retval, line))
        
        # Put metric data into CloudWatch
        ip_port = ':'.join([ip, port])
        response = cw.put_metric_data(
            MetricData=[
                {
                    'MetricName': 'ResponseTime',
                    'Dimensions': [
                        {
                            'Name': 'Hostname',
                            'Value': host
                        },
                        {
                            'Name': 'IP:Port',
                            'Value': ip_port
                        },
                    ],
                    'Unit': 'Seconds',
                    'Value': float(resp_time)
                },
                {
                    'MetricName': 'ResponseSize',
                    'Dimensions': [
                        {
                            'Name': 'Hostname',
                            'Value': host
                        },
                        {
                            'Name': 'IP:Port',
                            'Value': ip_port
                        },
                    ],
                    'Unit': 'Bytes',
                    'Value': int(resp_size)
                },
                {
                    'MetricName': 'Status',
                    'Dimensions': [
                        {
                            'Name': 'Hostname',
                            'Value': host
                        },
                        {
                            'Name': 'IP:Port',
                            'Value': ip_port
                        },
                    ],
                    'Unit': 'Count',
                    'Value': int(retval)
                }
            ],
            Namespace=config['dynamodb_namespace']
        )

