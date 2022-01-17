resource "aws_dynamodb_table" "client_config" {
  name           = format("%s-clients-config", var.project)
  read_capacity  = 10
  write_capacity = 10
  hash_key       = "clientid"
  tags           = local.persistent_tags

  attribute {
    name = "clientid"
    type = "S"
  }
}

resource "aws_dynamodb_table" "client_job" {
  name           = format("%s-clients-job", var.project)
  read_capacity  = 10
  write_capacity = 10
  hash_key       = "clientid"
  range_key      = "jobid"
  tags           = local.persistent_tags

  attribute {
    name = "clientid"
    type = "S"
  }

  attribute {
    name = "jobid"
    type = "S"
  }
}