from io import BytesIO
import boto3
import os

R2_ENDPOINT  = os.getenv("R2_ENDPOINT")
R2_ACCESS_ID = os.getenv("R2_ACCESS_ID")
R2_SECRET    = os.getenv("R2_SECRET")
R2_BUCKET    = os.getenv("R2_BUCKET")

DOMAIN_BASE  = os.getenv("DOMAIN_BASE")

def _upload_img(img, key: str, s3_client, bucket: str, domain_base: str, cache: bool) -> str:
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    if cache:
        s3_client.upload_fileobj(buffer, bucket, key, ExtraArgs={"ContentType": "image/png"})
    else:
        s3_client.upload_fileobj(buffer, bucket, key, ExtraArgs={"ContentType": "image/png", "CacheControl": "no-cache"})
    return f"{domain_base}/{key}"

def uploadImg(img, key: str, cache: bool = False) -> str:
    s3 = boto3.client(
        service_name="s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_ID,
        aws_secret_access_key=R2_SECRET,
        region_name="auto"
    )
    return _upload_img(img, key, s3, R2_BUCKET, DOMAIN_BASE, cache)

def getURL(key: str) -> str:
    return f"{DOMAIN_BASE}/{key}"