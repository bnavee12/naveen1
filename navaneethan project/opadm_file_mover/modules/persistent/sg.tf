resource "aws_security_group" "fargate_egress_sg" {
  name                   = "${var.project}-fargate-sg"
  vpc_id                 = var.vpc_id
  revoke_rules_on_delete = true
}

resource "aws_security_group_rule" "fargate_security_group_rule_allow_https" {
  description       = "Allow TLS egress from VPC"
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.fargate_egress_sg.id
}

resource "aws_security_group_rule" "fargate_security_group_rule_allow_sftp" {
  description       = "Allow TLS egress from VPC"
  type              = "egress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.fargate_egress_sg.id
}