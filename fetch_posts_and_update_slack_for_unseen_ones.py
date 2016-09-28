from __future__ import unicode_literals
import requests
from s3keyring.s3 import S3Keyring
import boto3
import json
import botocore
import sys

from HTMLParser import HTMLParser

S3_BUCKET = '<s3-bucket-goes-here>'
S3_KEYNAME = '<s3-filename-goes-here>'
ZENDESK_ACCOUNT = '<zen-desk-user-account-goes-here>'
ZENDESK_COMMUNITY_URL = '<zendesk-community-url-goes-here>'
SLACK_MESSAGE_PRETEXT = "New Zendesk Help Center Community Post from {:name:}"
SLACK_CHANNEL = "<channel-name-goes-here>"
SLACK_USERNAME = "<slack-user-name-goes-here>"

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def find_messages(*args, **kwargs):
    messagesRead = {}

    #find previously read messages
    bucket = S3_BUCKET
    keyname = S3_KEYNAME
    s3Object = boto3.resource('s3').Object(bucket, keyname)
    try:
        result = s3Object.get()['Body'].read()
        if result:
            messagesRead = json.loads(result)
    except botocore.exceptions.ClientError as e:
        print e.response['Error']
        if e.response['Error']['Code'] != "NoSuchKey":
            raise e

    keyring = S3Keyring(config_file="./s3keyring.ini",
                        profile_name="production")
    zendesk_token = keyring.get_password('product-feedback-zendesk-to-slack-bot', ZENDESK_ACCOUNT)

    response = requests.get(ZENDESK_COMMUNITY_URL,
                            auth=('{}/token'.format(ZENDESK_ACCOUNT), zendesk_token),
                            verify=False)

    slack_webhook = keyring.get_password('product-feedback-zendesk-to-slack-bot', 'slack-webhook')
    zendesk_response = response.json()
    users = {user['id']: user for user in zendesk_response["users"]}
    for post in zendesk_response['posts']:
        if str(post["id"]) in messagesRead:
            continue
        pretext = SLACK_MESSAGE_PRETEXT
        if "{:name:}" in pretext:
            pretext = pretext.replace("{:name:}", users[post['author_id']]['name'])

        json_payload = json.dumps(
            {
                "attachments": [
                    {
                        "fallback": "{} - {}".format(post['title'], post['details'][:80] + "..."),
                        "pretext": pretext,
                        "author_name": users[post['author_id']]['name'],
                        "title": strip_tags(post['title']),
                        "title_link": post['html_url'],
                        "text": strip_tags(post['details']),
                        "color": "#00343A"}],
                "channel": SLACK_CHANNEL,
                "username": SLACK_USERNAME,
                "icon_emoji": ":bulb:"
            }
        )
        slack_response = requests.post(slack_webhook, data={"payload": json_payload})
        messagesRead[post['id']] = True
    data = json.dumps(messagesRead)
    boto3.resource('s3').Bucket(bucket).put_object(Key=keyname, Body=data)


if __name__ == '__main__':
    find_messages()
