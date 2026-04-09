"""
Script para analizar los resultados del shadow mode del clasificador Haiku.
Ejecutar: cd backend && python -m scripts.analizar_shadow
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json

from app.services.classifier_shadow_log import generar_reporte_shadow, SHADOW_LOG_PATH


def main():
    print("=" * 70)
    print("REPORTE SHADOW MODE - CLASIFICADOR HAIKU")
    print("=" * 70)

    reporte = generar_reporte_shadow()

    if "error" in reporte:
        print(f"\n  {reporte['error']}")
        return

    print(f"\nTotal preguntas analizadas: {reporte['total_preguntas']}")
    print(f"Acuerdos (Haiku = Router actual): {reporte['acuerdos']} ({reporte['acuerdo_pct']}%)")

    print(f"\nClasificaciones de Haiku:")
    for k, v in reporte["clasificaciones_haiku"].items():
        print(f"  {k}: {v}")

    print(f"\nDiscrepancias:")
    for k, v in reporte["discrepancias"].items():
        if v > 0:
            print(f"  {k}: {v}")

    print(f"\nDiscrepancias criticas (HAIKU_LIBERARIA): {reporte['discrepancias_criticas']}")
    print(f"   -> Preguntas donde Haiku habria dejado pasar a Claude pero el template capturo")

    print(f"\nLatencia Haiku: promedio {reporte['latencia_promedio_ms']}ms, max {reporte['latencia_max_ms']}ms")

    print(f"\n{reporte['interpretacion']}")

    # Mostrar detalle de discrepancias
    if os.path.exists(SHADOW_LOG_PATH):
        print("\n" + "-" * 70)
        print("DETALLE DE DISCREPANCIAS (HAIKU_LIBERARIA):")
        print("-" * 70)
        with open(SHADOW_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry.get("discrepancia") == "HAIKU_LIBERARIA":
                    print(f"\n  Pregunta: {entry['pregunta']}")
                    print(
                        f"  Haiku: {entry['haiku']['clasificacion']} "
                        f"(confianza: {entry['haiku']['confianza']})"
                    )
                    print(f"  Razon: {entry['haiku']['razon']}")
                    print(f"  Router actual: template capturo")


if __name__ == "__main__":
    main()
