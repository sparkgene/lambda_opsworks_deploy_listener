# -*- coding: utf-8 -*-
import boto3
import json
import yaml
from time import gmtime, strftime
import datetime
from slackclient import SlackClient


class DeployListener:

    def __init__(self, slack_config):
        # OpsWorks is only avalable at us-east-1
        self.opsworks = boto3.client('opsworks', region_name='us-east-1')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('deploy_listener')

        self.slack = SlackClient(slack_config['token'])
        self.slack_username = slack_config['username']
        self.slack_channel = slack_config['channel']
        self.slack_icon_url = slack_config['icon_url']
        self.slack_icon_emoji = slack_config['icon_emoji']

    def describe_deployment(self, app_id):
        response = self.opsworks.describe_deployments(
            AppId=app_id
        )
        return response['Deployments']

    def get_item(self, key):
        result = self.table.get_item(
            Key={
                'DeploymentId': key
            }
        )
        if 'Item' not in result:
            return None
        return result['Item']

    def add_item(self, key, create_date):
        self.table.put_item(
            Item={
                'DeploymentId': key,
                'CreatedAt': create_date
            }
        )

    def delete_item(self, key):
        self.table.delete_item(
            Key={
                'DeploymentId': key
            }
        )

    def get_stack_name(self, stack_id):
        response = self.opsworks.describe_stacks(
            StackIds=[stack_id]
        )
        if len(response['Stacks']) == 0:
            return stack_id

        return response['Stacks'][0]['Name']

    def post_slack(self, deploy_info):
        stack_name = self.get_stack_name(deploy_info['StackId'])
        if deploy_info['Status'] == 'running':
            title = 'Deploy started.'
            message = 'Deploy started.\nCreatedAt: {0}'.format(
                            deploy_info['CreatedAt']
                        )
            color = 'warning'
        elif deploy_info['Status'] == 'successful':
            title = 'Deploy finished successful'
            message = 'Deploy finished successful.\nCompletedAt: {0}'.format(
                            deploy_info['CompletedAt']
                        )
            color = 'good'
        else:
            title = 'Deploy failed'
            message = 'Deploy failed!\nCompletedAt: {0}'.format(
                            deploy_info['CompletedAt']
                        )
            color = 'danger'

        attachments = [
            {
                'fallback': title,
                'pretext': stack_name,
                'text': message,
                'color': color
            }
        ]
        ret = self.slack.api_call('chat.postMessage',
                    channel=self.slack_channel,
                    attachments=json.dumps(attachments),
                    username=self.slack_username,
                    icon_url=self.slack_icon_url,
                    icon_emoji=self.slack_icon_emoji)
        print(ret)

    def check_deployment(self, app_id):
        deploy_info = self.describe_deployment(app_id)
        if len(deploy_info) == 0:
            return

        deploy_info = sorted(
                            deploy_info,
                            key=lambda k: k['CreatedAt'],
                            reverse=True
                        )
        now = datetime.datetime.now()

        for deploy in deploy_info:
            created_at = datetime.datetime.strptime(
                            deploy['CreatedAt'],
                            '%Y-%m-%dT%H:%M:%S+00:00'
                        )
            if (now - created_at).total_seconds() > 3600:
                continue
            data = self.get_item(deploy['DeploymentId'])
            if deploy['Status'] == 'running':
                if data:
                    continue
                self.add_item(deploy['DeploymentId'], deploy['CreatedAt'])
                self.post_slack(deploy)

            elif deploy['Status'] == 'successful':
                if data:
                    self.delete_item(deploy['DeploymentId'])
                    self.post_slack(deploy)

            else:
                if data:
                    self.delete_item(deploy['DeploymentId'])
                    self.post_slack(deploy)


def load_config():
    config = []
    with open('config.yml') as file:
        config = yaml.load(file)
    return config


def lambda_handler(event, context):
    print(strftime('%a, %d %b %Y %H:%M:%S +0000', gmtime()))

    config = load_config()
    listener = DeployListener(config['slack'])

    for app_id in config['app_id']:
        listener.check_deployment(app_id)

    return True
