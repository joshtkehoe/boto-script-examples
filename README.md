# boto-script-examples

I created these scripts to automate some AWS components that we use. Mostly, these scripts interact with Elastic Beanstalk and S3
and were written to be launched from Jenkins jobs, but they can be launched from anywhere.

We are running a Jenkins service on an EC2 instance with an IAM role. Because of this, we use AWS STS retrieve a temporary access key, secret access key, and session token in order to make boto3 connections to other AWS accounts. You can easily remove this code if that is not needed in your environment. If STS is not needed, you can either modify the code to pass in your own API access keys, or use your aws saved profiles on your machine. 

Requirements:
boto3
Python 3
