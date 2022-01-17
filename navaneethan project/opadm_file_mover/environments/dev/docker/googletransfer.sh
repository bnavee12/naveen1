#!/bin/bash

response=$(wget -O - 169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI)

export AWS_ACCESS_KEY_ID=$(echo "$response" | jq -r '.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo "$response" | jq -r '.SecretAccessKey')
export AWS_SECURITY_TOKEN=$(echo "$response" | jq -r '.Token')

GSUTIL_SP=$(aws ssm get-parameter --name $GSUTIL_SP --with-decryption --query 'Parameter.Value' --output text )
echo "$GSUTIL_SP" > /tmp/service-principal.json

gcloud auth activate-service-account --key-file /tmp/service-principal.json

gsutil $@

# until gsutil $@; do
#   sleep 1
# done

aws s3 cp manifest.txt s3://$MANIFEST_BUCKET/H984000/opadm/gsutil/$JobId.txt