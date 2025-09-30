from scripts.configurar_vanna_local import my_vanna as vn

vn.connect_to_postgres(
    host='localhost',
    dbname='cfo_inteligente',
    user='cfo_user',
    password='cfo_pass',
    port=5432
)

# DDL principal
vn.train(ddl="""
CREATE TABLE operaciones (
    id UUID PRIMARY KEY,
    tipo_operacion VARCHAR(20),
    fecha DATE,
    monto_original NUMERIC(15,2),
    moneda_original VARCHAR(3),
    tipo_cambio NUMERIC(10,4),
    monto_usd NUMERIC(15,2),
    monto_uyu NUMERIC(15,2),
    deleted_at TIMESTAMP
);
""")

# Entrenar pregunta específica
vn.train(
    question="¿Cuánto hemos facturado hasta la fecha?",
    sql="SELECT SUM(monto_usd) as total_facturado_usd FROM operaciones WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL"
)

# Más ejemplos para que aprenda mejor
vn.train(
    question="¿Cuáles son los ingresos totales?",
    sql="SELECT SUM(monto_usd) FROM operaciones WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL"
)

vn.train(
    question="¿Cuánto facturamos?",
    sql="SELECT SUM(monto_usd) FROM operaciones WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL"
)

vn.train(
    question="Total de ventas",
    sql="SELECT SUM(monto_usd) FROM operaciones WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL"
)

print("Entrenamiento completado")
