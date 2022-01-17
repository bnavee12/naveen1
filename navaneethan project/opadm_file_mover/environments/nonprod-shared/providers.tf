provider "aws" {
  region = var.aws_region

  default_tags { # requires aws provider >= 3.38.0
    tags = {
      "optum:application"           = local.project
      "optum:terraform_environment" = local.env_prefix
      "optum:environment"           = "dev"
      "IAC_Repo"                    = "DataFactoryEnablement/opadm_filemover_terraform"
      "terraform"                   = "true"
    }
  }
}