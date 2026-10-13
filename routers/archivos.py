from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError
import uuid
import os

from database import get_db
from models import ArchivoDB
from schemas import Archivo
from dependencies import get_s3_client, get_current_user
from config import BUCKET_NAME

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "API funcionando"}


@router.get("/archivos", response_model=list[Archivo], dependencies=[Depends(get_current_user)])
def listar_archivos(db: Session = Depends(get_db)):
    return db.query(ArchivoDB).all()


@router.get("/archivos/{archivo_id}", response_model=Archivo, dependencies=[Depends(get_current_user)])
def obtener_archivo(archivo_id: int, db: Session = Depends(get_db)):
    archivo = db.query(ArchivoDB).filter(ArchivoDB.id == archivo_id).first()
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return archivo


@router.delete("/archivos/{archivo_id}", dependencies=[Depends(get_current_user)])
def eliminar_archivo(archivo_id: int, db: Session = Depends(get_db), s3=Depends(get_s3_client)):
    archivo = db.query(ArchivoDB).filter(ArchivoDB.id == archivo_id).first()
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=archivo.s3_key)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando de S3: {e}")

    db.delete(archivo)
    db.commit()
    return {"detail": "Archivo eliminado de S3 y de la base de datos"}


@router.post("/upload", response_model=Archivo, dependencies=[Depends(get_current_user)])
def subir_archivo(file: UploadFile = File(...), db: Session = Depends(get_db), s3=Depends(get_s3_client)):
    file.file.seek(0, 2)
    tamano_bytes = file.file.tell()
    tamano_kb = round(tamano_bytes / 1024, 2)
    file.file.seek(0)

    extension = os.path.splitext(file.filename)[1]
    s3_key = f"{uuid.uuid4()}{extension}"

    try:
        s3.upload_fileobj(file.file, BUCKET_NAME, s3_key)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo a S3: {e}")

    nuevo_archivo = ArchivoDB(
        nombre=file.filename,
        s3_key=s3_key,
        tipo=file.content_type,
        tamano_kb=tamano_kb,
    )
    db.add(nuevo_archivo)
    db.commit()
    db.refresh(nuevo_archivo)

    return nuevo_archivo


@router.get("/archivos/{archivo_id}/download", dependencies=[Depends(get_current_user)])
def obtener_url_descarga(archivo_id: int, db: Session = Depends(get_db), s3=Depends(get_s3_client)):
    archivo = db.query(ArchivoDB).filter(ArchivoDB.id == archivo_id).first()
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": archivo.s3_key},
            ExpiresIn=300,
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error generando URL: {e}")

    return {"download_url": url, "expira_en_segundos": 300}
