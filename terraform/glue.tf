# ── IAM Role for Glue ────────────────────────────────────────────────────────
resource "aws_iam_role" "glue_role" {
  name = "${var.project_name}-glue-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
    }]
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3_access" {
  name = "${var.project_name}-glue-s3-policy"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ]
      Resource = [
        aws_s3_bucket.nba_data_lake.arn,
        "${aws_s3_bucket.nba_data_lake.arn}/*"
      ]
    }]
  })
}

# ── Glue Crawlers ─────────────────────────────────────────────────────────────
resource "aws_glue_crawler" "raw_player_stats" {
  name          = "${var.project_name}-raw-player-stats"
  role          = aws_iam_role.glue_role.arn
  database_name = aws_glue_catalog_database.nba.name

  s3_target {
    path = "s3://${var.bucket_name}/raw/player_stats/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_glue_crawler" "raw_team_standings" {
  name          = "${var.project_name}-raw-team-standings"
  role          = aws_iam_role.glue_role.arn
  database_name = aws_glue_catalog_database.nba.name

  s3_target {
    path = "s3://${var.bucket_name}/raw/team_standings/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_glue_crawler" "processed_data" {
  name          = "${var.project_name}-processed-data"
  role          = aws_iam_role.glue_role.arn
  database_name = aws_glue_catalog_database.nba.name

  s3_target {
    path = "s3://${var.bucket_name}/processed/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# ── Glue ETL Job ──────────────────────────────────────────────────────────────
resource "aws_glue_job" "transform_stats" {
  name     = "${var.project_name}-transform-stats"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.bucket_name}/glue_scripts/transform_stats.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"        = "python"
    "--S3_BUCKET"           = var.bucket_name
    "--DATABASE_NAME"       = var.athena_database
    "--extra-py-files"      = ""
    "--enable-metrics"      = "true"
    "--enable-job-insights" = "true"
  }

  glue_version      = "4.0"
  number_of_workers = 2
  worker_type       = "G.1X"
  timeout           = 60

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}
