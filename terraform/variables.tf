variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for naming resources"
  type        = string
  default     = "nba-analytics"
}

variable "bucket_name" {
  description = "S3 bucket name for NBA data lake (must be globally unique)"
  type        = string
  default     = "nba-analytics-camron"
}

variable "athena_database" {
  description = "Glue/Athena database name"
  type        = string
  default     = "nba_analytics"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}
