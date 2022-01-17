#!/bin/bash

response=$(aws ssm get-parameter --name $SFTP_CREDS --with-decryption --query 'Parameter.Value' --output text )

export RCLONE_SFTP_HOST=$(echo "$response" | jq -r '.host')
export RCLONE_SFTP_USER=$(echo "$response" | jq -r '.username')
PASS=$(echo "$response" | jq -r '.password')
export RCLONE_SFTP_PASS=$(rclone obscure "$PASS")

rclone $@