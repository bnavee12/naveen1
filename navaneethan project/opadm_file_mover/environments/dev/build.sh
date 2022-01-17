#!/bin/bash

# Fail fast
set -e

# This is the order of arguments
build_folder=$1
aws_ecr_repository_url=$2
aws_ecr_repository_tag=$3

# kept for backwards compatibility
aws_region=$4

# Allow overriding the aws region from system
if [ "$aws_region" != "" ]; then
  aws_extra_flags="--region $aws_region"
else
  aws_extra_flags=""
fi

# Check that aws is installed
which aws > /dev/null || { echo 'ERROR: aws-cli is not installed' ; exit 1; }

# Check that docker is installed and running
which docker > /dev/null && docker ps > /dev/null || { echo 'ERROR: docker is not running' ; exit 1; }

# Connect into aws
aws ecr get-login-password $aws_extra_flags | docker login --username AWS --password-stdin $aws_ecr_repository_url

# Some Useful Debug
echo "Building Docker Image $aws_ecr_repository_url from $build_folder/Dockerfile"

# Build image
docker build -t $aws_ecr_repository_url:$aws_ecr_repository_tag $build_folder
docker build -t $aws_ecr_repository_url:latest $build_folder

# Push image
docker push $aws_ecr_repository_url:$aws_ecr_repository_tag
docker push $aws_ecr_repository_url:latest