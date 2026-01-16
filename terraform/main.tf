# Terraform AWS Configuration for DocPilot

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  default = "us-east-1"
}

variable "project_name" {
  default = "docpilot"
}

variable "db_password" {
  description = "Password for RDS PostgreSQL"
  sensitive   = true
}

variable "embedding_api_url" {
  description = "Modal embedding API URL (e.g., https://USERNAME--docpilot-embedder-model-embedding-webhook.modal.run)"
}
