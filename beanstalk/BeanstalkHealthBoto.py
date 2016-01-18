# BeanstalkHealthBoto.py
#
# This script is invoked from Jenkins jobs. Its duty is to verify that the passed in environment name has a health of 'green' and a status of 'ready'.
# If it is not yet green and ready, it will sleep and try again. After a set number of attempts, if the environment is still not ready,
# it will exit with an error. This uses STS to assume a different role.
#
#    -r or --role_name          : AWS Role ARN for the role you want to assume.
#    -a or --application_name   : Name of the Beanstalk application to query
#    -e or --environment_name   : Name of the Beanstalk environment to query
#
# joshtkehoe@gmail.com - 1/2016
#

import sys
import os
import boto3
import getopt
import time

def goodHealth(str):
    if str.lower().find('green') > -1:
      return True
    return False

def goodStatus(str):
    if str.lower().find('ready') > -1:
      return True
    return False

def printEnvData(x):
    if 'EnvironmentName' in x:
        print('environment name:',x['EnvironmentName'])
    else:
        sys.exit('No environment name')

    if 'CNAME' in x:
        print('CNAME:',x['CNAME'])
    else:
        sys.exit('No CName')

    if 'Health' in x:
        print('health:',x['Health'])
    else:
        sys.exit('No health')

    if 'Status' in x:
        print('status:',x['Status'])
    else:
        sys.exit('No status')


def descEnvironments(eb_client, appName, envName):
    response = eb_client.describe_environments(
      ApplicationName=appName,
      EnvironmentNames=[envName]
    )

    cName=''
    health=''
    status=''

    environments=response['Environments']
    if not environments:
        sys.exit('Environment not found: '+ envName +' in app: ' + appName)

    for x in environments:
      printEnvData(x)
      cName=x['CNAME']
      health=x['Health']
      status=x['Status']

      if goodHealth(health):
        if goodStatus(status):
          return True
    return False


def main(argv):
    print ('Number of arguments:', len(sys.argv), 'arguments.')
    print ('Argument List:', str(sys.argv))

    appName=''
    envName=''
    roleArn=''
    try:
      opts, args = getopt.getopt(argv,"a:e:r:",
        ["application_name=","environment_name=","role_arn="])
      print('opts',opts)
      print('args',args)
    except getopt.GetoptError:
      print('BeanstalkHealthBoto.py -a <application_name> -e <environment_name> -r <role_arn>')
      sys.exit(2)
    for opt, arg in opts:
      if opt in ("-e", "--environment_name"):
        envName=arg
      elif opt in ("-a", "--application_name"):
        appName=arg
      elif opt in ("-r", "--role_arn"):
        roleArn=arg

    if envName=='' or appName=='' or roleArn=='':
      sys.exit('BeanstalkHealthBoto.py -a <application_name> -e <environment_name> -r <role_arn>')

    print('environment_name:',envName)
    print('application_name:',appName)
    print('role_arn:',roleArn)

    sts_client = boto3.client('sts')
    response = sts_client.assume_role(
      RoleArn=roleArn,
      RoleSessionName='temp_sess'
    )

    ACC_KEY = response['Credentials']['AccessKeyId']
    SEC_KEY=response['Credentials']['SecretAccessKey']
    SESS_TOKEN=response['Credentials']['SessionToken']

    print('ACC_KEY: ', ACC_KEY)
    print('SEC_KEY: ', SEC_KEY)
    print('SESS_TOKEN: ', SESS_TOKEN)

    eb_client = boto3.client(
       'elasticbeanstalk',
       aws_access_key_id=ACC_KEY,
       aws_secret_access_key=SEC_KEY,
       aws_session_token=SESS_TOKEN
    )

    ready=False
    for x in range(1,10):
      print('Run',x,'of 10')
      greenAndReady=descEnvironments(eb_client, appName, envName)
      if greenAndReady:
        print('Env',envName,'is ready to go')
        ready=True
        break
      else:
        print('Env',envName,'is NOT ready to go')
      print('Sleep and try again')
      time.sleep(20)

    if not ready:
      sys.exit("Environment not starting up in alotted time or environment is not healthy.")

if __name__ == "__main__":
  main(sys.argv[1:])


