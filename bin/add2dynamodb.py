#
# Script to insert new hos/ip/port into DynamoDB 
#  and set up a new CloudWatch alarm
#
# @author: Robertas.Reiciunas
# @date: 20181207
#

# Imports
from __future__ import print_function
import boto3
import json
import os
import sys, getopt
from pprint import pprint

# Read configuration file
dirname = os.path.dirname(__file__)
with open(os.path.join(dirname, '../etc/config.json')) as config_json:
    config = json.load(config_json)

# Read input from command line
if (len(sys.argv) == 2):
    vhost, vhttps, vip, vport = sys.argv[1].split(',')
    vid = vhost + ":" + vport + "/" + vip
else:
    # Read input interactively
    print("Usage: python3 add2dynamodb.py www.ielts.org,true,195.224.12.21,443")
    print ("Need some details, enter them!")
    vhost = input("Hostname: ")
    vhttps = input("HTTPS (true / false): ")
    vip = input("IP address: ")
    vport = input("Port: ")

# Build Id field and verify it's ok
vhttps = bool(vhttps)
vid = vhost + ":" + vport + "/" + vip
print("New Id: %s (using %r)" % (vid, vhttps))

# Define objects for: DynamoDB
session = boto3.Session(profile_name=config['aws_profile_name'], region_name=config['aws_region'])
ddb = session.client('dynamodb')

# Put it in the table
response = ddb.put_item(
    Item={
        'Id': {
            'S': vid
        },
        'Host': {
            'S': vhost
        },
        'Https': {
            'BOOL': vhttps
        },
        'IP': {
            'S': vip
        },
        'Port': {
            'S': vport
        }
    },
    ReturnConsumedCapacity='TOTAL',
    TableName=config['dynamodb_table']
)
pprint(response)
