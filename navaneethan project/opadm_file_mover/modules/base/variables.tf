variable "project" {
  description = "Name of the Project"
}

variable "env_prefix" {
  description = "The name of the environment. Environment specific prefix to uniquely identify resources for an environment. e.g. dev/qa/state/prod or dev-joe"
}

variable "private_subnets" {
  description = "The private subnets in the VPC"
}

variable "global_tags" {
  description = "Additional global tags to be applied to created resources"
  type        = map(string)
  default     = {}
}

variable "fargate" {
  description = "Expects the fargate output from the persistent module"
}

variable "gsutil_ssm_parameter" {
  description = "SSM paranter that stores secret information for using gsutil"
  default     = null
}

variable "dynamo" {
  description = "Expects the dynamo output from the persistent module"
}

variable "input_sns" {
  description = "Expects the SNS ARN to trigger the lambda"
}

variable "destination_bucket" {
  description = "Bucket name of the OPADM clients destination"
}

variable "logs_bucket" {
  description = "Bucket name of logs"
}