# Create ECR registry to store the ode-pipeline-master docker image
resource "aws_ecr_repository" "opadm_ecr_repo" {
  name                 = var.name
  image_tag_mutability = "MUTABLE" # for now, we will allow this to be mutable
  tags                 = var.tags
}

# If non-prod ECR, attach policy to allow production AWS account to read the image from here as well
resource "aws_ecr_repository_policy" "opadm_ecr_repo_policy" {
  repository = aws_ecr_repository.opadm_ecr_repo.name

  # The account number is hardcoded in the policy below instead of being a variable because it is allowing ECR access from a DIFFERENT account
  policy = <<EOF
{
    "Version": "2008-10-17",
    "Statement": [
        {
            "Sid": "AllowPushPull",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::754417584131:root"
            },
            "Action": [
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetRepositoryPolicy",
                "ecr:ListImages"
            ]
        }
    ]
}
EOF
}

resource "aws_ecr_lifecycle_policy" "repository" {
  count      = var.add_lifecycle_policy ? 1 : 0
  repository = aws_ecr_repository.opadm_ecr_repo.name

  policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Expire untagged images",
            "selection": {
                "countType": "sinceImagePushed",
                "countUnit": "days",
                "countNumber": ${var.lifecycle_policy_untagged_days},
                "tagStatus": "untagged"
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}