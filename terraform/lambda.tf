# ── IAM Role for Lambda ───────────────────────────────────────────────────────
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Attach basic Lambda execution policy (CloudWatch logs)
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Inline policy: allow Lambda to read/write S3
resource "aws_iam_role_policy" "lambda_s3_access" {
  name = "${var.project_name}-lambda-s3-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ]
      Resource = [
        aws_s3_bucket.nba_data_lake.arn,
        "${aws_s3_bucket.nba_data_lake.arn}/*"
      ]
    }]
  })
}

# ── Lambda Function ───────────────────────────────────────────────────────────
resource "aws_lambda_function" "nba_ingestion" {
  function_name = "${var.project_name}-ingestion"
  role          = aws_iam_role.lambda_exec.arn
  runtime       = "python3.11"
  handler       = "lambda_handler.handler"
  timeout       = 300  # 5 minutes — nba_api calls can be slow
  memory_size   = 512

  # Placeholder — GitHub Actions deploys the real zip
  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  environment {
    variables = {
      S3_BUCKET_NAME = var.bucket_name
      AWS_REGION     = var.aws_region
      SEASON         = "2024-25"
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_basic]
}

# ── EventBridge (CloudWatch Events) — daily trigger ──────────────────────────
resource "aws_cloudwatch_event_rule" "daily_ingestion" {
  name                = "${var.project_name}-daily-trigger"
  description         = "Trigger NBA data ingestion every day at 6 AM UTC"
  schedule_expression = "cron(0 6 * * ? *)"

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_ingestion.name
  target_id = "NBAIngestionLambda"
  arn       = aws_lambda_function.nba_ingestion.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.nba_ingestion.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_ingestion.arn
}
