# -*- coding: utf-8 -*-

# Copyright Joseph Holland
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from graffiti_monkey import cli as gm_cli
import os
import boto3
import logging

# Remove existing log handler setup by Lambda
log = logging.getLogger()
for log_handler in log.handlers:
    log.removeHandler(log_handler)

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)


def envvar_to_list(envvar):
    return os.environ[envvar].split(',')


def send_notification(sns_arn, region, subject, message):
    client = boto3.client('sns')

    response = client.publish(
        TopicArn=sns_arn,
        Subject=subject,
        Message=message
    )

    log.info('SNS Response: {}'.format(response))


def handler(event, context):
    log.info('Loading function')
    try:
        sns_arn = os.environ.get('SNS_ARN', '')
        region_list = envvar_to_list('REGION')
        for region in region_list:
            gm = gm_cli.GraffitiMonkeyCli()
            gm.region = region
            gm.config = {"_instance_tags_to_propagate": envvar_to_list('INSTANCE_TAGS_TO_PROPAGATE'),
                        "_volume_tags_to_propagate": envvar_to_list('VOLUME_TAGS_TO_PROPAGATE'),
                        "_volume_tags_to_be_set": envvar_to_list('VOLUME_TAGS_TO_BE_SET'),
                        "_snapshot_tags_to_be_set": envvar_to_list('SNAPSHOT_TAGS_TO_BE_SET'),
                        "_instance_filter": envvar_to_list('INSTANCE_FILTER'),
                        }
            gm.initialize_monkey()
            gm.start_tags_propagation()
            if sns_arn:
                send_notification(sns_arn, region, 'Graffiti Monkey completed successfully',
                                'Graffiti Monkey completed successfully in ' + region + '.')
        return 'Graffiti Monkey completed successfully!'
    except KeyError as e:
        error_message = 'Error: Environment variable not set: ' + str(e)
        log.error(error_message)
        if sns_arn:
            send_notification(sns_arn, region, 'Error running Graffiti Monkey',
                            'Error running Lambda Graffiti Monkey in ' + region + '. Error Message: ' + error_message)
        raise e
    except Exception as e:
        error_message = 'Error: Graffiti Monkey encountered the following error: ' + str(e)
        log.error(error_message)
        if sns_arn:
            send_notification(sns_arn, region, 'Error running Graffiti Monkey',
                            'Error running Lambda Graffiti Monkey in ' + region + '. Error Message: ' + error_message)
        raise e
