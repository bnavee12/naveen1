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

logger = logging.getLogger(os.environ["AWS_LAMBDA_FUNCTION_NAME"])
logger.setLevel(logging.INFO)

client_config = os.environ["CLIENT_CONFIG"]
client_job    = os.environ["CLIENT_JOB"]
log_bucket    = os.environ["MANIFEST_BUCKET"]

"""
Function to get the gsutil manifest(log) file from S3 location.
Output : Manifest file data
"""
def get_manifest_data(clientid,jobid):
    s3client = boto3.client('s3')
    logger.info('Getting Manifest data from S3 bucket')
    response = s3client.get_object(Bucket = log_bucket,Key='H984000/opadm/gsutil/'+jobid+'.txt')
    decode_data = response['Body'].read().decode("utf-8")
    manifest_data = list(csv.DictReader(io.StringIO(decode_data)))
    return manifest_data

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
def send_email(file_status,client_config):
    client = boto3.client('ssm')
    response = client.get_parameter(Name=os.environ["SMTP_CREDS"],WithDecryption=True)
    smtp_creds = json.loads(response['Parameter']['Value'])
    logger.info('Sending Final email to recipients')
    sender = 'oaextractionteam_dl@optum.com'
    receiver = list(client_config['contact_email'].split(","))
    msg = MIMEMultipart()
    msg['Subject'] = '**EXTERNAL** '+client_config['clientid']+'- OPADM File Transfer - Status of the transfer: Success'
    msg_body = """
        <html>
        <p>Greetings for the day!<br><br>This e-mail is to notify that the OPADM file transfer process has successfully completed. Please refer the attachment for additional details like the name of the files expected as part of the transfer, size of each file in the source before the transfer process began, size of each file after transferred to the destination folder and status of the transfer of each file.<br><br>Thanks,<br>Optum Extraction Team<br><br>
        <h4><span style="color: #003366;">List of files transferred with the transfer status</span><br></h2>
        <p><span style="color: #003366">
        <table border="1" cellpadding="5">
        <tr>
            <th><span style="color: #003366">Client</th>
            <th><span style="color: #003366">FilePath</th>
            <th><span style="color: #003366">FileName</th>
            <th><span style="color: #003366">Startedtime</th>
            <th><span style="color: #003366">Completedtime</th>
            <th><span style="color: #003366">SourceFileSize(Size in GB)</th>
            <th><span style="color: #003366">DestinationFileSize(Size in GB)</th>
            <th><span style="color: #003366">TransferStatus</th>
        </tr>
        """
    for s3file in file_status:
        start_time = datetime.datetime.strptime(s3file['Start'],"%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(s3file['End'],"%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
        source_size = round(int(s3file['Source Size'])/(1024*1024*1024),5)
        dest_size = round(int(s3file['Bytes Transferred'])/(1024*1024*1024),5)
        if s3file['Result'] == 'OK':
            msg_body += """
            <tr>
                <td align="left">"""+str(client_config['clientid'])+"""</td>
                <td align="right">"""+str(os.path.dirname(s3file['Source']))+"""</td>
                <td align="right">"""+str(os.path.basename(s3file['Source']))+"""</td>
                <td align="right">"""+str(start_time)+"""</td>
                <td align="right">"""+str(end_time)+"""</td>
                <td align="right">"""+str(source_size)+"""</td>
                <td align="right">"""+str(dest_size)+"""</td>
                <td align="right">Success</td>
            </tr>
            """
        else:
            msg_body += """
            <tr>
                <td align="left">"""+str(client_config['clientid'])+"""</td>
                <td align="right">"""+str(os.path.dirname(s3file['Source']))+"""</td>
                <td align="right">"""+str(os.path.basename(s3file['Source']))+"""</td>
                <td align="right">"""+str(start_time)+"""</td>
                <td align="right">"""+str(end_time)+"""</td>
                <td align="right">"""+str(source_size)+"""</td>
                <td align="right">"""+str(dest_size)+"""</td>
                <td align="right">Failure</td>
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
def send_failure_email(jobid,clientid):
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
    msg['Subject'] = '**EXTERNAL** '+clientid+'- OPADM File Transfer - Status of the transfer: Success'
    msg_body = """<html>
    <p>Greetings for the day!<br><br>This e-mail is to notify that the OPADM file transfer process has  failed. Please refer the attachment for additional details like the name of the files expected as part of the transfer, size of each file in the source before the transfer process began, size of each file after transferred to the destination folder and status of the transfer of each file.<br><br>Action needs to be taken by: Optum<br><br>Steps: Optum team will take care of the next steps for this failure and will keep the email chain posted with possible updates within 24 hours from when this is triggered. Client need not to take any action.<br><br>Thanks,<br>Optum Extraction Team
    </html>"""
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
        dynamodb = boto3.resource('dynamodb')
        jobid = event['JobId']
        clientid = event['ClientId']
        if event['Status']:
            client_config = getclientconfig(clientid)
            manifest_data = get_manifest_data(clientid,jobid)
            if manifest_data != []:
                job_table = dynamodb.Table(client_job)
                logger.info('Update Job status to Completed')
                job_table.update_item(
                    Key={'clientid': client_config['clientid'],'jobid': jobid},
                    UpdateExpression = "set jobstatus = :r",
                    ExpressionAttributeValues={':r': 'Completed'},
                    ReturnValues="UPDATED_NEW"
                )
                send_email(manifest_data,client_config)
            else:
                logger.error('No data found in manifest file')
                send_failure_email(jobid,clientid)
        else:
            send_failure_email(jobid,clientid)
    except Exception as e:
        logger.error("Error:"+str(e))
        send_failure_email(jobid,clientid)