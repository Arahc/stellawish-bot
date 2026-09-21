from io import BytesIO
import asyncio
import boto3
import os
from functools import lru_cache

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

@lru_cache(maxsize=1)
def _get_s3_client():
    return boto3.client(
        service_name="s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_ID,
        aws_secret_access_key=R2_SECRET,
        region_name="auto"
    )
def uploadImg(img, key: str, cache: bool = False) -> str:
    return _upload_img(img, key, _get_s3_client(), R2_BUCKET, DOMAIN_BASE, cache)


async def uploadImgAsync(img, key: str, cache: bool = False, timeout: float = 15) -> str:
    """Run the blocking S3 upload away from NoneBot's event loop."""
    return await asyncio.wait_for(
        asyncio.to_thread(uploadImg, img, key, cache),
        timeout=timeout,
    )

def getURL(key: str) -> str:
    return f"{DOMAIN_BASE}/{key}"
