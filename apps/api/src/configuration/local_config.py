import os
from dotenv import load_dotenv

load_dotenv()

FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1")
SECRET_KEY = os.getenv("SECRET_KEY", "")

POSTGRES_DB = os.getenv("POSTGRES_DB", "digisutra")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB_PORT = os.getenv("POSTGRES_DB_PORT", "5432")
POSTGRES_DB_URI = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_DB_PORT}/{POSTGRES_DB}"
)

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
RAZORPAY_TEST_KEY_ID = os.getenv("RAZORPAY_TEST_KEY_ID", "")
RAZORPAY_TEST_KEY_SECRET = os.getenv("RAZORPAY_TEST_KEY_SECRET", "")
RAZORPAY_TEST_WEBHOOK_SECRET = os.getenv("RAZORPAY_TEST_WEBHOOK_SECRET", "")
RAZORPAY_LIVE_KEY_ID = os.getenv("RAZORPAY_LIVE_KEY_ID", "")
RAZORPAY_LIVE_KEY_SECRET = os.getenv("RAZORPAY_LIVE_KEY_SECRET", "")
RAZORPAY_LIVE_WEBHOOK_SECRET = os.getenv("RAZORPAY_LIVE_WEBHOOK_SECRET", "")
RAZORPAY_CURRENCY = os.getenv("RAZORPAY_CURRENCY", "INR")

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "")
AWS_CLOUDFRONT_DOMAIN = os.getenv("AWS_CLOUDFRONT_DOMAIN", "")
AWS_S3_PRESIGN_EXPIRES_IN = os.getenv("AWS_S3_PRESIGN_EXPIRES_IN", "900")
AWS_S3_GET_PRESIGN_EXPIRES_IN = os.getenv("AWS_S3_GET_PRESIGN_EXPIRES_IN", "900")
AWS_S3_UPLOAD_PREFIX = os.getenv("AWS_S3_UPLOAD_PREFIX", "products")

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:3000")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", APP_BASE_URL)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
AUTH_EDDSA_PRIVATE_KEY_PEM = os.getenv("AUTH_EDDSA_PRIVATE_KEY_PEM", "").replace("\\n", "\n")
AUTH_EDDSA_PUBLIC_KEY_PEM = os.getenv("AUTH_EDDSA_PUBLIC_KEY_PEM", "").replace("\\n", "\n")
ASSET_ACCESS_MAX_DOWNLOADS = os.getenv("ASSET_ACCESS_MAX_DOWNLOADS", "3")
ASSET_ACCESS_EXPIRES_IN_DAYS = os.getenv("ASSET_ACCESS_EXPIRES_IN_DAYS", "30")
ASSET_DELIVERY_TOKEN_TTL_SECONDS = os.getenv("ASSET_DELIVERY_TOKEN_TTL_SECONDS", "900")
PAYMENT_MODE = os.getenv("PAYMENT_MODE", "test")
PLATFORM_FEE_PERCENT = os.getenv("PLATFORM_FEE_PERCENT", "10")


def _build_postgres_db_uri():
    configured_uri = os.getenv("POSTGRES_DB_URI")
    if configured_uri:
        return configured_uri

    db_name = os.getenv("POSTGRES_DB", POSTGRES_DB)
    db_user = os.getenv("POSTGRES_USER", POSTGRES_USER)
    db_password = os.getenv("POSTGRES_PASSWORD", POSTGRES_PASSWORD)
    db_host = os.getenv("POSTGRES_HOST", POSTGRES_HOST)
    db_port = os.getenv("POSTGRES_DB_PORT", POSTGRES_DB_PORT)
    ssl_mode = os.getenv("POSTGRES_SSLMODE", "")

    from urllib.parse import quote_plus

    auth_user = quote_plus(db_user)
    auth_password = quote_plus(db_password)
    query = f"?sslmode={quote_plus(ssl_mode)}" if ssl_mode else ""
    return (
        f"postgresql+psycopg2://{auth_user}:{auth_password}"
        f"@{db_host}:{db_port}/{db_name}{query}"
    )


POSTGRES_DB_URI = _build_postgres_db_uri()
