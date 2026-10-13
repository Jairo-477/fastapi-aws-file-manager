from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import crear_tablas
import models  # noqa: F401  (registra ArchivoDB y UserDB en Base.metadata antes de crear_tablas)
from routers import archivos, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Se ejecuta al arrancar el servidor, no al importar el módulo
    crear_tablas()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(archivos.router)
app.include_router(auth.router)
