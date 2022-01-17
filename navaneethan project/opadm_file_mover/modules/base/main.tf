data "aws_caller_identity" "current_identity" {}
data "aws_region" "current_region" {}
data "aws_partition" "current" {}

data "aws_ssm_parameter" "google_sp" {
  name = "/das/opadm/ascension/sp"
}
data "aws_ssm_parameter" "opadm_smtp" {
  name = "/das/opadm/smtp"
}

locals {
  aws_region     = data.aws_region.current_region.name
  name           = "${var.env_prefix}-${var.project}"
  aws_account_id = data.aws_caller_identity.current_identity.account_id
  client_data    = jsondecode(file("${path.module}/files/client_config.json"))
  # ECR URL is hardcoded because both production and non-production accounts will read images from the nonprod account.
  container_image_url_with_tag = "575066535343.dkr.ecr.us-east-1.amazonaws.com/opadm-filemover:latest"
}

module "opadm_ecs" {
  source               = "git::https://github.optum.com/oaccoe/aws_azcopy_rclone.git//profiles/ecs_azcopy_rclone?ref=v1.0.5"
  name                 = local.name
  container_image_arn  = local.container_image_url_with_tag
  container_name       = local.name
  ecs_tasks_permission = data.aws_iam_policy_document.ecs_tasks_permission.json
  env_map = [
    {
      name  = "GSUTIL_SP",
      value = data.aws_ssm_parameter.google_sp.name
    },
    {
      name  = "MANIFEST_BUCKET",
      value = var.logs_bucket
  }]
}

data "aws_iam_policy_document" "ecs_tasks_permission" {
  statement {
    sid    = "ECSTaskS3Permission"
    effect = "Allow"
    actions = [
      "s3:PutObject"
    ]
    resources = ["arn:aws:s3:::${var.destination_bucket}", "arn:aws:s3:::${var.destination_bucket}/*", "arn:aws:s3:::${var.logs_bucket}", "arn:aws:s3:::${var.logs_bucket}/*"]
  }
  statement {
    sid    = "ECSTaskS3PermissionCross"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:ListBucket"
    ]
    resources = ["*"] # Giving global read access to fetch data from all S3 buckets and use it for multiple transfers
  }
  statement {
    sid    = "ECSTaskDynamoDBPermission"
    effect = "Allow"
    actions = [
      "dynamodb:Query",
      "dynamodb:UpdateItem"
    ]
    resources = [var.dynamo["client_config_arn"], var.dynamo["client_job_arn"]]
  }
  statement {
    sid    = "ECSTaskLogsPermission"
    effect = "Allow"
    actions = [
      "logs:*"
    ]
    resources = ["*"]
  }
  statement {
    sid    = "ECSTaskSSMPermission"
    effect = "Allow"
    actions = [
      "ssm:DescribeParameters",
      "ssm:GetParameters",
      "ssm:GetParameter",
      "ssm:GetParametersByPath",
      "kms:Decrypt"
    ]
    resources = ["arn:aws:ssm:${local.aws_region}:${local.aws_account_id}:parameter/das/*"]
  }
}

resource "aws_dynamodb_table_item" "configuration_item" {
  table_name = var.dynamo["client_config"]
  for_each   = { for client in local.client_data.clients : client.clientid["S"] => client }
  hash_key   = "clientid"
  item       = jsonencode(each.value)
}