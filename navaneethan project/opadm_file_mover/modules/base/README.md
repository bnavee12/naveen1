# Base module

This module is an aggregate module that forms the basis of an environment. There can be multiple logical environments within an account.

This creates the following:
* Lambda for performing file pre and post validations and initiate file transfer
* Step function to orchestrate ECS task and Lambda.
* S3 bucket for storing the gsutil metadata.
* Module for copying data between AWS S3 and Google.

<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_env_prefix"></a> [env\_prefix](#input\_env\_prefix) | The name of the environment. Environment specific prefix to uniquely identify resources for an environment. e.g. dev/qa/state/prod or dev-joe | `any` | n/a | yes |
| <a name="input_fargate"></a> [fargate](#input\_fargate) | Expects the fargate output from the persistent module | `any` | n/a | yes |
| <a name="input_dynamo"></a> [dynamo](#input\_dynamo) | Expects the dynamo output from the persistent module | `any` | `{}` | no |
| <a name="input_is_prod"></a> [is\_prod](#input\_is\_prod) | Flag used to determine whether to create prod or non-prod resources | `bool` | n/a | yes |
| <a name="input_private_subnets"></a> [private\_subnets](#input\_private\_subnets) | The private subnets in the VPC | `any` | n/a | yes |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | The ID of the VPC that hosts the environment | `any` | n/a | yes |

## Outputs

NA
<!-- END_TF_DOCS -->