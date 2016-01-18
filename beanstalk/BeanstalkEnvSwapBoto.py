# BeanstalkEnvSwapBoto.py
#
# This script is invoked from Jenkins jobs. Its duty is to swap environment CNAMES from the current live CNAME to the CNAME of
# the passed in Beanstalk environment. This uses STS to assume a different role.
#
#    -r or --role_name          : AWS Role ARN for the role you want to assume.
#    -a or --app_name           : Name of the Beanstalk application to query
#    -c or --cname_search       : The live CNAME to find
#    -d or --swap_dest          : The environment that we want to make the current live CNAME
#
# joshtkehoe@gmail.com - 1/2016
#

import sys
import os
import boto3
import getopt

def findLiveCName(cName, cNameSearch):
    if cName.lower().find(cNameSearch) > -1:
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

def swapEnvironments(eb_client, liveCName, swapCName):
    if liveCName.lower().strip() != swapCName.lower().strip():
        print('Changing LIVE env from from',liveCName,'to',swapCName)
        resp = eb_client.swap_environment_cnames(
            SourceEnvironmentName=liveCName,
            DestinationEnvironmentName=swapCName
        )
        code=resp['ResponseMetadata']['HTTPStatusCode']
        if code != 200:
            sys.exit('Something went wrong swapping the CNAME. ' + resp)
    else:
        print('CName already set to', swapCName, '- Doing nothing.')

def descEnvironments(eb_client, swapDest, cNameSearch, appName):
    LIVE = ''
    response = eb_client.describe_environments(
      ApplicationName=appName
    )

    cName=''
    environments=response['Environments']
    print(environments)
    for x in environments:
      printEnvData(x)
      cName=x['CNAME']
      if findLiveCName(cName, cNameSearch):
        LIVE = x['EnvironmentName']

    print('LIVE:',LIVE)
    print('DEST:',swapDest)
    if LIVE=='':
        sys.exit('Critical Error: No LIVE CName found for: '+ cNameSearch)
    swapEnvironments(eb_client, LIVE,swapDest)


def main(argv):
    if len(sys.argv)==1:
        sys.exit('Swap env argument required')

    print ('Number of arguments:', len(sys.argv), 'arguments.')
    print ('Argument List:', str(sys.argv))

    swapDest=''
    roleArn=''
    cNameSearch=''
    appName=''
    try:
        opts, args = getopt.getopt(argv,"d:r:c:a:",["swap_dest=","role_arn=","cname_search=","app_name="])
    except getopt.GetoptError:
        print('BeanstalkEnvSwapBoto.py -d <swap destination> -r <role ARN> -c <cname for env> -a <application name>' +
            '--swap_dest <swap destination> --role_arn <role ARN> --cname_search <cname for env> --app_name <application name>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-d", "--swap_dest"):
            swapDest=arg
        if opt in ("-r", "--role_arn"):
            roleArn=arg
        if opt in ("-c", "--cname_search"):
            cNameSearch=arg
        if opt in ("-a", "--app_name"):
            appName=arg

    if swapDest=='' or roleArn=='' or cNameSearch=='' or appName=='':
      sys.exit('BeanstalkEnvSwapBoto.py -d <swap destination> -r <role ARN> -c <cname for env> -a <application name>' +
            '--swap_dest <swap destination> --role_arn <role ARN> --cname_search <cname for env> --app_name <application name>')

    print('SwapDest:',swapDest)
    print('RoleArn:',roleArn)
    print('cNameSearch:',cNameSearch)
    print('appName:',appName)

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
    descEnvironments(eb_client, swapDest, cNameSearch,appName)
    print('Finished successfully.')

if __name__ == "__main__":
  main(sys.argv[1:])


