data "aws_region" "current_region" {
}

data "aws_caller_identity" "current_identity" {
}

locals {
  aws_region = data.aws_region.current_region.name
  account_id = data.aws_caller_identity.current_identity.account_id
  persistent_tags = merge(var.global_tags, {
    is_prod = var.is_prod
    }
  )

}

# Creating a single Fargate ECS cluster per AWS account.
# Each application and logical environment can create its own task definitions, services, and containers
resource "aws_ecs_cluster" "fargate_cluster" {
  name = "${var.env_prefix}-${var.project}-fargate-cluster"
  tags = local.persistent_tags

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

module "ecr_opadm" {
  count  = var.is_prod ? 0 : 1
  source = "../ecr_cross_account"
  name   = var.project
  tags   = local.persistent_tags
}