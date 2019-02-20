#
# Environment variables:
# * WEBHOOK_URL
# * SLACK_CHANNEL
#

from __future__ import print_function

import boto3
import json
import logging
import re
import os

from botocore.vendored import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Full event: " + json.dumps(event))
    message = json.loads(re.sub('^"|"$', '', event['Records'][0]['Sns']['Message']))
    
    state_dict = {"OK": ":thumbsup:", "INSUFFICIENT": ":information_source:", "ALARM": ":exclamation:"}
    color_dict = {"OK": "#00FF00", "INSUFFICIENT": "#FFFF00", "ALARM": "#FF0000"}
    
    slack_message = {
        "attachments": [
            {
                "fallback": "State: " + message['NewStateValue'] + "\nReason : " + message['NewStateReason'],
                "color": color_dict[message['NewStateValue']],
                "title": message['AlarmName'],
                "text": "State: " + message['OldStateValue'] + " ==> " + message['NewStateValue'] + "\nReason : " + message['NewStateReason'],
                "footer": message['Region'] + " / " + message['StateChangeTime']
            }
        ],
        "username": "AWS WebChecks",
        "icon_emoji": state_dict[message['NewStateValue']],
        "channel": os.environ['SLACK_CHANNEL']
    }
    
    try:
        r = requests.post(os.environ['WEBHOOK_URL'], data=json.dumps(slack_message))
        logger.info("Hooked. Message: %s", json.dumps(slack_message))
        logger.info("Hooked. Response: %r", r.text)
    except requests.exceptions.RequestException as e:
        logger.error("Requests failed: %s", e)
