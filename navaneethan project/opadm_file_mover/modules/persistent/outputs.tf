output "fargate" {
  description = "Outputs related to fargate, including the cluster ARN and the execution role (to be used in task definition execution_role_arn)"
  value = {
    cluster_arn       = aws_ecs_cluster.fargate_cluster.arn
    fargate_egress_sg = aws_security_group.fargate_egress_sg.id
  }
}

output "dynamo" {
  description = "Outputs dynamoDB tables created"
  value = {
    client_config     = aws_dynamodb_table.client_config.id
    client_job        = aws_dynamodb_table.client_job.id
    client_config_arn = aws_dynamodb_table.client_config.arn
    client_job_arn    = aws_dynamodb_table.client_job.arn
  }
}

output "opadm_ecr" {
  description = "The OPADM elastic container registry"
  value       = module.ecr_opadm[*].repository
}