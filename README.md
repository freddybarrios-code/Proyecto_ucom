# Laboratorio (UCOM)

Estructura de archivos requerida por la rúbrica (Ítem 1, 4 Ptos):

```
proyecto-cpd/
├── compose.yaml
├── ddl-v3.sql
├── importar_ventas_v3.py
└── ventas_muestra.csv
```

Subí estos 4 archivos a la raíz de tu repositorio público de GitHub y abrilo en
**Codespaces**. Seguí los pasos en orden; cada paso indica qué ítem de la
rúbrica satisface.

---

## Paso 0 — Requisitos previos
```bash
pip install pandas psycopg2-binary --break-system-packages
```

## Paso 1 — Levantar la infraestructura (Ítem 2, 4 Ptos)
```bash
docker compose up -d
docker compose ps
```
Deben verse los **4 nodos Postgres** (`cpd-matriz-db`, `cpd-cde-db`,
`cpd-enc-db`, `cpd-cnel-db`) en estado `Up` — Ítem 3 (3 Ptos).

## Paso 2 — Inicializar la tabla en la Matriz (Ítem 4, 3 Ptos)
```bash
docker exec -i cpd-matriz-db psql -U ucom_admin -d matriz_db < ddl-v3.sql
```

## Paso 3 — Editar `pg_hba.conf` (hardening)
```bash
docker cp cpd-matriz-db:/var/lib/postgresql/data/pg_hba.conf ./pg_hba.conf
```
1. Abrí `./pg_hba.conf` en VS Code.
2. Comentá con `#` la línea abierta original:
   `host    all             all             all                     scram-sha-256`
3. Pegá al final el contenido de `pg_hba-reglas-perimetrales.conf` (incluido en este repo).
4. Guardá (`Ctrl+S`).

## Paso 4 — Reinyectar el archivo y corregir permisos
```bash
docker cp ./pg_hba.conf cpd-matriz-db:/var/lib/postgresql/data/pg_hba.conf
docker exec -u root cpd-matriz-db chown postgres:postgres /var/lib/postgresql/data/pg_hba.conf
docker exec -u root cpd-matriz-db chmod 600 /var/lib/postgresql/data/pg_hba.conf
```

## Paso 5 — Recargar la configuración en caliente
```bash
docker exec -it cpd-matriz-db psql -U ucom_admin -d matriz_db -c "SELECT pg_reload_conf();"
```

## Paso 6 — Auditar las reglas activas (Ítem 5, 1 Pto)
```bash
docker exec -it cpd-matriz-db psql -U ucom_admin -d matriz_db -c \
  "SELECT line_number, type, database, user_name, address, auth_method, error FROM pg_hba_file_rules;"
```
La columna `error` debe estar **vacía** en todas las filas.

## Paso 7 — Prueba A: ataque perimetral externo bloqueado (Ítem 7, 1 Pto)
```bash
docker run --rm -it --add-host=host.docker.internal:host-gateway \
  postgres:15-alpine psql -h host.docker.internal -p 5432 -U ucom_admin -d matriz_db
```
Debe fallar con `pg_hba.conf rejects connection for host "172.18.0.1"...`.

## Paso 8 — Prueba B: fallo didáctico del script desde el Host (Ítem 6, 1 Pto)
Con `DB_CONFIG["host"] = "localhost"` en `importar_ventas_v3.py`:
```bash
python3 importar_ventas_v3.py
```
Debe fallar por la misma razón (NAT + regla `reject`).

## Paso 9 — Prueba C: solución definitiva dentro de la red segura (Ítem 8, 2 Ptos)
1. En `importar_ventas_v3.py`, cambiá `"host": "localhost"` por `"host": "postgres-matriz"`.
2. Corré el simulador dentro de la red `red_empresarial`:
```bash
docker run --rm -it --network proyecto-cpd_red_empresarial \
  -v "$PWD":/usr/src/app -w /usr/src/app python:3.10-slim \
  sh -c "pip install pandas psycopg2-binary && python importar_ventas_v3.py"
```
> Si la red no existe con ese nombre exacto, listá las redes con
> `docker network ls` y ajustá `--network` (puede ser `proyecto_red_empresarial`
> dependiendo del nombre de la carpeta del proyecto).

## Paso 10 — Validar la consistencia de datos en Asunción
```bash
docker exec -it cpd-matriz-db psql -U ucom_admin -d matriz_db -c \
  "SELECT id, invoice_no, quantity, sucursal, insertado_en FROM ventas_locales ORDER BY id;"
```

## Paso 11 — Liberar recursos
```bash
docker compose down
```

---

## Mapa rúbrica → evidencia

| Ítem | Evidencia | Puntaje |
|---|---|---|
| 1 | Repo con `compose.yaml`, `ddl-v3.sql`, `importar_ventas_v3.py`, `ventas_muestra.csv` | 4 |
| 2 | `docker compose up -d` → red + volúmenes + 4 contenedores | 4 |
| 3 | `docker compose ps` con los 4 nodos `Up` | 3 |
| 4 | `ventas_locales` creada vía `docker exec -i ... < ddl-v3.sql` | 3 |
| 5 | `importar_ventas_v3.py` corriendo con éxito dentro de la red | 3 |
| 6 | Consulta SQL final mostrando las ventas asentadas | 3 |
| **Total** | | **20** |
