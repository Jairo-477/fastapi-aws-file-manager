import secrets

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config import INVITE_CODE
from database import get_db
from models import UserDB
from schemas import UserCreate, UserOut, Token
from security import hash_password, verify_password, create_access_token

router = APIRouter(tags=["auth"])

# Hash de una contraseña inexistente: se usa en el login cuando el email no existe,
# para que verificar siempre cueste lo mismo y no se note por tiempo de respuesta
_HASH_FALSO = hash_password("contraseña-que-nadie-usa")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def registrar_usuario(datos: UserCreate, db: Session = Depends(get_db)):
    # compare_digest compara en tiempo constante (un == se corta en el primer carácter
    # distinto y permitiría adivinar el código midiendo tiempos de respuesta)
    codigo_ok = secrets.compare_digest(
        datos.invite_code.encode("utf-8"), INVITE_CODE.encode("utf-8")
    )
    # Se revisa ANTES que el email duplicado: así quien no tiene el código
    # no puede averiguar qué emails existen mirando si recibe 409 o 403
    if not codigo_ok:
        raise HTTPException(status_code=403, detail="Código de invitación inválido")

    existente = db.query(UserDB).filter(UserDB.email == datos.email).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")

    nuevo_usuario = UserDB(
        email=datos.email,
        hashed_password=hash_password(datos.password),
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario


# OAuth2PasswordRequestForm recibe form-data con los campos "username" y "password";
# aquí "username" contiene el email
@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(UserDB).filter(UserDB.email == form.username).first()

    hash_a_verificar = usuario.hashed_password if usuario else _HASH_FALSO
    password_ok = verify_password(form.password, hash_a_verificar)

    # Mismo mensaje para email inexistente y contraseña incorrecta
    if not usuario or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(usuario.id), token_type="bearer")
