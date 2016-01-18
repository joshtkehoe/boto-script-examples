# boto-script-examples

I created these scripts to automate some AWS components that we use. Mostly, these scripts interact with Elastic Beanstalk and S3
and were written to be launched from Jenkins jobs, but they can be launched from anywhere.

We are running a Jenkins service on an EC2 instance with an IAM role. Because of this, we use AWS STS retrieve a temporary access key, secret access key, and session token in order to make boto3 connections to other AWS accounts. You can easily remove this code if that is not needed in your environment. If STS is not needed, you can either modify the code to pass in your own API access keys, or use your aws saved profiles on your machine. 

## Requirements
* boto3
* Python 3

## Scripts

### beanstalk
1. *BeanstalkHealthBoto.py* - Takes in an ARN, beanstalk application name, and beanstalk environment name. 
   * This script is intended to be used after a new environment has been created. It is recommended to wait 10 minutes after invoking the creation of a new environment before launching this script to allow AWS to do its thing. After making a connection to EB, this will run the describe_environments boto command using the passed in application and environment names. It will specifically look for 'Health' and 'Status' to be 'Green' and 'Ready' respectively. If either of these are not what we are looking for, we will sleep for 20 seconds and try again. If after 10 attempts the environment is not ready, it will exit with an error.
   * Example usage:  
   ```BeanstalkHealthBoto.py -a My_EB_App -e test-env-33 -r arn:aws:iam::775678901234:role/MyJenkins```
