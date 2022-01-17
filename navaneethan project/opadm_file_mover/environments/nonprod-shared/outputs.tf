output "fargate" {
  description = "Outputs related to fargate"
  value       = module.persistent.fargate
}

output "dynamo" {
  description = "Outputs related to Dynamo"
  value       = module.persistent.dynamo
}
