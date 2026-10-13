from datetime import datetime, timedelta, timezone

import jwt

from config import SECRET_KEY, ALGORITHM, INVITE_CODE
from models import UserDB
from security import hash_password, verify_password


# --- Hashing ---
def test_hash_no_es_la_contrasena_y_se_verifica():
    h = hash_password("clave12345")
    assert h != "clave12345"
    assert verify_password("clave12345", h)
    assert not verify_password("otra-clave", h)


def test_mismo_password_da_hashes_distintos_por_el_salt():
    assert hash_password("clave12345") != hash_password("clave12345")


# --- /register ---
def test_register_ok_y_no_expone_password(client):
    resp = client.post("/register", json={"email": "a@example.com", "password": "clave12345", "invite_code": INVITE_CODE})
    assert resp.status_code == 201
    cuerpo = resp.json()
    assert cuerpo["email"] == "a@example.com"
    assert "id" in cuerpo
    assert "password" not in cuerpo
    assert "hashed_password" not in cuerpo


def test_register_email_duplicado_da_409(client, usuario):
    resp = client.post("/register", json={"email": usuario["email"], "password": "otraclave123", "invite_code": INVITE_CODE})
    assert resp.status_code == 409


def test_register_validaciones_dan_422(client):
    assert client.post("/register", json={"email": "no-es-email", "password": "clave12345", "invite_code": INVITE_CODE}).status_code == 422
    assert client.post("/register", json={"email": "a@example.com", "password": "corta", "invite_code": INVITE_CODE}).status_code == 422
    assert client.post("/register", json={"email": "a@example.com", "password": "x" * 73, "invite_code": INVITE_CODE}).status_code == 422


def test_register_sin_codigo_da_422(client):
    resp = client.post("/register", json={"email": "a@example.com", "password": "clave12345"})
    assert resp.status_code == 422


def test_register_con_codigo_incorrecto_da_403_y_no_crea_usuario(client, session_factory):
    resp = client.post(
        "/register",
        json={"email": "a@example.com", "password": "clave12345", "invite_code": "codigo-equivocado"},
    )
    assert resp.status_code == 403
    db = session_factory()
    assert db.query(UserDB).count() == 0
    db.close()


def test_codigo_incorrecto_no_revela_si_el_email_existe(client, usuario):
    # Con email ya registrado y código malo debe dar 403 (no 409)
    resp = client.post(
        "/register",
        json={"email": usuario["email"], "password": "clave12345", "invite_code": "codigo-equivocado"},
    )
    assert resp.status_code == 403


# --- /login ---
def test_login_ok_devuelve_token(client, usuario):
    resp = client.post("/login", data={"username": usuario["email"], "password": usuario["password"]})
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["token_type"] == "bearer"
    payload = jwt.decode(cuerpo["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert set(payload) == {"sub", "exp"}  # nada sensible en el payload


def test_login_error_es_generico_para_email_y_password(client, usuario):
    password_mala = client.post("/login", data={"username": usuario["email"], "password": "incorrecta1"})
    email_inexistente = client.post("/login", data={"username": "nadie@example.com", "password": "clave12345"})
    assert password_mala.status_code == 401
    assert email_inexistente.status_code == 401
    assert password_mala.json() == email_inexistente.json()


def test_password_se_guarda_hasheada(session_factory, usuario):
    db = session_factory()
    fila = db.query(UserDB).filter(UserDB.email == usuario["email"]).first()
    assert fila.hashed_password != usuario["password"]
    assert fila.hashed_password.startswith("$2b$")
    db.close()


# --- get_current_user (probado a través de un endpoint protegido) ---
def test_token_expirado_da_401(client, usuario):
    vencido = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    resp = client.get("/archivos", headers={"Authorization": f"Bearer {vencido}"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token expirado"


def test_token_con_firma_incorrecta_da_401(client, usuario):
    falso = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "otra-clave-distinta-para-firmar-1234567",
        algorithm=ALGORITHM,
    )
    resp = client.get("/archivos", headers={"Authorization": f"Bearer {falso}"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token inválido"


def test_token_valido_de_usuario_inexistente_da_401(client):
    token = jwt.encode(
        {"sub": "999", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    resp = client.get("/archivos", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
