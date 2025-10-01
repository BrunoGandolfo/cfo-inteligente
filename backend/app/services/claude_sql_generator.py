"""
Generador de SQL usando Claude Sonnet 4.5 como modelo principal
Mayor precisión y determinismo que GPT-3.5
"""

import anthropic
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class ClaudeSQLGenerator:
    """
    Usa Claude Sonnet 4.5 para generar SQL directamente
    Más preciso y determinístico que Vanna+GPT-3.5
    """
    
    DDL_CONTEXT = """
CREATE TABLE operaciones (
    id UUID PRIMARY KEY,
    tipo_operacion VARCHAR(20) NOT NULL CHECK (tipo_operacion IN ('INGRESO', 'GASTO', 'RETIRO', 'DISTRIBUCION')),
    fecha DATE NOT NULL,
    monto_original NUMERIC(15,2) NOT NULL,
    moneda_original VARCHAR(3) NOT NULL CHECK (moneda_original IN ('UYU', 'USD')),
    tipo_cambio NUMERIC(10,4) NOT NULL,
    monto_usd NUMERIC(15,2) NOT NULL,
    monto_uyu NUMERIC(15,2) NOT NULL,
    area_id UUID NOT NULL REFERENCES areas(id),
    localidad VARCHAR(50) NOT NULL CHECK (localidad IN ('MONTEVIDEO', 'MERCEDES')),
    descripcion VARCHAR(500),
    cliente VARCHAR(200),
    proveedor VARCHAR(200),
    deleted_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE distribuciones_detalle (
    id UUID PRIMARY KEY,
    operacion_id UUID REFERENCES operaciones(id),
    socio_id UUID REFERENCES socios(id),
    monto_uyu NUMERIC(15,2),
    monto_usd NUMERIC(15,2),
    porcentaje NUMERIC(5,2)
);

CREATE TABLE socios (
    id UUID PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL CHECK (nombre IN ('Agustina', 'Viviana', 'Gonzalo', 'Pancho', 'Bruno')),
    porcentaje_participacion NUMERIC(5,2) NOT NULL
);

CREATE TABLE areas (
    id UUID PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL CHECK (nombre IN ('Jurídica', 'Notarial', 'Contable', 'Recuperación', 'Gastos Generales', 'Otros'))
);
"""
    
    BUSINESS_CONTEXT = """
CONTEXTO DEL NEGOCIO - CONEXIÓN CONSULTORA:
• Consultora uruguaya con 5 socios: Agustina, Viviana, Gonzalo, Pancho y Bruno
• Opera en 2 localidades: MONTEVIDEO y MERCEDES
• Áreas de negocio: Jurídica, Notarial, Contable, Recuperación, Gastos Generales, Otros
• Tipos de operaciones: INGRESO, GASTO, RETIRO, DISTRIBUCION
• Monedas: UYU (pesos uruguayos) y USD (dólares estadounidenses)
• Fórmula de rentabilidad: (Ingresos - Gastos) / Ingresos * 100
• SIEMPRE filtrar deleted_at IS NULL para operaciones activas

REGLAS SQL CRÍTICAS:
• Si pide "en dólares/USD/dólares": usa monto_usd
• Si pide "en pesos/UYU": usa monto_uyu
• Si NO especifica moneda: usa monto_uyu (default)
• Para rentabilidad: SOLO tipos INGRESO y GASTO (excluir RETIRO y DISTRIBUCION)
• Para comparaciones "este X vs anterior": usar DATE_TRUNC y LIMIT con ORDER BY DESC
• Para "mejor/peor": ORDER BY + LIMIT 1
• Para "cómo venimos/estamos": mostrar ingresos, gastos, resultado y rentabilidad
• Para trimestre actual: DATE_TRUNC('quarter', CURRENT_DATE)
• Para mes actual: DATE_TRUNC('month', CURRENT_DATE)
• Para año actual: DATE_TRUNC('year', CURRENT_DATE)
• Los nombres de localidades son MAYÚSCULAS: 'MONTEVIDEO', 'MERCEDES'
• Los nombres de áreas son con mayúscula inicial: 'Jurídica', 'Notarial', etc.
• Los nombres de socios son con mayúscula inicial: 'Bruno', 'Agustina', etc.
"""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no encontrada en .env")
        
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generar_sql(self, pregunta: str) -> str:
        """
        Genera SQL usando Claude Sonnet 4.5
        
        Args:
            pregunta: Pregunta del usuario en lenguaje natural
            
        Returns:
            SQL válido de PostgreSQL o texto explicativo si no puede
        """
        
        prompt = f"""{self.DDL_CONTEXT}

{self.BUSINESS_CONTEXT}

PREGUNTA DEL USUARIO: {pregunta}

INSTRUCCIONES:
• Genera SOLO el SQL query en PostgreSQL, sin explicaciones ni markdown
• NO uses triple backticks ni formato ```sql
• El SQL debe ser ejecutable directamente
• Si la pregunta es ambigua, genera el SQL más probable
• Si pide "en dólares" o "USD", usa monto_usd
• Si pide rentabilidad, usa la fórmula: (Ingresos - Gastos) / Ingresos * 100
• SIEMPRE incluye WHERE deleted_at IS NULL
• Para comparaciones temporales, usa CTEs con DATE_TRUNC

Genera ÚNICAMENTE el SQL query:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1500,
                temperature=0.0,  # Más determinístico
                messages=[{"role": "user", "content": prompt}]
            )
            
            sql_generado = response.content[0].text.strip()
            
            # Limpiar si viene con markdown
            if sql_generado.startswith("```"):
                sql_generado = sql_generado.replace("```sql", "").replace("```", "").strip()
            
            return sql_generado
            
        except Exception as e:
            print(f"Error en Claude SQL Generator: {e}")
            return f"ERROR: {str(e)}"

