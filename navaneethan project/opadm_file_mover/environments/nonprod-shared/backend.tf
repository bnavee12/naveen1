terraform {
  required_version = ">= 0.14.10"

  backend "s3" {
    region         = "us-east-1"
    bucket         = "575066535343-ode-foundation-tfstate"
    key            = "opadm-filemover/nonprod-shared.tfstate"
    dynamodb_table = "tfstate-lock"
    encrypt        = "true"
  }
}


data "terraform_remote_state" "data_acquisition_persistent" {
  backend = "s3"

  config = {
    bucket = "575066535343-ode-foundation-tfstate"
    key    = "data_acquisition_ingestion1_server/nonprod-shared.tfstate"
    region = "us-east-1"
  }
}