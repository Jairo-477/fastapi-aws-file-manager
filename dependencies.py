import boto3
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models import UserDB
from security import decode_access_token


def get_s3_client():
    return boto3.client("s3")


# tokenUrl indica a /docs a qué endpoint ir para obtener el token (botón Authorize);
# en cada petición extrae el valor del header "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserDB:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credenciales_invalidas

    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise credenciales_invalidas

    usuario = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not usuario:
        # El token es válido pero el usuario ya no existe
        raise credenciales_invalidas

    return usuario
