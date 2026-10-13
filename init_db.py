from database import crear_tablas
import models  # noqa: F401  (registra ArchivoDB y UserDB en Base.metadata)

crear_tablas()
print("✅ Tablas 'archivos' y 'users' creadas exitosamente")