# general variables

variable "project" {
  description = "Name of the Project"
}

variable "env_prefix" {
  description = "Environment specific prefix to uniquely identify resources for an environment. e.g. dev/qa/state/prod or dev-joe"
}

variable "is_prod" {
  type        = bool
  description = "Flag used to determine whether to create prod or non-prod resources"
}

variable "global_tags" {
  description = "Additional global tags to be applied to created resources"
  type        = map(string)
  default     = {}
}

variable "vpc_id" {}
