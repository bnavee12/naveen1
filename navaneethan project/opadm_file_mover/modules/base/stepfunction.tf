resource "aws_sfn_state_machine" "sfn_state_machine" {
  name     = "${local.name}-ascension"
  role_arn = module.stepfunction_role.arn
  definition = templatefile("${path.module}/files/sfn_google_transfer_task.json.tmpl", {
    cluster_arn         = var.fargate["cluster_arn"]
    task_definition_arn = module.opadm_ecs.ecs_taskdefinition_arn
    lambda_arn          = module.opadm-ascension-postvalidation-lambda.lambda_function_arn
    security_groups     = jsonencode([var.fargate["fargate_egress_sg"]])
    subnets             = jsonencode([var.private_subnets[0]])
  })
}

module "stepfunction_role" {
  source = "git::https://github.optum.com/oaccoe/aws_iam.git//profiles/iam-role?ref=v2.2.0"

  name                           = "StepfunctionRole_${local.name}"
  description                    = "Role to allow stepfunction to perform steps"
  assume_role_service_principals = ["states.amazonaws.com"]
  custom_inline_policy_count     = 1
  custom_inline_policy = [
    {
      custom_inline_name   = "stepfunction_allowed_permission"
      custom_inline_policy = data.aws_iam_policy_document.sfn_execution_policy.json
    },
  ]
}

data "aws_iam_policy_document" "sfn_execution_policy" {
  statement {
    effect    = "Allow"
    actions   = ["iam:PassRole", "iam:GetRole"]
    resources = [module.opadm_ecs.iam_taskrole_arn, module.opadm_ecs.iam_taskexecutionrole_arn, module.opadm-ascension-postvalidation-lambda.lambda_role_arn, module.opadm-sftpvalidation-lambda.lambda_role_arn]
  }
  statement {
    effect  = "Allow"
    actions = ["events:PutTargets", "events:PutRule", "events:DescribeRule"]
    resources = [
      "arn:${data.aws_partition.current.partition}:events:${data.aws_region.current_region.name}:${data.aws_caller_identity.current_identity.account_id}:rule/StepFunctionsGetEventsForECSTaskRule"
    ]
  }
  statement {
    effect    = "Allow"
    actions   = ["ecs:RunTask"]
    resources = [module.opadm_ecs.ecs_taskdefinition_arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["ecs:StopTask", "ecs:DescribeTasks"]
    resources = ["*"]
    condition {
      test     = "ArnEquals"
      variable = "ecs:cluster"
      values   = [var.fargate["cluster_arn"]]
    }
  }
  statement {
    effect    = "Allow"
    actions   = ["kms:GenerateDataKey", "kms:Decrypt"]
    resources = ["*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = [module.opadm-ascension-postvalidation-lambda.lambda_function_arn, module.opadm-sftpvalidation-lambda.lambda_function_arn]
  }
}


resource "aws_sfn_state_machine" "sfn_state_machine_sftp" {
  name     = "${local.name}-sftp"
  role_arn = module.stepfunction_role.arn
  definition = templatefile("${path.module}/files/sfn_sftp_transfer_task.json.tmpl", {
    cluster_arn         = var.fargate["cluster_arn"]
    task_definition_arn = module.opadm_ecs.ecs_taskdefinition_arn
    lambda_arn          = module.opadm-sftpvalidation-lambda.lambda_function_arn
    security_groups     = jsonencode([var.fargate["fargate_egress_sg"]])
    subnets             = jsonencode([var.private_subnets[0]])
  })
}