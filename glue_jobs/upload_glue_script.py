"""
upload_glue_script.py
Run this once to upload the Glue ETL script to S3 so Terraform can reference it.
Run from the project root: python glue_jobs/upload_glue_script.py
"""

import boto3
import os
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "nba-analytics-camron")
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "transform_stats.py")
S3_KEY = "glue_scripts/transform_stats.py"

s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))

print(f"Uploading {SCRIPT_PATH} to s3://{S3_BUCKET}/{S3_KEY} ...")
s3.upload_file(SCRIPT_PATH, S3_BUCKET, S3_KEY)
print("Done! Glue script uploaded successfully.")