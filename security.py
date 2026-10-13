from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    # gensalt() genera un salt aleatorio nuevo en cada llamada;
    # bcrypt lo guarda dentro del propio hash resultante
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    # checkpw lee el salt del hash guardado, vuelve a hashear y compara
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: int) -> str:
    # sub (subject) identifica al usuario; PyJWT exige que sea un string.
    # El payload solo está firmado, NO cifrado: cualquiera puede leerlo,
    # así que no se guarda nada sensible aquí.
    expira = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expira}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    # Verifica la firma y la expiración. Lanza jwt.ExpiredSignatureError si venció
    # y jwt.InvalidTokenError si la firma no coincide o el token está mal formado.
    # Siempre se indica la lista de algoritmos permitidos.
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
