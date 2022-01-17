output "repository" {
  description = "The ARN of the ECR (Elastic Container Registry)"
  value = {
    arn            = aws_ecr_repository.opadm_ecr_repo.arn
    id             = aws_ecr_repository.opadm_ecr_repo.registry_id
    name           = aws_ecr_repository.opadm_ecr_repo.name
    repository_url = aws_ecr_repository.opadm_ecr_repo.repository_url
  }
}