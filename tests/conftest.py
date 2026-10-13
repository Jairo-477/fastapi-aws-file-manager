import os

# Valores falsos solo para los tests; deben fijarse ANTES de importar la app,
# porque config.py los lee al importarse. Forzar SECRET_KEY evita usar la del .env.
os.environ["SECRET_KEY"] = "clave-solo-para-tests-0123456789-abcdef"
os.environ["INVITE_CODE"] = "codigo-de-invitacion-de-tests"
os.environ.setdefault("S3_BUCKET_NAME", "bucket-de-pruebas")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from dependencies import get_s3_client
import models  # noqa: F401  (registra las tablas en Base.metadata)
from main import app


class FakeS3:
    """Reemplaza a boto3: no toca AWS. Guarda en memoria lo que se "sube"."""

    def __init__(self):
        self.objetos = {}

    def upload_fileobj(self, fileobj, bucket, key):
        self.objetos[key] = fileobj.read()

    def delete_object(self, Bucket, Key):
        self.objetos.pop(Key, None)

    def generate_presigned_url(self, operacion, Params, ExpiresIn):
        return f"https://fake-s3/{Params['Key']}"


@pytest.fixture()
def session_factory():
    # SQLite en memoria (nueva en cada test): no se toca la base de datos real (RDS)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    engine.dispose()


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_s3_client] = lambda: FakeS3()

    # Sin "with": no se ejecuta el lifespan (que haría crear_tablas() en RDS)
    yield TestClient(app)

    app.dependency_overrides.clear()


EMAIL = "test@example.com"
PASSWORD = "clave12345"


@pytest.fixture()
def usuario(client):
    resp = client.post(
        "/register",
        json={"email": EMAIL, "password": PASSWORD, "invite_code": os.environ["INVITE_CODE"]},
    )
    assert resp.status_code == 201
    return {"email": EMAIL, "password": PASSWORD}


@pytest.fixture()
def auth_headers(client, usuario):
    resp = client.post("/login", data={"username": usuario["email"], "password": usuario["password"]})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
