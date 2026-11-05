"""
scripts/test_s3.py — Amazon S3 Integration Connectivity Test Utility
Run with: python scripts/test_s3.py
"""
import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.services.s3_service import S3Service

app = create_app()

with app.app_context():
    print("=" * 60)
    print(" Amazon S3 Integration Verification")
    print("=" * 60)

    s3 = S3Service()
    bucket = app.config.get("S3_BUCKET_NAME")
    region = app.config.get("AWS_REGION")
    key_id = app.config.get("AWS_ACCESS_KEY_ID")

    print(f"Target Bucket : {bucket or '[NOT CONFIGURED]'}")
    print(f"AWS Region    : {region}")
    print(f"Auth Method   : {'Access Key + Secret (Local Dev)' if key_id else 'EC2 IAM Instance Profile / Environment'}")

    if not s3.is_configured():
        print("\n[NOTE] S3_BUCKET_NAME is not set in environment or .env.")
        print("       The application is operating in local fallback mode:")
        print("       Images will be saved to 'app/static/images/uploads/'.")
        print("\nTo activate Amazon S3:")
        print("1. Set S3_BUCKET_NAME=your-bucket in .env or EC2 environment.")
        print("2. Ensure EC2 IAM role has AmazonS3FullAccess (or equivalent bucket policy).")
    else:
        print("\nAttempting connection to Amazon S3...")
        test_key = "test/connectivity_check.txt"
        test_data = io.BytesIO(b"Amazon S3 Connectivity Verification for Student Management System")

        uploaded = s3.upload_file(test_data, test_key, content_type="text/plain")
        if uploaded:
            print(f"[SUCCESS] Test object uploaded to s3://{bucket}/{test_key}")
            url = s3.get_presigned_url(test_key, expiry=300)
            print(f"[SUCCESS] Presigned URL generated (expires in 5m):")
            print(f"          {url[:80]}...")

            deleted = s3.delete_file(test_key)
            if deleted:
                print(f"[SUCCESS] Cleaned up test object from S3.")
            print("\n[OK] Amazon S3 integration is fully operational.")
        else:
            print("[ERROR] Failed to communicate with S3. Verify bucket permissions and AWS credentials.")
    print("=" * 60)
