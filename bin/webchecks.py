#
# WebChecks script to poll websites and put stats into CloudWatch
#
# @author: Robertas.Reiciunas
# @date: 20181206
#

# Imports
from __future__ import print_function
import boto3
import json
from pprint import pprint
import subprocess

# Define objects for: DynamoDB and CloudWatch
session = boto3.Session(profile_name='precedent', region_name='eu-west-2')
ddb = session.resource('dynamodb')
cw = session.client('cloudwatch')

# Fetch / scan full table
table = ddb.Table('webChecks')
response = table.scan()

# Loop through items/rows
for i in response['Items']:
    cmd = ['/usr/lib/nagios/plugins/check_http -H', i['Host'], '-I', i['IP'], '-p', i['Port']]

    # Add extra https flags
    if (i['Https'] == True):
        cmd.append('-S')
        cmd.append('--sni')
    
    # Call check_http command
    p = subprocess.Popen(' '.join(cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    line = p.stdout.readline().decode("utf-8").strip()
    retval = p.wait()

    # Switch between return values and parse output
    if (retval == 0):
        # 0: OK
        print("%d: %s; %s" % (retval, i['Id'], line))
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
    ip_port = ':'.join([i['IP'], i['Port']])
    cw.put_metric_data(
        MetricData=[
            {
                'MetricName': 'ResponseTime',
                'Dimensions': [
                    {
                        'Name': 'Hostname',
                        'Value': i['Host']
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
                        'Value': i['Host']
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
                        'Value': i['Host']
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
        Namespace='WebChecks'
    )

