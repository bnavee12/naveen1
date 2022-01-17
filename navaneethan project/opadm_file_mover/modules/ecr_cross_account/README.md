# ECR with Cross Account access

This is a small module intended to create an ECR (Elastic Container Respository) that will also be accessible from the Production account. This way strongly-versioned images can be uploaded to the non-prod ECR but still be leveraged in the production account.

<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | n/a |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_ecr_lifecycle_policy.repository](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_lifecycle_policy) | resource |
| [aws_ecr_repository.repository](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository) | resource |
| [aws_ecr_repository_policy.repository](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository_policy) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_add_lifecycle_policy"></a> [add\_lifecycle\_policy](#input\_add\_lifecycle\_policy) | Whether to include a default lifecycle policy | `bool` | `true` | no |
| <a name="input_lifecycle_policy_untagged_days"></a> [lifecycle\_policy\_untagged\_days](#input\_lifecycle\_policy\_untagged\_days) | The number of days an untagged image will be kept | `number` | `14` | no |
| <a name="input_name"></a> [name](#input\_name) | The name for the ECR repository | `string` | n/a | yes |
| <a name="input_tags"></a> [tags](#input\_tags) | n/a | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_repository"></a> [repository](#output\_repository) | The ARN of the ECR (Elastic Container Registry) |
<!-- END_TF_DOCS -->