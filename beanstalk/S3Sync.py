#
# This script is invoked from Jenkins jobs to assume a role from another AWS environment, delete all of the objects out of a given bucket, 
# upload objects from a file path, and invalidate a given CloudFront cache. The following env variables are required from Jenkins:
#    
#    ROLE_ARN - AWS Role ARN for the role you want to assume.
#    ROLE_SESS_NAME - You will give the assumed role a unique session name - can be anything. 
#    WORKSPACE - The Jenkins workspace name. This will be where the deployment files are found. Jenkins injects this variable by default in every job.
#    BUCKET_NAME - Name of the bucket you are deleting from/uploading to.
#    CF_DIST_ID - AWS CloudFront distribution ID. Used to invalidate the CloudFront distribution cache.
# 
# KEHOEJO - 9/2015
#

import os
from io import StringIO
import hashlib
import sys


import boto
from boto.sts import STSConnection
from boto.s3.connection import S3Connection

print ('Assuming role to access S3 on a different account')
ROLE_ARN = os.environ['ROLE_ARN']
ROLE_SESS_NAME = os.environ['ROLE_SESS_NAME']
FILE_ROOT = os.environ['WORKSPACE'] + '/project/deploy/'
BUCKET_PARAM = os.environ['BUCKET_NAME']
CF_DIST_ID = os.environ['CF_DIST_ID']

sts_connection = STSConnection()
assumedRoleObject = sts_connection.assume_role(
    role_arn=ROLE_ARN,
    role_session_name=ROLE_SESS_NAME
)

ACCESS_KEY = assumedRoleObject.credentials.access_key
SECRET_KEY = assumedRoleObject.credentials.secret_key
TOKEN = assumedRoleObject.credentials.session_token

# Use the temporary credentials returned by AssumeRole to call Amazon S3
connection = S3Connection(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    security_token=TOKEN,
    calling_format=boto.s3.connection.OrdinaryCallingFormat()
)

print('File Root: ', FILE_ROOT)
print('Bucket Name ', BUCKET_PARAM)
bucket = connection.get_bucket(BUCKET_PARAM, validate=False)

print ('Empty the bucket of all contents')
for key in bucket.list():
    key.delete()

fn = ''
for (root, dirs, files) in os.walk(FILE_ROOT):
   for name in files:
       fn = os.path.join(root, name)
       k = boto.s3.key.Key(bucket)
       keyPath = fn.replace(FILE_ROOT,"")
       keyPath = keyPath.replace("\\","/")
       print('KeyPath ', keyPath)
       k.key = keyPath
       print ('Uploading ', keyPath, ' to ',  BUCKET_PARAM)
       k.set_contents_from_filename(fn, policy='public-read')

print('Invalidate the CloudFront cache')

cf = boto.connect_cloudfront(ACCESS_KEY, SECRET_KEY, security_token=TOKEN)
files = ['/bundles/modules.js','/bundles/modules.min.js','/bundles/pioneer.min.css','/bundles/thirdparty.min.js','/bundles/thirdparty.min.css','/bundles/pioneer.js','/bundles/templates.js','/bundles/pioneer.min.js']
cf.create_invalidation_request(CF_DIST_ID, files)
