# ── S3 Data Lake Bucket ───────────────────────────────────────────────────────
resource "aws_s3_bucket" "nba_data_lake" {
  bucket = var.bucket_name

  tags = {
    Name        = "${var.project_name}-data-lake"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "nba_data_lake" {
  bucket = aws_s3_bucket.nba_data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning
resource "aws_s3_bucket_versioning" "nba_data_lake" {
  bucket = aws_s3_bucket.nba_data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Folder structure via placeholder objects
resource "aws_s3_object" "raw_prefix" {
  bucket  = aws_s3_bucket.nba_data_lake.id
  key     = "raw/"
  content = ""
}

resource "aws_s3_object" "processed_prefix" {
  bucket  = aws_s3_bucket.nba_data_lake.id
  key     = "processed/"
  content = ""
}

resource "aws_s3_object" "athena_results_prefix" {
  bucket  = aws_s3_bucket.nba_data_lake.id
  key     = "athena-results/"
  content = ""
}

# ── Athena Workgroup ──────────────────────────────────────────────────────────
resource "aws_athena_workgroup" "nba" {
  name = "${var.project_name}-workgroup"

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.nba_data_lake.bucket}/athena-results/"
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# ── Glue Database (used by Athena) ───────────────────────────────────────────
resource "aws_glue_catalog_database" "nba" {
  name        = var.athena_database
  description = "NBA Analytics data catalog"
}
