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
import sys, getopt
from pprint import pprint

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
correct = input("Is this correct (y/N)?")
if (correct != "y"):
    raise Exception("You failed!")

# Define objects for: DynamoDB
session = boto3.Session(profile_name='precedent', region_name='eu-west-2')
ddb = session.resource('dynamodb')

# Build request, action it and get response
table = ddb.Table('webChecks')
request = {
    'Item': {
        'Id': vid,
        'Host': vhost,
        'Https': vhttps,
        'IP': vip,
        'Port': vport
    }
}
response = table.put_item(**request)
pprint(response)
