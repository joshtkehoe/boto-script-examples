#
# This script is invoked from Jenkins jobs to assume a role from another AWS environment, upload an elastic beanstalk application 
# to a S3 bucket, create a new application version using the uploaded artifact, and create a new elastic beanstalk environment
# using the newly created application version. 
#    
#    ROLE_ARN - AWS Role ARN for the role you want to assume.
#    ROLE_SESS_NAME - You will give the assumed role a unique session name - can be anything. 
#    FILE_NAME - What we will name the uploaded artifact in S3. We will also append the build number and .zip to the name.
#    BUCKET_NAME - Name of the bucket we will upload the application to.
#    SOURCE - Local path for the artifact we are uploading
#    EB_APP_NAME - The name that we will give the new application version. Must be unique. We will append the build number to it.
#    EB_TEMPLATE - The name of the template that will be used for the create environment process.
#    EB_ENV_NAME - The name for the new environment. Must be unique. We will append the build number to it.
#    BUILD_NUMBER - Jenkins environment variable.
# 
# KEHOEJO - 10/2015
#

import os
from io import StringIO
import hashlib
import sys

import boto
from boto.sts import STSConnection
from boto.s3.connection import S3Connection
from boto import beanstalk 
from boto.beanstalk.layer1 import Layer1

print ('Assuming role of MaverickJenkins to access AWS on a different account')
ROLE_ARN = os.environ['ROLE_ARN']
ROLE_SESS_NAME = os.environ['ROLE_SESS_NAME']
BUCKET_PARAM = os.environ['BUCKET_NAME']
FILE_NAME = os.environ['FILE_NAME']
SOURCE = os.environ['SOURCE']
APP_NAME = os.environ['EB_APP_NAME']
BUILD_NUMBER = os.environ['BUILD_NUMBER']
TEMPLATE_NAME = os.environ['EB_TEMPLATE']
ENVIRONMENT_NAME = os.environ['EB_ENV_NAME']

sts_connection = STSConnection()
assumedRoleObject = sts_connection.assume_role(
    role_arn=ROLE_ARN,
    role_session_name=ROLE_SESS_NAME
)

ACCESS_KEY = assumedRoleObject.credentials.access_key
SECRET_KEY = assumedRoleObject.credentials.secret_key
TOKEN = assumedRoleObject.credentials.session_token

# Connect to S3. Upload .zip to S3 bucket.
connection = S3Connection(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    security_token=TOKEN,
    calling_format=boto.s3.connection.OrdinaryCallingFormat()
)

bucket = connection.get_bucket(BUCKET_PARAM, validate=False)
	
k = boto.s3.key.Key(bucket)
k.key=FILE_NAME + '-' + BUILD_NUMBER + '.zip'
print('source ', SOURCE)
print('bucket ', BUCKET_PARAM)
print('file name ', FILE_NAME)
print('template name ', TEMPLATE_NAME)
print('build number ', BUILD_NUMBER)
k.set_contents_from_filename(SOURCE)

# Connect to Layer1
l = Layer1(aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,security_token=TOKEN)

# Create a new application version using the file we just uploaded to S3
verName = APP_NAME + '-boto-' + BUILD_NUMBER
l.create_application_version(APP_NAME,verName,description='eb app ver created via boto',s3_bucket=BUCKET_PARAM,s3_key=k.key,auto_create_application=False)
l.create_environment(APP_NAME,ENVIRONMENT_NAME,template_name=TEMPLATE_NAME,version_label=verName)

print('done')

