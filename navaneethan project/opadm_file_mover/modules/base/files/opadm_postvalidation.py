import sys
import boto3
import os
import logging
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from urllib.parse import urlparse

logger = logging.getLogger(os.environ["AWS_LAMBDA_FUNCTION_NAME"])
logger.setLevel(logging.INFO)
client_config = os.environ["CLIENT_CONFIG"]

"""
Function to get the client config information from the Dynamo DB
Output : client config
"""
def getclientconfig(dynamodb):
    logger.info('Fetching Client config details')
    config_table = dynamodb.Table(client_config)
    client_config_data = config_table.scan()
    return client_config_data['Items']

"""
Function to get the email content
"""
def client_email_notification(client_conf,variable,items,log_file):
    client = boto3.client('s3')
    if 'DoneFileNotFound' in items['Key']:
        logger.info('Flag not found (.done) log file found for the client')
        tmp_filename = ''
        subject = client_conf['clientid'] + ' - ' + variable + ' File Transfer - Flag file not found (.done)'
        msg_body = "Greetings for the day! \r\rThis e-mail is to notify that the {} automated file transfer process couldn't start because the flag file (.done) was not available in the sftp server. \r\rAction to be taken by the PRODOPS team: Kindly make sure the .done file is present along with the data files. \r\rThanks, \rOptum Extraction Team".format(variable)
        client.delete_object(Bucket=log_file.netloc,Key=items['Key'])
        logger.info('Flag not found (.done) log file removed from the S3 location')
        return subject,tmp_filename,msg_body
    elif 'HnumberNotMatched' in items['Key']:
        logger.info('HnumberNotMatched log file found for the client')
        tmp_filename = ''
        subject = client_conf['clientid'] + ' - ' + variable + ' File Transfer - Client Hnumber not matched'
        msg_body = "Greetings for the day, \r\rThis e-mail is to notify that the Hnumber present in the .done file name was not matching with the Hnumber that is expected for the client. So the file transfer couldn't start. \r\rAction to be taken by the PRODOPS team: Kindly verfiy and correct the Hnumber in the .done file name. \r\rThanks, \rOptum Extraction Team"
        client.delete_object(Bucket=log_file.netloc,Key=items['Key'])
        logger.info('HnumberNotMatched log file removed from the S3 location')
        return subject,tmp_filename,msg_body
    elif 'NoDataFilesPresent' in items['Key']:
        logger.info('NoDataFilesPresent log file found for the client')
        tmp_filename = ''
        subject = client_conf['clientid'] + ' - ' + variable + ' File Transfer - No data files present in sFTP'
        msg_body = "Greetings for the day, \r\rThis e-mail is to notify that the {} automated file transfer couldn't progress because no data files (apart from .done file) were present in the sftp. \r\rAction to be taken by the PRODOPS team: Kindly place the data files along with the .done file. \r\rThanks, \rOptum Extraction Team".format(variable)
        client.delete_object(Bucket=log_file.netloc,Key=items['Key'])
        logger.info('NoDataFilesPresent log file removed from the S3 location')
        return subject,tmp_filename,msg_body
    elif 'FilesAlreadyPresent' in items['Key']:
        logger.info('FilesAlreadyPresent log file found for the client')
        tmp_filename = ''
        subject = client_conf['clientid'] + ' - ' + variable + ' File Transfer - No new files to transfer'
        msg_body = "Greetings for the day, \r\rThis e-mail is to notify that the {} automated file transfer couldn't progress because the files in sftp has been already transferred to the destination (files were compared based on the following sequential order - Name, Lastmodifieddate, size, count). \r\rAction to be taken by the PRODOPS team: Kindly make sure the latest set of files are sent to the sftp. \r\rThanks, \rOptum Extraction Team".format(variable)
        client.delete_object(Bucket=log_file.netloc,Key=items['Key'])
        logger.info('FilesAlreadyPresent log file removed from the S3 location')
        return subject,tmp_filename,msg_body
    elif 'ProcessStarted' in items['Key']:
        logger.info('ProcessStarted log file found for the client')
        tmp_filename = '/tmp/'+os.path.basename(items['Key'])
        client.download_file(log_file.netloc,items['Key'],tmp_filename)
        subject = '**EXTERNAL** ' + client_conf['clientid'] + ' - ' + variable + ' File Transfer - File transfer process started'
        msg_body = "Greetings for the day, \r\rThis e-mail is to notify that the {} automated file transfer has started for the latest set of files. Further status updates will be sent when the transfer gets completed. \r\rThanks, \rOptum Extraction Team".format(variable)
        client.delete_object(Bucket=log_file.netloc,Key=items['Key'])
        logger.info('ProcessStarted log file removed from the S3 location')
        return subject,tmp_filename,msg_body
    elif 'NotEnoughSpace' in items['Key']:
        logger.info('NotEnoughSpace log file found for the client')
        tmp_filename = '/tmp/'+os.path.basename(items['Key'])
        client.download_file(log_file.netloc,items['Key'],tmp_filename)
        subject = '**EXTERNAL** ' + client_conf['clientid'] + ' - ' + variable + ' File Transfer - Not enough space in drive to accommodate new files'
        msg_body = "Greetings for the day, \r\rThis e-mail is to notify that the {} file transfer couldn't progress because there wasn't enough space in the destination to accommodate the new files. \r\rAction needs to be taken by: Client\rSteps: Please do clean-up the drive to accumulate free space and notify the same email thread after the clean-up (possibly within 24 hours from receiving the alert).\r\rThanks, \rOptum Extraction Team".format(variable)
        client.delete_object(Bucket=log_file.netloc,Key=items['Key'])
        logger.info('NotEnoughSpace log file removed from the S3 location')
        return subject,tmp_filename,msg_body
    elif 'Success' in items['Key']:
        logger.info('Success log file found for the client')
        tmp_filename = '/tmp/'+os.path.basename(items['Key'])
        client.download_file(log_file.netloc,items['Key'],tmp_filename)
        subject = '**EXTERNAL** ' + client_conf['clientid'] + ' - ' + variable + ' File Transfer - Status of the transfer: Success'
        msg_body = "Greetings for the day, \r\rThis e-mail is to notify that the {} file transfer process has successfully completed. Please refer the attachment for additional details like the name of the files expected as part of the transfer, size of each file in the source before the transfer process began, size of each file after transferred to the destination folder and status of the transfer of each file. \r\rThanks, \rOptum Extraction Team".format(variable)
        client.delete_object(Bucket=log_file.netloc,Key=items['Key'])
        logger.info('Success log file removed from the S3 location')
        return subject,tmp_filename,msg_body
    elif 'Failure' in items['Key']:
        logger.info('Failure log file found for the client')
        tmp_filename = '/tmp/'+os.path.basename(items['Key'])
        client.download_file(log_file.netloc,items['Key'],tmp_filename)
        subject = '**EXTERNAL** ' + client_conf['clientid'] + ' - ' + variable + ' File Transfer - Status of the transfer: Failure'
        msg_body = "Greetings for the day! \r\r This e-mail is to notify that the {} file transfer process has  failed. Please refer the attachment for additional details like the name of the files expected as part of the transfer, size of each file in the source before the transfer process began, size of each file after transferred to the destination folder and status of the transfer of each file.\r\rAction needs to be taken by: Optum \rSteps: Optum team will take care of the next steps for this failure and will keep the email chain posted with possible updates within 24 hours from when this is triggered. Client need not to take any action.\r\rThanks, \rOptum Extraction Team".format(variable)
        client.delete_object(Bucket=log_file.netloc,Key=items['Key'])
        logger.info('Failure log file removed from the S3 location')
        return subject,tmp_filename,msg_body
    else:
        logger.info('Invalid log file found for the client')
        subject=''
        msg_body=''
        tmp_filename=''
        return subject,tmp_filename,msg_body

"""
Function to check for success/error log file in S3 location and delete upon email notification.
Output : None
"""
def process_logfile(client_conf):
    logger.info('Checking log file for client '+client_conf['clientid'])
    client = boto3.client('s3')
    log_file = urlparse(client_conf['destination']['loglocation'], allow_fragments=False)
    response = client.list_objects_v2(Bucket = log_file.netloc, Prefix = log_file.path.lstrip('/'))
    for items in response['Contents']:
        if 'OPADM' in items['Key']:
            variable = 'OPADM'
            subject,tmp_filename,msg_body = client_email_notification(client_conf,variable,items,log_file)
            if msg_body:
                send_email(client_conf,subject,tmp_filename,msg_body)
        elif 'OCCP' in items['Key']:
            variable = 'OCCP'
            subject,tmp_filename,msg_body = client_email_notification(client_conf,variable,items,log_file)
            if msg_body:
                send_email(client_conf,subject,tmp_filename,msg_body)
        elif 'Custom' in items['Key']:
            variable = 'Custom'
            subject,tmp_filename,msg_body = client_email_notification(client_conf,variable,items,log_file)
            if msg_body:
                send_email(client_conf,subject,tmp_filename,msg_body)

"""
Function to send Email.
Output : None
"""
def send_email(client_conf,subject,tmp_filename,msg_body):
    client = boto3.client('ssm')
    logger.info('Sending email to the configured recipients')
    response = client.get_parameter(Name=os.environ["SMTP_CREDS"],WithDecryption=True)
    smtp_creds = json.loads(response['Parameter']['Value'])
    msg = MIMEMultipart()
    msg['Subject'] = subject
    sender = 'oaextractionteam_dl@optum.com'
    receiver = list(client_conf['contact_email'].split(","))
    part = MIMEText(msg_body)
    msg.attach(part)
    if tmp_filename:
        attachment = MIMEApplication(open(tmp_filename, 'rb').read())
        attachment.add_header('Content-Disposition','attachment',filename=os.path.basename(tmp_filename))
        msg.attach(attachment)
    smtpObj = smtplib.SMTP("omail.o360.cloud", 587)
    smtpObj.starttls()
    smtpObj.login(smtp_creds['username'],smtp_creds['password'])
    smtpObj.sendmail(sender, receiver, msg.as_string())
    smtpObj.quit()
    logger.info('Email sent to the configured recipients')

def lambda_handler(event, context):
    try:
        dynamodb = boto3.resource('dynamodb')
        client_config = getclientconfig(dynamodb)
        for client_conf in client_config:
            if client_conf['destination']['location'] == 's3':
                process_logfile(client_conf)
    except Exception as e:
        logger.error("Error:"+str(e))