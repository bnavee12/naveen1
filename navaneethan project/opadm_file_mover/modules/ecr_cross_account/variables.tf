variable "name" {
  description = "The name for the ECR repository"
  type        = string
}

variable "add_lifecycle_policy" {
  description = "Whether to include a default lifecycle policy"
  type        = bool
  default     = true
}

variable "lifecycle_policy_untagged_days" {
  description = "The number of days an untagged image will be kept"
  type        = number
  default     = 14
}

variable "tags" {
  type    = map(string)
  default = {}
}