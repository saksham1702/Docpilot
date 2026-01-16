# ECR Repository for Docker Images

resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = {
    Name = "${var.project_name}-backend"
  }
}

# Output ECR URL
output "ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}
