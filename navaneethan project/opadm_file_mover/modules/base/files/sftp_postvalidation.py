import json
import boto3
import logging
import os
import botocore
import collections
import uuid
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import csv
import io
from boto3.dynamodb.conditions import Key, Attr
import sys
from urllib.parse import urlparse
import time
from datetime import datetime, timedelta

logger = logging.getLogger(os.environ["AWS_LAMBDA_FUNCTION_NAME"])
logger.setLevel(logging.INFO)

client_config = os.environ["CLIENT_CONFIG"]
client_job    = os.environ["CLIENT_JOB"]

"""
Function to get the client config information from the Dynamo DB
Output : client config
"""
def getclientconfig(client_id):
    logger.info('Fetching Client config details')
    dynamodb = boto3.resource('dynamodb')
    config_table = dynamodb.Table(client_config)
    client_config_data = config_table.get_item(Key={'clientid': client_id})
    return client_config_data['Item']

"""
Function to send Email.
Output : None
"""
def send_email(client_config,file_list):
    client = boto3.client('ssm')
    response = client.get_parameter(Name=os.environ["SMTP_CREDS"],WithDecryption=True)
    smtp_creds = json.loads(response['Parameter']['Value'])
    logger.info('Sending Final email to recipients')
    sender = 'oaextractionteam_dl@optum.com'
    receiver = list(client_config['contact_email'].split(","))
    msg = MIMEMultipart()
    msg['Subject'] = '**EXTERNAL** '+client_config['clientid']+'- OPADM File Transfer - Status of the transfer: Success'
    msg_body = """<html>
    <p>Greetings for the day!<br><br>This e-mail is to notify that the OPADM file transfer process has successfully completed. Please refer the attachment for additional details like the name of the files expected as part of the transfer, size of each file in the source before the transfer process began, size of each file after transferred to the destination folder and status of the transfer of each file.<br><br>Thanks,<br>Optum Extraction Team<br><br>
    <h4><span style="color: #003366;">List of files transferred with the transfer status</span><br></h2>
    <p><span style="color: #003366">
    <table border="1" cellpadding="5">
    <tr>
        <th><span style="color: #003366">Client</th>
        <th><span style="color: #003366">FileName</th>
        <th><span style="color: #003366">TransferStatus</th>
    </tr>
    """
    for files in file_list:
        if files['loggingType'] == 'INFO':
            msg_body += """
            <tr>
                <td align="left">"""+str(client_config['clientid'])+"""</td>
                <td align="right">"""+str(files['filename'])+"""</td>
                <td align="right">Success</td>
            </tr>
            """
        else:
            msg_body += """
            <tr>
                <td align="left">"""+str(client_config['clientid'])+"""</td>
                <td align="right">"""+str(files['filename'])+"""</td>
                <td align="right">"""+str(files['loggingType'])+"""</td>
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
Function to send Failure email in case of error.
Output : None
"""
def send_failure_email(jobid,clientid,file_list):
    client_config = getclientconfig(clientid)
    dynamodb = boto3.resource('dynamodb')
    job_table = dynamodb.Table(client_job)
    logger.info('Update Job status')
    job_table.update_item(
        Key={'clientid': client_config['clientid'],'jobid': jobid},
        UpdateExpression = "set jobstatus = :r",
        ExpressionAttributeValues={':r': 'Failed'},
        ReturnValues="UPDATED_NEW"
    )
    client = boto3.client('ssm')
    response = client.get_parameter(Name=os.environ["SMTP_CREDS"],WithDecryption=True)
    smtp_creds = json.loads(response['Parameter']['Value'])
    logger.info('Sending Failure email to recipients')
    sender = 'oaextractionteam_dl@optum.com'
    receiver = list(client_config['contact_email'].split(","))
    msg = MIMEMultipart()
    msg['Subject'] = '**EXTERNAL** '+clientid+'- OPADM File Transfer - Status of the transfer: Failure'
    msg_body = """<html>
    <p>Greetings for the day!<br><br>This e-mail is to notify that the OPADM file transfer process has failed. Please refer the attachment for additional details like the name of the files expected as part of the transfer, size of each file in the source before the transfer process began, size of each file after transferred to the destination folder and status of the transfer of each file.<br><br>Action needs to be taken by: Optum<br>Steps: Optum team will take care of the next steps for this failure and will keep the email chain posted with possible updates within 24 hours from when this is triggered. Client need not to take any action.<br><br>Thanks,<br>Optum Extraction Team"""
    if file_list != []:
        msg_body += """
        <h4><span style="color: #003366;">List of files transferred with the transfer status</span><br></h4>
        <p><span style="color: #003366">
        <table border="1" cellpadding="5">
        <tr>
            <th><span style="color: #003366">Client</th>
            <th><span style="color: #003366">FileName</th>
            <th><span style="color: #003366">TransferStatus</th>
        </tr>
        """
        for files in file_list:
            if files['loggingType'] == 'INFO':
                msg_body += """
                <tr>
                    <td align="left">"""+str(client_config['clientid'])+"""</td>
                    <td align="right">"""+str(files['filename'])+"""</td>
                    <td align="right">Success</td>
                </tr>
                """
            else:
                msg_body += """
                <tr>
                    <td align="left">"""+str(client_config['clientid'])+"""</td>
                    <td align="right">"""+str(files['filename'])+"""</td>
                    <td align="right">"""+str(files['loggingType'])+"""</td>
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

def get_filestatus(ecs_loggroup,logstream_name):
    log_client = boto3.client("logs")
    query_log_hours = 100
    query_log_mins = 1
    delay = 10
    query = f"filter @logStream = '{logstream_name}' | fields @timestamp, @message | parse @message '* * * : *: *' as date, time, loggingType, filename, loggingMessage | filter @message like /ERROR|INFO/ | display filename, loggingType, @timestamp, @message "
    response = log_client.start_query(
            logGroupName=ecs_loggroup,
            startTime=int((datetime.today() - timedelta(hours=query_log_hours, minutes=query_log_mins)).timestamp()),
            endTime=int(datetime.now().timestamp()),
            queryString=query,
        )
    time.sleep(delay)
    logger.info("Getting results of query ...")
    query_result = log_client.get_query_results(queryId=response["queryId"])
    print(query_result["results"])
    data_list = []
    for match_logs in query_result["results"]:
        json_data = {i["field"]: i["value"] for i in match_logs if i["field"] != "@ptr" and len(match_logs) >= 5}
        if json_data:
            if len(json_data["filename"].split(" ")) == 1:
                data_list.append(json_data)
    return data_list

def lambda_handler(event, context):
    try:
        dynamodb = boto3.resource('dynamodb')
        jobid = event['JobId']
        clientid = event['ClientId']
        ecs_name = event['ecsname']
        executionresult = event['executionResult']
        ecs_loggroup = '/ecs/'+ecs_name+'_def'
        ecs_logstream = 'ecs/'+ecs_name+'/'
        if event['Status']:
            client_config = getclientconfig(clientid)
            job_table = dynamodb.Table(client_job)
            logger.info('Update Job status to Completed')
            job_table.update_item(
                Key={'clientid': client_config['clientid'],'jobid': jobid},
                UpdateExpression = "set jobstatus = :r",
                ExpressionAttributeValues={':r': 'Completed'},
                ReturnValues="UPDATED_NEW"
            )
            taskid = executionresult['TaskArn'].rsplit('/', 1)[-1]
            logstream_name = ecs_logstream+taskid
            status_log = get_filestatus(ecs_loggroup,logstream_name)
            if status_log == []:
                send_failure_email(jobid,clientid,status_log)
            else:
                send_email(client_config,status_log)
        else:
            result = json.loads(executionresult['Cause'])
            taskid = result['TaskArn'].rsplit('/', 1)[-1]
            logstream_name = ecs_logstream+taskid
            status_log = get_filestatus(ecs_loggroup,logstream_name)
            send_failure_email(jobid,clientid,status_log)
    except Exception as e:
        logger.error("Error:"+str(e))
        file_list=''
        send_failure_email(jobid,clientid,file_list)