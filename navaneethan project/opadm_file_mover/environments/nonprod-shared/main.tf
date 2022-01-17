locals {
  project    = "opadm-filemover"
  env_prefix = "nonprod-shared"
  vpc_id     = data.terraform_remote_state.data_acquisition_persistent.outputs.vpc["id"]
}

module "persistent" {
  source = "../../modules/persistent"

  # environment setup
  project    = local.project
  env_prefix = local.env_prefix
  vpc_id     = local.vpc_id

  is_prod = false
}