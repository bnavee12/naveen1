import json
import boto3
import logging
import os
import botocore
import collections
import uuid
import datetime
from datetime import datetime, timezone
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

logger = logging.getLogger(os.environ["AWS_LAMBDA_FUNCTION_NAME"])
logger.setLevel(logging.INFO)

client_config = os.environ["CLIENT_CONFIG"]
client_job    = os.environ["CLIENT_JOB"]

"""
Function to get the client config information from the Dynamo DB
Output : client config
"""
def getclientconfig(client_id,dynamodb):
    logger.info('Fetching Client config details')
    config_table = dynamodb.Table(client_config)
    client_config_data = config_table.get_item(Key={'clientid': client_id})
    return client_config_data

"""
Function to get the list of S3 files from Source Location
Output : S3 files list
"""
def get_s3filelist(bucket,s3path,clients):
    s3files_list = []
    logger.info('Fetching S3 files present in the client source location for '+clients['clientid']+'')
    client = boto3.client('s3')
    list_response = client.list_objects_v2(Bucket = bucket,Prefix = s3path+"/")
    sort_bysize = lambda obj: int(obj['Size'])
    sorted_files= [obj for obj in sorted(list_response['Contents'], key=sort_bysize)]
    for name in sorted_files:
        s3path = "s3://"+bucket+"/"+name['Key']
        path, s3filename = os.path.split(name['Key'])
        s3files_dict = collections.OrderedDict()
        s3files_attr_dict = collections.OrderedDict()
        if s3filename:
            s3files_dict['clientid'] = clients['clientid']
            s3files_dict['Etag'] = name['ETag'].strip('"')
            s3files_attr_dict['Filepath'] = s3path
            s3files_attr_dict['Uploadedon'] = str(name['LastModified'])
            s3files_attr_dict['FileName'] = s3filename
            s3files_attr_dict['Filesize'] = name['Size']
            s3files_dict['file_attributes'] = s3files_attr_dict
            s3files_list.append(s3files_dict)
    s3files_json = eval(json.dumps(s3files_list))
    return s3files_json

"""
Function to send Email.
Output : None
"""
def send_email(client_conf,client_s3files,started_at):
    if client_conf['destination']['location'] != 's3':
        client = boto3.client('ssm')
        response = client.get_parameter(Name=os.environ["SMTP_CREDS"],WithDecryption=True)
        smtp_creds = json.loads(response['Parameter']['Value'])
        logger.info('Sending Initial email to recipients')
        sender = 'oaextractionteam_dl@optum.com'
        receiver = list(client_conf['contact_email'].split(","))
        msg = MIMEMultipart()
        msg['Subject'] = '**EXTERNAL** '+client_conf['clientid']+' - OPADM File Transfer - File transfer process started'
        msg_body = """
            <html>
            <p>Greetings for the day!<br><br>This e-mail is to notify that the OPADM automated file transfer has started for the latest set of files. Further status updates will be sent when the transfer gets completed.<br><br>Thanks,<br>Optum Extraction Team<br><br>
            <table border="1" cellpadding="5">
            <tr>
                <th><span style="color: #003366">Total File count</th>
                <th><span style="color: #003366">Total File Size(Size in GB)</th>
            </tr>
            """
        file_count = len(client_s3files)
        file_size = 0
        for s3file in client_s3files:
            file_size += s3file['file_attributes']['Filesize']
        total_size = round(int(file_size)/(1024*1024*1024),5)
        msg_body += """
                <tr>
                    <td align="left">"""+str(file_count)+"""</td>
                    <td align="right">"""+str(total_size)+"""</td>
                </tr>
                """
        msg_body += "</table></html>"
        msg_body += """
            <h4><span style="color: #003366;">List of files to be transferred</span><br></h4>
            <p><span style="color: #003366">
            <table border="1" cellpadding="5">
            <tr>
                <th><span style="color: #003366">Client</th>
                <th><span style="color: #003366">Startedtime</th>
                <th><span style="color: #003366">FilePath</th>
                <th><span style="color: #003366">FileName</th>
                <th><span style="color: #003366">FileSize(Size in GB)</th>
            </tr>
            """
        for s3file in client_s3files:
            file_size = round(s3file['file_attributes']['Filesize']/(1024*1024*1024),5)
            started = datetime.strptime(started_at,"%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d %H:%M:%S")
            msg_body += """
                <tr>
                    <td align="left">"""+str(client_conf['clientid'])+"""</td>
                    <td align="right">"""+str(started)+"""</td>
                    <td align="right">"""+str(os.path.dirname(s3file['file_attributes']['Filepath']))+"""</td>
                    <td align="right">"""+str(s3file['file_attributes']['FileName'])+"""</td>
                    <td align="right">"""+str(file_size)+"""</td>
                </tr>
                """
        msg_body += "</table></html>"
        msg.preamble = 'Multipart message.\n'
        part = MIMEText(str(msg_body), 'html')
        msg.attach(part)
        smtpObj = smtplib.SMTP("omail.o360.cloud", 587)
        smtpObj.starttls()
        smtpObj.login(smtp_creds['username'],smtp_creds['password'])
        smtpObj.sendmail(sender, receiver, msg.as_string())
        smtpObj.quit()
        logger.info('Successfully sent email')

"""
Function to add Job into DynamoDB and trigger the Stepfunction for file transfer.
Output : None
"""
def trigger_transfer(client_conf,client_s3files,dynamodb,bucket,s3path,path_count):
    ecsclient = boto3.client('ecs')
    logger.info('Adding Job Information into the Database')
    job_dict = collections.OrderedDict()
    job_dict['clientid'] = client_conf['clientid']
    job_dict['jobid']  = str(uuid.uuid4())
    job_dict['started_at'] = datetime.utcnow().isoformat()
    job_dict['jobstatus'] = 'Processing'
    job_table = dynamodb.Table(client_job)
    job_response = job_table.put_item(Item=job_dict)
    logger.info('Job Information added')
    if client_conf['destination']['location'] == 'sftp':
        if client_conf['destination']['path']:
            dest_path = "sftp:"+client_conf['destination']['path']
        else:
            dest_path="sftp:"
        if path_count == 1:
            destination = dest_path
        else:
            destination = dest_path+os.path.basename(s3path)+"/"
        logger.info('Trigger SFTP Process')
        state_name = str(uuid.uuid4())
        sf_input = {
            "Overrides": {
            "ContainerOverrides": [
                {
                "Name": os.environ["CONTAINER_NAME"],
                "Command": [
                    "sftptransfer.sh","--sftp-set-modtime=false","copy",
                    "s3://"+bucket+"/"+s3path+"/", destination,"--log-level", "INFO", "--retries", "1"
                ],
                "Environment": [
                    {
                    "Name": "SFTP_CREDS",
                    "Value": client_conf['destination']['sftpcredentials']
                    },
                ]
                }
            ]
            },
            "jobid": job_dict['jobid'],
            "clientid": client_conf['clientid'],
            "ecs_name": os.environ["CONTAINER_NAME"]
        }
        sfclient = boto3.client('stepfunctions')
        sfresponse = sfclient.start_execution(
        stateMachineArn=os.environ['SFTP_STEPFUNCTION_ARN'],
        name=state_name,
        input=json.dumps(sf_input),
        )
    elif client_conf['destination']['location'] == 's3':
        logger.info('Trigger S3 Transfer Process')
        response = ecsclient.run_task(
            cluster=os.environ["CLUSTER"],
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [os.environ["SUBNETS"]],
                    'securityGroups': [os.environ["SECURITY_GROUP"]]
                }
            },
            overrides={
                'containerOverrides': [
                    {
                        'name': os.environ["CONTAINER_NAME"],
                        'command': [
                        "s3transfer.sh",
                        "s3://"+bucket+"/"+s3path+"/", client_conf['destination']['path']+os.path.basename(s3path)+"/",
                        client_conf['clientid'],client_job,job_dict['jobid']
                        ]
                    },
                ]
            },
            taskDefinition=os.environ["TASK_DEFINITION"]
            )
    elif client_conf['destination']['location'] == 'google':
        state_name = str(uuid.uuid4())
        sf_input = {
            "Overrides": {
            "ContainerOverrides": [
                {
                "Name": os.environ["CONTAINER_NAME"],
                "Command": [
                    "googletransfer.sh",
                    "cp", "-c", "-L", "manifest.txt","-r",
                    "s3://"+bucket+"/"+s3path+"",
                    client_conf['destination']['path']+os.path.basename(s3path)
                ],
                "Environment": [
                    {
                    "Name": "JobId",
                    "Value": job_dict['jobid']
                    },
                ]
                }
            ]
            },
            "jobid": job_dict['jobid'],
            "clientid": client_conf['clientid']
        }
        sfclient = boto3.client('stepfunctions')
        sfresponse = sfclient.start_execution(
        stateMachineArn=os.environ['STEPFUNCTION_ARN'],
        name=state_name,
        input=json.dumps(sf_input),
        )
    return job_dict['started_at']

"""
Function to check if the Job is already running for the client in DynamoDB.
Output : Job details if running
"""
def check_job_running(client_conf):
    logger.info('Checking to see if job is running for the client '+client_conf['clientid'])
    dbclient = boto3.client('dynamodb')
    client_job_details = dbclient.query(TableName=client_job,KeyConditions={'clientid': {'AttributeValueList': [{'S': client_conf['clientid']}],'ComparisonOperator': 'EQ'}},QueryFilter={'jobstatus': {'AttributeValueList': [{'S': 'Processing'}],'ComparisonOperator': 'EQ'}})
    return client_job_details['Items']

"""
Function to send Failure email in case of error.
Output : None
"""
def send_failure_email(client_config,msg_data):
    if client_conf['destination']['location'] != 's3':
        client = boto3.client('ssm')
        response = client.get_parameter(Name=os.environ["SMTP_CREDS"],WithDecryption=True)
        smtp_creds = json.loads(response['Parameter']['Value'])
        logger.info('Sending Failure email to recipients')
        sender = 'oaextractionteam_dl@optum.com'
        receiver = list(client_config['contact_email'].split(","))
        msg = MIMEMultipart()
        msg['Subject'] = '**EXTERNAL** '+client_config['clientid']+'- OPADM File Transfer - Status of the transfer: Failure'
        msg_body = """Greetings for the day!
        
        This e-mail is to notify that the OPADM file transfer process has  failed. Please refer the attachment for additional details like the name of the files expected as part of the transfer, size of each file in the source before the transfer process began, size of each file after transferred to the destination folder and status of the transfer of each file.
        
        Action needs to be taken by: Optum
        Steps: Optum team will take care of the next steps for this failure and will keep the email chain posted with possible updates within 24 hours from when this is triggered. Client need not to take any action.
        
        Thanks,
        Optum Extraction Team"""
        msg.preamble = 'Multipart message.\n'
        part = MIMEText(str(msg_body), 'html')
        msg.attach(part)
        smtpObj = smtplib.SMTP("omail.o360.cloud", 587)
        smtpObj.starttls()
        smtpObj.login(smtp_creds['username'],smtp_creds['password'])
        smtpObj.sendmail(sender, receiver, msg.as_string())
        smtpObj.quit()
        logger.info('Successfully sent email')

def lambda_handler(event, context):
    try:
        message = event["Records"][0]["Sns"]["Message"]
        data = json.loads(message)
        client_id = data['clientId']
        s3bucket = data['clientBucket']
        s3path = data['s3FilePrefix']
        dynamodb = boto3.resource('dynamodb')
        client_config = getclientconfig(client_id,dynamodb)
        if 'Item' in client_config:
            job_status = check_job_running(client_config['Item'])
            if job_status==[]:
                all_client_files=[]
                for path in s3path:
                    client_s3files = get_s3filelist(s3bucket,path,client_config['Item'])
                    all_client_files+=client_s3files
                    if client_s3files!=[]:
                        started_time = trigger_transfer(client_config['Item'],client_s3files,dynamodb,s3bucket,path,len(s3path))
                    else:
                        logger.error('No files found in source location for '+client_config['Item']['clientid'])
                        msg = 'No files found in source location  for '+client_config['Item']['clientid']
                        send_failure_email(client_config['Item'],msg)
                send_email(client_config['Item'],all_client_files,started_time)
            else:
                logger.error('Job already running for the client '+ client_config['Item']['clientid'])
                msg = 'Job already running for the client '+ client_config['Item']['clientid']
                send_failure_email(client_config['Item'],msg)
        else:
            logger.error("No client config found in the DynamoDB table for "+client_config['Item']['clientid'])
            msg = "No client config found in the DynamoDB table for "+client_config['Item']['clientid']
            send_failure_email(client_config['Item'],msg)
    except Exception as e:
        logger.error("Error:"+str(e))
        msg = str(e)
        send_failure_email(client_config['Item'],msg)