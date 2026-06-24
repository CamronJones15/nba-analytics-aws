"""
create_placeholder.py
Run this once before terraform apply to create the required placeholder zip.
Place this file in the terraform/ directory and run it from there.
"""
import zipfile
import os
 
placeholder_code = b"def handler(event, context): return {'statusCode': 200}"
 
zip_path = os.path.join(os.path.dirname(__file__), "lambda_placeholder.zip")
 
with zipfile.ZipFile(zip_path, "w") as zf:
    zf.writestr("lambda_handler.py", placeholder_code)
 
print(f"Created {zip_path}")
 