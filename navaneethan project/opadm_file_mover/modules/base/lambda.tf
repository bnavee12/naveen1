locals {
  python_version = "python3.8"
}

module "opadm-preprocess-lambda" {
  source         = "git::https://github.com/terraform-aws-modules/terraform-aws-lambda.git?ref=v2.4.0"
  create         = true
  description    = "Lambda function to perform pre validation and initiate file transfer process"
  source_path    = "${path.module}/files/opadm_prevalidation.py"
  runtime        = local.python_version
  timeout        = "900"
  handler        = "opadm_prevalidation.lambda_handler"
  create_package = true
  publish        = true
  function_name  = "${local.name}-opadm-prevalidation"

  environment_variables = {
    CONTAINER_NAME        = local.name
    CLIENT_CONFIG         = var.dynamo["client_config"]
    CLIENT_JOB            = var.dynamo["client_job"]
    SMTP_CREDS            = data.aws_ssm_parameter.opadm_smtp.name
    STEPFUNCTION_ARN      = aws_sfn_state_machine.sfn_state_machine.arn
    SFTP_STEPFUNCTION_ARN = aws_sfn_state_machine.sfn_state_machine_sftp.arn
    TASK_DEFINITION       = module.opadm_ecs.ecs_taskdefinition_arn
    CLUSTER               = var.fargate["cluster_arn"]
    SUBNETS               = var.private_subnets[0]
    SECURITY_GROUP        = var.fargate["fargate_egress_sg"]
  }

  allowed_triggers = {
    SNSTrigger = {
      principal  = "sns.amazonaws.com"
      source_arn = var.input_sns
    }
  }

  attach_policy_json = true
  policy_json        = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecs:RunTask"
            ],
            "Resource": "${module.opadm_ecs.ecs_taskdefinition_arn}"
        },
        {
            "Effect": "Allow",
            "Action": [
                "states:StartExecution"
            ],
            "Resource": ["${aws_sfn_state_machine.sfn_state_machine.arn}","${aws_sfn_state_machine.sfn_state_machine_sftp.arn}"]
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:PassRole", 
                "iam:GetRole"
            ],
            "Resource": ["${module.stepfunction_role.arn}","${module.opadm_ecs.iam_taskrole_arn}","${module.opadm_ecs.iam_taskexecutionrole_arn}"]
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": ["${var.dynamo["client_config_arn"]}","${var.dynamo["client_job_arn"]}"]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:ListBucket"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": "${data.aws_ssm_parameter.opadm_smtp.arn}"
        }
    ]
  }
  EOF

}

module "opadm-ascension-postvalidation-lambda" {
  source         = "git::https://github.com/terraform-aws-modules/terraform-aws-lambda.git?ref=v2.4.0"
  create         = true
  description    = "Lambda function to send status of transfer to Ascension based on manifest file"
  source_path    = "${path.module}/files/google_postvalidation.py"
  runtime        = local.python_version
  timeout        = "900"
  handler        = "google_postvalidation.lambda_handler"
  create_package = true
  publish        = true
  function_name  = "${local.name}-ascension-postvalidation"

  environment_variables = {
    CLIENT_CONFIG   = var.dynamo["client_config"]
    CLIENT_JOB      = var.dynamo["client_job"]
    MANIFEST_BUCKET = var.logs_bucket
    SMTP_CREDS      = data.aws_ssm_parameter.opadm_smtp.name
  }

  attach_policy_json = true
  policy_json        = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:UpdateItem"
            ],
            "Resource": ["${var.dynamo["client_config_arn"]}","${var.dynamo["client_job_arn"]}"]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": ["arn:aws:s3:::${var.logs_bucket}","arn:aws:s3:::${var.logs_bucket}/*"]
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": "${data.aws_ssm_parameter.opadm_smtp.arn}"
        }
    ]
  }
  EOF

}

module "opadm-sftpvalidation-lambda" {
  source         = "git::https://github.com/terraform-aws-modules/terraform-aws-lambda.git?ref=v2.4.0"
  create         = true
  description    = "Lambda function to send status of S3 to SFTP transfer"
  source_path    = "${path.module}/files/sftp_postvalidation.py"
  runtime        = local.python_version
  timeout        = "900"
  handler        = "sftp_postvalidation.lambda_handler"
  create_package = true
  publish        = true
  function_name  = "${local.name}-sftp-postvalidation-lambda"

  environment_variables = {
    CLIENT_CONFIG = var.dynamo["client_config"]
    CLIENT_JOB    = var.dynamo["client_job"]
    SMTP_CREDS    = data.aws_ssm_parameter.opadm_smtp.name
  }

  attach_policy_json = true
  policy_json = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Effect" : "Allow",
          "Action" : [
            "dynamodb:GetItem",
            "dynamodb:Query",
            "dynamodb:UpdateItem"
          ],
          "Resource" : ["${var.dynamo["client_config_arn"]}", "${var.dynamo["client_job_arn"]}"]
        },
        {
          "Effect" : "Allow",
          "Action" : [
            "logs:*"
          ],
          "Resource" : "*"
        },
        {
          "Effect" : "Allow",
          "Action" : [
            "ssm:GetParameter"
          ],
          "Resource" : "${data.aws_ssm_parameter.opadm_smtp.arn}"
        },
        {
          "Effect" : "Allow",
          "Action" : [
            "logs:GetLogEvents"
          ],
          "Resource" : "arn:aws:logs:${local.aws_region}:${local.aws_account_id}:log-group:/ecs/dev-opadm-filemover_def:*"
        }
      ]
  })

}

module "opadm-postvalidation-lambda" {
  source         = "git::https://github.com/terraform-aws-modules/terraform-aws-lambda.git?ref=v2.4.0"
  create         = true
  description    = "Lambda function to check for Success/Error log file for S3 to S3 transfer"
  source_path    = "${path.module}/files/opadm_postvalidation.py"
  runtime        = local.python_version
  timeout        = "900"
  handler        = "opadm_postvalidation.lambda_handler"
  create_package = true
  publish        = true
  function_name  = "${local.name}-s3-postvalidation"

  environment_variables = {
    CLIENT_CONFIG = var.dynamo["client_config"]
    SMTP_CREDS    = data.aws_ssm_parameter.opadm_smtp.name
  }

  allowed_triggers = {
    Scheduledtrigger = {
      principal  = "events.amazonaws.com"
      source_arn = aws_cloudwatch_event_rule.schedule_trigger.arn
    }
  }

  attach_policy_json = true
  policy_json        = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:Scan"
            ],
            "Resource": ["${var.dynamo["client_config_arn"]}"]
        },    
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:ListBucket",
                "s3:DeleteObject"
            ],
            "Resource": ["arn:aws:s3:::${var.destination_bucket}","arn:aws:s3:::${var.destination_bucket}/*"]
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": "${data.aws_ssm_parameter.opadm_smtp.arn}"
        }
    ]
  }
  EOF
}


##############################
# Cloudwatch Event rule to trigger Lambda
#############################

resource "aws_cloudwatch_event_rule" "schedule_trigger" {
  name                = "${var.env_prefix}-${var.project}-trigger"
  description         = "Fires every thirty minutes"
  schedule_expression = "rate(30 minutes)"
}

resource "aws_cloudwatch_event_target" "schedule_target" {
  rule       = aws_cloudwatch_event_rule.schedule_trigger.name
  arn        = module.opadm-postvalidation-lambda.lambda_function_arn
  depends_on = [module.opadm-postvalidation-lambda]
}

resource "aws_sns_topic_subscription" "fileupload_sns" {
  topic_arn  = var.input_sns
  protocol   = "lambda"
  endpoint   = module.opadm-preprocess-lambda.lambda_function_arn
  depends_on = [module.opadm-preprocess-lambda]
}
