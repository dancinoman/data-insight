import boto3

try:
    s3 = boto3.client('s3')
    # Try to list buckets to verify credentials work
    print(s3.list_buckets())
except Exception as e:
    print("Error:", e)
