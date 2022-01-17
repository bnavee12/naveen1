#!/bin/bash
aws s3 cp $1 $2 --recursive

clientid=$3
client_jobtable=$4
jobid=$5

touch $clientid.done

aws s3 cp $clientid.done $2

aws dynamodb update-item \
    --table-name $client_jobtable \
    --key "{\"clientid\":{\"S\": \"$clientid\"}, \"jobid\":{\"S\": \"$jobid\"}}" \
    --update-expression "SET jobstatus = :sd" \
    --expression-attribute-values '{":sd": {"S": "Completed"}}' \
    --return-values ALL_NEW