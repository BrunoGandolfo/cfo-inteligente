#!/usr/bin/env python3
"""
POC Módulo ALA - CFO Inteligente
Prueba con datos reales: Bruno Gaston Gandolfo Dos Santos - CI 28677475
"""

import csv
import hashlib
import io
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import requests

PERSONA_TEST = {
    "nombre_completo": "Bruno Gaston Gandolfo Dos Santos",
    "ci": "28677475",
    "fecha_nacimiento": "1975-01-01",
    "nacionalidad": "Uruguaya",
    "tipo_operacion": "COMPRAVENTA_INMUEBLE",
    "monto_usd": 150000,
    "forma_pago": "TRANSFERENCIA",
}

PEP_CSV_URL = "https://catalogodatos.gub.uy/dataset/bcf06dc6-c41e-4307-b466-8168e7556542/resource/fdb17214-13a8-4604-acec-b11a1c612957/download/lista-actualizada-de-pep.csv"
ONU_XML_URL = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"

GAFI_HIGH_RISK = ["Iran", "Democratic People's Republic of Korea", "Myanmar"]
GAFI_GREY_LIST = ["Albania", "Barbados", "Burkina Faso", "Cameroon", "Haiti", "Jamaica", "Jordan", "Nigeria", "Panama", "Philippines", "South Africa", "Syria", "Tanzania", "Turkey", "Uganda", "Venezuela", "Vietnam", "Yemen"]

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def normalizar_texto(texto):
    import unicodedata
    if not texto:
        return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = texto.upper().strip()
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def normalizar_ci(ci):
    return re.sub(r'\D', '', ci or '')

def similitud_nombres(nombre1, nombre2):
    n1 = set(normalizar_texto(nombre1).split())
    n2 = set(normalizar_texto(nombre2).split())
    if not n1 or not n2:
        return 0.0
    interseccion = len(n1 & n2)
    union = len(n1 | n2)
    return interseccion / union if union > 0 else 0.0

def descargar_lista_pep():
    print("\n" + "="*70)
    print("1. DESCARGANDO LISTA PEP (SENACLAFT)")
    print("="*70)
    try:
        response = requests.get(PEP_CSV_URL, timeout=60)
        response.raise_for_status()
        contenido = response.content
        hash_archivo = sha256(contenido)
        print(f"   OK Descargado: {len(contenido):,} bytes")
        print(f"   OK SHA256: {hash_archivo[:16]}...")
        try:
            texto = contenido.decode('utf-8-sig')
        except:
            texto = contenido.decode('latin-1')
        reader = csv.DictReader(io.StringIO(texto))
        registros = list(reader)
        print(f"   OK Registros: {len(registros):,}")
        print(f"   OK Columnas: {reader.fieldnames}")
        return {"registros": registros, "hash": hash_archivo, "total": len(registros)}
    except Exception as e:
        print(f"   ERROR: {e}")
        return None

def verificar_pep(persona, lista_pep):
    print("\n" + "-"*70)
    print("   VERIFICANDO EN LISTA PEP...")
    print("-"*70)
    ci_buscar = normalizar_ci(persona["ci"])
    nombre_buscar = normalizar_texto(persona["nombre_completo"])
    print(f"   Buscando CI: {ci_buscar}")
    print(f"   Buscando nombre: {nombre_buscar}")
    resultado = {"es_pep": False, "match_ci": False, "match_nombre": False, "cargo": None, "organismo": None, "similitud": 0.0}
    mejor_similitud = 0.0
    mejor_match = None
    for registro in lista_pep["registros"]:
        ci_registro = normalizar_ci(registro.get("CI", ""))
        nombre_registro = normalizar_texto(registro.get("NOMBRE", ""))
        if ci_registro == ci_buscar:
            resultado["es_pep"] = True
            resultado["match_ci"] = True
            resultado["cargo"] = registro.get("CARGO")
            resultado["organismo"] = registro.get("ORGANISMO")
            print(f"\n   ALERTA MATCH POR CI ENCONTRADO!")
            print(f"       Nombre en lista: {registro.get('NOMBRE')}")
            print(f"       Cargo: {registro.get('CARGO')}")
            print(f"       Organismo: {registro.get('ORGANISMO')}")
            return resultado
        sim = similitud_nombres(nombre_buscar, nombre_registro)
        if sim > mejor_similitud:
            mejor_similitud = sim
            mejor_match = registro
    resultado["similitud"] = mejor_similitud
    if mejor_similitud >= 0.85:
        resultado["es_pep"] = True
        resultado["match_nombre"] = True
        resultado["cargo"] = mejor_match.get("CARGO")
        resultado["organismo"] = mejor_match.get("ORGANISMO")
        print(f"\n   ALERTA POSIBLE MATCH POR NOMBRE (similitud: {mejor_similitud:.0%})")
    else:
        print(f"\n   OK NO ES PEP (mejor similitud: {mejor_similitud:.0%})")
    return resultado

def descargar_lista_onu():
    print("\n" + "="*70)
    print("2. DESCARGANDO LISTA ONU CONSOLIDADA")
    print("="*70)
    try:
        response = requests.get(ONU_XML_URL, timeout=120)
        response.raise_for_status()
        contenido = response.content
        hash_archivo = sha256(contenido)
        print(f"   OK Descargado: {len(contenido):,} bytes")
        print(f"   OK SHA256: {hash_archivo[:16]}...")
        root = ET.fromstring(contenido)
        individuos = root.findall(".//INDIVIDUAL")
        entidades = root.findall(".//ENTITY")
        print(f"   OK Individuos: {len(individuos):,}")
        print(f"   OK Entidades: {len(entidades):,}")
        return {"root": root, "individuos": individuos, "hash": hash_archivo, "total_individuos": len(individuos)}
    except Exception as e:
        print(f"   ERROR: {e}")
        return None

def verificar_onu(persona, lista_onu):
    print("\n" + "-"*70)
    print("   VERIFICANDO EN LISTA ONU...")
    print("-"*70)
    nombre_buscar = normalizar_texto(persona["nombre_completo"])
    resultado = {"aparece": False, "nombres_encontrados": [], "listas_consultadas": ["1267", "1988", "1989", "1718", "1737", "2231", "1373"]}
    mejor_similitud = 0.0
    for individuo in lista_onu["individuos"]:
        nombres_xml = []
        for tag in ["FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME"]:
            elem = individuo.find(tag)
            if elem is not None and elem.text:
                nombres_xml.append(elem.text)
        nombre_completo_onu = " ".join(nombres_xml)
        for alias in individuo.findall(".//ALIAS_NAME"):
            if alias.text:
                nombres_xml.append(alias.text)
        for nombre_onu in nombres_xml:
            sim = similitud_nombres(nombre_buscar, nombre_onu)
            if sim > mejor_similitud:
                mejor_similitud = sim
            if sim >= 0.85:
                resultado["aparece"] = True
                resultado["nombres_encontrados"].append(nombre_onu)
    if resultado["aparece"]:
        print(f"\n   ALERTA POSIBLE MATCH EN LISTA ONU!")
        print(f"       Nombres: {resultado['nombres_encontrados']}")
    else:
        print(f"\n   OK NO APARECE EN LISTA ONU (mejor similitud: {mejor_similitud:.0%})")
    return resultado

def clasificar_riesgo(persona, resultado_pep, resultado_onu):
    print("\n" + "="*70)
    print("3. CLASIFICACION DE RIESGO (Decreto 379/018)")
    print("="*70)
    factores = []
    nivel = "BAJO"
    diligencia = "SIMPLIFICADA"
    valido = True
    if resultado_onu and resultado_onu.get("aparece"):
        factores.append("BLOQUEO: COINCIDENCIA EN LISTA ONU")
        return {"nivel": "ALTO", "factores": factores, "diligencia": "INTENSIFICADA", "valido_para_escritura": False}
    if resultado_pep and resultado_pep.get("es_pep"):
        factores.append("Cliente es PEP")
        nivel = "ALTO"
    if persona.get("forma_pago") == "EFECTIVO":
        factores.append("Operacion en EFECTIVO")
        nivel = "ALTO"
    if persona.get("monto_usd", 0) > 300000:
        factores.append(f"Monto > USD 300.000")
        nivel = "ALTO"
    if persona.get("nacionalidad") in GAFI_HIGH_RISK:
        factores.append("Jurisdiccion GAFI alto riesgo")
        nivel = "ALTO"
    if persona.get("nacionalidad") in GAFI_GREY_LIST and nivel != "ALTO":
        factores.append("Jurisdiccion GAFI grey list")
        nivel = "MEDIO"
    if nivel == "ALTO":
        diligencia = "INTENSIFICADA"
        valido = False
    elif nivel == "MEDIO":
        diligencia = "NORMAL"
    else:
        factores.append("Sin factores de riesgo")
    if persona.get("forma_pago") in ["TRANSFERENCIA", "CREDITO_HIPOTECARIO"] and nivel == "BAJO":
        factores.append("Elegible diligencia simplificada (LUC 2020)")
    print(f"\n   Nivel: {nivel}")
    print(f"   Diligencia: {diligencia}")
    print(f"   Valido para escritura: {'SI' if valido else 'NO'}")
    print(f"   Factores:")
    for f in factores:
        print(f"      - {f}")
    return {"nivel": nivel, "factores": factores, "diligencia": diligencia, "valido_para_escritura": valido}

def main():
    print("\n" + "#"*70)
    print("#  POC MODULO ALA - CFO INTELIGENTE")
    print("#  Verificacion de Debida Diligencia (Decreto 379/018)")
    print("#"*70)
    print(f"\nPERSONA A VERIFICAR:")
    print(f"   Nombre: {PERSONA_TEST['nombre_completo']}")
    print(f"   CI: {PERSONA_TEST['ci']}")
    print(f"   Operacion: {PERSONA_TEST['tipo_operacion']}")
    print(f"   Monto: USD {PERSONA_TEST['monto_usd']:,}")
    print(f"   Forma de pago: {PERSONA_TEST['forma_pago']}")
    
    lista_pep = descargar_lista_pep()
    resultado_pep = verificar_pep(PERSONA_TEST, lista_pep) if lista_pep else None
    
    lista_onu = descargar_lista_onu()
    resultado_onu = verificar_onu(PERSONA_TEST, lista_onu) if lista_onu else None
    
    riesgo = clasificar_riesgo(PERSONA_TEST, resultado_pep, resultado_onu)
    
    print("\n" + "#"*70)
    print("#  RESULTADO FINAL")
    print("#"*70)
    import json
    certificado = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "persona": {"nombre": PERSONA_TEST["nombre_completo"], "ci": PERSONA_TEST["ci"]},
        "pep": resultado_pep,
        "onu": resultado_onu,
        "riesgo": riesgo
    }
    cert_str = json.dumps(certificado, indent=2, ensure_ascii=False, default=str)
    certificado["hash"] = f"sha256:{sha256(cert_str.encode())[:32]}"
    print(json.dumps(certificado, indent=2, ensure_ascii=False, default=str))
    
    with open("certificado_ala_bruno.json", "w") as f:
        json.dump(certificado, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nGuardado en: certificado_ala_bruno.json")
    
    print("\n" + "#"*70)
    if riesgo["valido_para_escritura"]:
        print("#  VERIFICACION OK - VALIDO PARA ESCRITURA")
    else:
        print("#  REQUIERE REVISION ADICIONAL")
    print("#"*70 + "\n")

if __name__ == "__main__":
    main()
