"""
importar_ventas_v3.py
----------------------
Simulación de conexión remota multi-sucursal hacia la Casa Matriz (Asunción).

Uso:
  - Prueba B (fallo didáctico): correr tal cual desde el Host de Codespaces.
    DB_CONFIG["host"] = "localhost"  -> Postgres rechazará la conexión porque
    llega enmascarada (NAT) con la IP del Gateway de Docker (172.18.0.1),
    y la regla de hardening del pg_hba.conf la bloquea con 'reject'.

  - Prueba C (solución): correr dentro del contenedor Python conectado a la
    red 'red_empresarial', y cambiar DB_CONFIG["host"] = "postgres-matriz".
    Al estar dentro de la red interna, la conexión llega con una IP del
    rango 172.18.0.0/16 y matchea la regla 'scram-sha-256' -> éxito.
"""

import sys
import time
import pandas as pd
import psycopg2

# ==============================================================================
# CONFIGURACIÓN DE CONEXIÓN A LA CASA MATRIZ
# ==============================================================================
DB_CONFIG = {
    "host": "postgres-matriz",  # <--- Prueba C: dentro de la red interna
    "port": "5432",
    "database": "matriz_db",
    "user": "ucom_admin",
    "password": "password_matriz",
}

CSV_PATH = "ventas_muestra.csv"

# Ciclo de sucursales legítimas del CPD (Casa Matriz vive en Asunción)
SUCURSALES = ["ASUNCION", "CDE", "ENC", "CORONEL_OVIEDO"]


def cargar_ventas(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return df


def conectar_matriz():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        connect_timeout=5,
    )


def insertar_venta(conn, row, sucursal: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ventas_locales
                (invoice_no, stock_code, description, quantity,
                 invoice_date, unit_price, customer_id, country,
                 sucursal)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(row["InvoiceNo"]),
                str(row["StockCode"]),
                str(row["Description"]),
                int(row["Quantity"]),
                row["InvoiceDate"],
                float(row["UnitPrice"]),
                str(row["CustomerID"]),
                str(row["Country"]),
                sucursal,
            ),
        )
    conn.commit()


def main():
    print("🚀 INICIANDO SIMULACIÓN DE CONEXIÓN REMOTA MULTI-SUCURSAL (CASA MATRIZ)...")
    print("=" * 90)

    df = cargar_ventas(CSV_PATH)
    print(f"📋 Cargados los primeros {len(df)} registros de ventas para la simulación.\n")

    for i, row in df.iterrows():
        sucursal = SUCURSALES[i % len(SUCURSALES)]
        print(f"[CONEXIÓN REMOTA: SUCURSAL_{sucursal} ➔ CASA MATRIZ]")
        print(
            f"   ↳ Detalles: Factura: {row['InvoiceNo']} | Item: {row['Description']} "
            f"| Cantidad: {row['Quantity']} | Precio: L {row['UnitPrice']}"
        )
        print(f"   🔌 Conectándose remotamente al puerto {DB_CONFIG['port']} de la Casa Matriz...")

        try:
            conn = conectar_matriz()
            insertar_venta(conn, row, sucursal)
            conn.close()
            print("   ✅ [ÉXITO] Registro asentado correctamente en la tabla centralizada de Asunción.")
            print("-" * 92)
        except psycopg2.OperationalError as e:
            print(f"   ❌ [FALLO] No se pudo asentar la transacción de Sucursal_{sucursal}.")
            print(f"      Detalle técnico: {str(e).strip()}")
            print("-" * 92)
            print(
                "\n💡 Este fallo es esperado si estás corriendo el script desde el Host "
                "(localhost) contra un pg_hba.conf endurecido. Revisá la guía, Prueba C, "
                "para correrlo dentro de la red interna del CPD.\n"
            )
            sys.exit(1)

    print("\n🏁 Simulación finalizada: todos los registros fueron asentados con éxito.")


if __name__ == "__main__":
    main()