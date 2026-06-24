output "s3_bucket_name" {
  description = "Name of the S3 data lake bucket"
  value       = aws_s3_bucket.nba_data_lake.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 data lake bucket"
  value       = aws_s3_bucket.nba_data_lake.arn
}

output "lambda_function_name" {
  description = "Name of the ingestion Lambda function"
  value       = aws_lambda_function.nba_ingestion.function_name
}

output "lambda_function_arn" {
  description = "ARN of the ingestion Lambda function"
  value       = aws_lambda_function.nba_ingestion.arn
}

output "glue_database_name" {
  description = "Glue catalog database name"
  value       = aws_glue_catalog_database.nba.name
}

output "athena_workgroup" {
  description = "Athena workgroup name"
  value       = aws_athena_workgroup.nba.name
}

output "athena_results_location" {
  description = "S3 path for Athena query results"
  value       = "s3://${aws_s3_bucket.nba_data_lake.bucket}/athena-results/"
}
