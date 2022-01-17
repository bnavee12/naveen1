# Persistent module

This is a singleton-style infrastructure module that contains account-level infrastructure. There should only be 1 instance of this in an AWS account. It provides:
- Fargate cluster for running container tasks
- Repository for hosting docker images
- Dynamo DB table for storing the config

<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | n/a |

## Inputs

NA

## Outputs

| Name | Description |
|------|-------------|
| <a name="dynamo"></a> [dynamodb\_tables](#output\_dynamodb\_tables) | Outputs related to dynamodb tables |
| <a name="output_egress_security_groups"></a> [egress\_security\_groups](#output\_egress\_security\_groups) | Returns a map of egress security group IDs by shorthand name. These can be used to allow egress from a lambda for example to resources in the VPC |
| <a name="output_fargate"></a> [fargate](#output\_fargate) | Outputs related to fargate, including the cluster ARN and the execution role (to be used in task definition execution\_role\_arn) |
| <a name="output_ecr"></a> [ecr](#output\_ecr) | ECR repository for storing the image |
<!-- END_TF_DOCS -->