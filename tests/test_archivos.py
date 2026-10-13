# Los endpoints de archivos usan una base SQLite en memoria y un S3 falso (ver conftest.py)

ENDPOINTS_PROTEGIDOS = [
    ("get", "/archivos"),
    ("get", "/archivos/1"),
    ("get", "/archivos/1/download"),
    ("delete", "/archivos/1"),
    ("post", "/upload"),
]


def test_healthcheck_es_publico(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_endpoints_de_archivos_sin_token_dan_401(client):
    for metodo, ruta in ENDPOINTS_PROTEGIDOS:
        resp = getattr(client, metodo)(ruta)
        assert resp.status_code == 401, f"{metodo.upper()} {ruta} debería exigir token"


def test_endpoints_con_token_malformado_dan_401(client):
    for metodo, ruta in ENDPOINTS_PROTEGIDOS:
        resp = getattr(client, metodo)(ruta, headers={"Authorization": "Bearer abc.def.ghi"})
        assert resp.status_code == 401, f"{metodo.upper()} {ruta} debería rechazar un token inválido"


def test_flujo_completo_con_token(client, auth_headers):
    subida = client.post(
        "/upload",
        files={"file": ("hola.txt", b"contenido de prueba", "text/plain")},
        headers=auth_headers,
    )
    assert subida.status_code == 200
    archivo = subida.json()
    assert archivo["nombre"] == "hola.txt"
    assert archivo["tipo"] == "text/plain"

    listado = client.get("/archivos", headers=auth_headers)
    assert listado.status_code == 200
    assert [a["id"] for a in listado.json()] == [archivo["id"]]

    detalle = client.get(f"/archivos/{archivo['id']}", headers=auth_headers)
    assert detalle.status_code == 200

    descarga = client.get(f"/archivos/{archivo['id']}/download", headers=auth_headers)
    assert descarga.status_code == 200
    assert descarga.json()["download_url"].startswith("https://")

    borrado = client.delete(f"/archivos/{archivo['id']}", headers=auth_headers)
    assert borrado.status_code == 200

    assert client.get(f"/archivos/{archivo['id']}", headers=auth_headers).status_code == 404


def test_archivo_inexistente_da_404_con_token(client, auth_headers):
    assert client.get("/archivos/999", headers=auth_headers).status_code == 404
    assert client.delete("/archivos/999", headers=auth_headers).status_code == 404
