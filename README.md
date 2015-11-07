# lambda_deploy_listener
AWS Lambda function for checking OpsWorks deploy status.

## Overview

This is a Scheduled Lambda function for checking OpsWorks deploy status and post to slack.
The function use DynamoDB to store deploy id.(setting up DynamoDB is required. DynamoDB and Lambda function must located on same region)

![slack post image](https://raw.githubusercontent.com/sparkgene/lambda_opsworks_deploy_listener/master/slack_post_image.png)

## Installation

```
git clone https://github.com/sparkgene/lambda_opsworks_deploy_listener
pip install -r requirements.txt -t /path/to/lambda_opsworks_deploy_listener
```

## Configuration

```
cp lambda_opsworks_deploy_listener/config.yml.org lambda_opsworks_deploy_listener/config.yml
```

Edit `config.yml` with editor and fill up the settings.

```
app_id:
 - your_app_id
 - your_app_id 2(If you want to check several apps)

slack:
  token: your_token
  username: lambda_bot
  channel: your_slack_channel
  icon_url: None
  icon_emoji: ":slack:"
```

### slack config

Create a api token. https://api.slack.com/web
Other keys are based on https://api.slack.com/methods/chat.postMessage
If post do not appear to your channel, set `channel id` to `channel`.

## Usage

1. Edit config.yml
2. Create Amazon DynamoDB table.

  ``` shell
  # create table
  aws dynamodb create-table --table-name deploy_listener --attribute-definitions AttributeName=DeploymentId,AttributeType=S --key-schema AttributeName=DeploymentId,KeyType=HASH --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
  ```
3. Pack function

  ``` shell
  zip -r func.zip . -x .git/**/*
  ```
  details
  http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html
4. Upload to your lambda function
  See details createing scheduled lambda function.
  http://docs.aws.amazon.com/lambda/latest/dg/getting-started-scheduled-events.html

## Caution

Rate frequencies of less than five minutes are not supported on AWS Lambda.

http://docs.aws.amazon.com/lambda/latest/dg/getting-started-scheduled-events.html

If the deploy start and finish between the execution of Lambda function, nothing will post to Slack.

Using this scripts on AWS is not free.

[Amazon DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/)

[AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
