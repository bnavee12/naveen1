data "aws_caller_identity" "current_identity" {
}

locals {
  account_id      = data.aws_caller_identity.current_identity.account_id
  project         = "opadm-filemover"
  env_prefix      = "dev"
  private_subnets = data.terraform_remote_state.data_acquisition_persistent.outputs.vpc["private_subnet_ids"]
  fargate         = data.terraform_remote_state.opadm_filemover_persistent.outputs.fargate
  dynamo          = data.terraform_remote_state.opadm_filemover_persistent.outputs.dynamo
  global_tags     = {}
}

module "base" {
  source = "../../modules/base"

  # environment setup
  project            = local.project
  env_prefix         = local.env_prefix
  private_subnets    = local.private_subnets
  fargate            = local.fargate
  dynamo             = local.dynamo
  input_sns          = "arn:aws:sns:us-east-1:679480943031:dev-opadm-extraction-notify"
  destination_bucket = "575066535343-sourcedata"
  logs_bucket        = "575066535343-data-acquisition-logs"
}