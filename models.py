from sqlalchemy import Column, Integer, String, Float
from database import Base

class ArchivoDB(Base):
    __tablename__ = "archivos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    s3_key = Column(String, nullable=False, unique=True)
    tipo = Column(String, nullable=False)
    tamano_kb = Column(Float, nullable=False)


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True, index=True)
    # Solo se guarda el hash de bcrypt, nunca la contraseña en texto plano
    hashed_password = Column(String, nullable=False)