from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Modelo Pydantic (para la API) ---
class Archivo(BaseModel):
    # from_attributes permite convertir un ArchivoDB a este modelo
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    s3_key: str
    tipo: str
    tamano_kb: float


# --- Usuarios y autenticación ---
# Entrada (lo que envía el cliente): incluye la contraseña en texto plano
class UserCreate(BaseModel):
    email: EmailStr
    # bcrypt solo usa los primeros 72 bytes; por eso el máximo
    password: str = Field(min_length=8, max_length=72)
    # Código compartido que se entrega a quien se quiere dejar registrar (ver /register)
    invite_code: str


# Salida (lo que devuelve la API): NUNCA incluye password ni hashed_password
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str
