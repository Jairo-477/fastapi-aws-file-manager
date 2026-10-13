import os
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
if not BUCKET_NAME:
    raise RuntimeError("Falta la variable de entorno S3_BUCKET_NAME en el .env")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "Falta la variable de entorno SECRET_KEY en el .env "
        '(genérala con: python -c "import secrets; print(secrets.token_hex(32))")'
    )

INVITE_CODE = os.getenv("INVITE_CODE")
if not INVITE_CODE:
    raise RuntimeError(
        "Falta la variable de entorno INVITE_CODE en el .env "
        '(genérala con: python -c "import secrets; print(secrets.token_urlsafe(16))")'
    )

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
