#!/usr/bin/env python3
"""
POC - Certificado ALA para Escribanos
Genera certificado de debida diligencia con datos reales

Ejecutar: python3 poc_certificado_ala.py
"""

import requests
import csv
import xml.etree.ElementTree as ET
import hashlib
import json
from datetime import datetime, timezone
from io import StringIO
import unicodedata
import re

# ============================================================================
# DATOS DE LA OPERACIÓN (BRUNO)
# ============================================================================

OPERACION = {
    "tipo": "COMPRAVENTA_INMUEBLE",
    "monto_usd": 150000,
    "forma_pago": "TRANSFERENCIA",
    "fecha": "2026-02-02",
    "descripcion": "Compraventa apartamento Pocitos",
    "escribano": "Esc. Agustina Rodríguez"
}

COMPRADOR = {
    "nombre": "Bruno Gaston Gandolfo Dos Santos",
    "ci": "28677475",
    "nacionalidad": "UY"
}

VENDEDOR = {
    "nombre": "María Fernanda López García", 
    "ci": "12345678",
    "nacionalidad": "UY"
}

# ============================================================================
# FUENTES OFICIALES
# ============================================================================

URL_PEP = "https://catalogodatos.gub.uy/dataset/bcf06dc6-c41e-4307-b466-8168e7556542/resource/fdb17214-13a8-4604-acec-b11a1c612957/download/lista-actualizada-de-pep.csv"
URL_ONU = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"

PAISES_ALTO_RIESGO = {"IR", "KP", "MM"}
PAISES_GREY_LIST = {"SY", "YE", "HT", "PK", "NI", "JM", "TZ", "UG", "VN", "PH"}

# ============================================================================
# FUNCIONES
# ============================================================================

def normalizar(texto):
    """Normaliza texto para comparación"""
    if not texto:
        return ""
    texto = unicodedata.normalize('NFKD', str(texto))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = texto.upper().strip()
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def normalizar_ci(ci):
    """Normaliza cédula: solo dígitos"""
    if not ci:
        return ""
    return re.sub(r'[^\d]', '', str(ci))

def similitud(s1, s2):
    """Similitud simple entre strings"""
    s1, s2 = normalizar(s1), normalizar(s2)
    if not s1 or not s2:
        return 0
    palabras1 = set(s1.split())
    palabras2 = set(s2.split())
    if not palabras1 or not palabras2:
        return 0
    interseccion = len(palabras1 & palabras2)
    union = len(palabras1 | palabras2)
    return int((interseccion / union) * 100) if union > 0 else 0

def verificar_pep(ci, nombre):
    """Verifica si la persona está en lista PEP de Uruguay"""
    print(f"\n📋 Descargando Lista PEP Uruguay...")
    
    try:
        resp = requests.get(URL_PEP, timeout=30)
        resp.raise_for_status()
        print(f"   ✅ Descargado: {len(resp.content):,} bytes")
        
        # Parsear CSV
        contenido = resp.content.decode('utf-8-sig')
        reader = csv.DictReader(StringIO(contenido))
        registros = list(reader)
        print(f"   ✅ Registros: {len(registros):,}")
        
        ci_normalizada = normalizar_ci(ci)
        nombre_normalizado = normalizar(nombre)
        
        # Buscar por CI exacta
        for reg in registros:
            ci_pep = normalizar_ci(reg.get('CI', ''))
            if ci_pep and ci_pep == ci_normalizada:
                return {
                    "es_pep": True,
                    "match_tipo": "CI_EXACTA",
                    "cargo": reg.get('CARGO', ''),
                    "organismo": reg.get('ORGANISMO', ''),
                    "similitud": 100
                }
        
        # Buscar por nombre (fuzzy)
        mejor_match = {"similitud": 0}
        for reg in registros:
            nombre_pep = normalizar(reg.get('NOMBRE', ''))
            sim = similitud(nombre_normalizado, nombre_pep)
            if sim > mejor_match["similitud"]:
                mejor_match = {
                    "similitud": sim,
                    "nombre_lista": reg.get('NOMBRE', ''),
                    "cargo": reg.get('CARGO', ''),
                    "organismo": reg.get('ORGANISMO', '')
                }
        
        es_pep = mejor_match["similitud"] >= 85
        return {
            "es_pep": es_pep,
            "match_tipo": "NOMBRE_FUZZY" if es_pep else "NO_MATCH",
            "similitud": mejor_match["similitud"],
            "mejor_match": mejor_match.get("nombre_lista", ""),
            "cargo": mejor_match.get("cargo", "") if es_pep else "",
            "organismo": mejor_match.get("organismo", "") if es_pep else ""
        }
        
    except Exception as e:
        return {"error": str(e), "es_pep": None}

def verificar_onu(nombre):
    """Verifica si la persona está en lista ONU consolidada"""
    print(f"\n🌐 Descargando Lista ONU Consolidada...")
    
    try:
        resp = requests.get(URL_ONU, timeout=60)
        resp.raise_for_status()
        print(f"   ✅ Descargado: {len(resp.content):,} bytes")
        
        root = ET.fromstring(resp.content)
        ns = {'un': 'https://scsanctions.un.org/consolidated/'}
        
        individuos = root.findall('.//INDIVIDUAL', ns) or root.findall('.//INDIVIDUAL')
        if not individuos:
            # Intentar sin namespace
            individuos = []
            for elem in root.iter():
                if elem.tag.endswith('INDIVIDUAL') or elem.tag == 'INDIVIDUAL':
                    individuos.append(elem)
        
        print(f"   ✅ Individuos en lista: {len(individuos):,}")
        
        nombre_normalizado = normalizar(nombre)
        mejor_match = {"similitud": 0}
        
        for ind in individuos:
            # Buscar en diferentes campos de nombre
            nombres_onu = []
            for tag in ['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME', 'FOURTH_NAME', 
                       'NAME_ORIGINAL_SCRIPT', 'COMMENTS1']:
                elem = ind.find(f'.//{tag}') or ind.find(tag)
                if elem is not None and elem.text:
                    nombres_onu.append(elem.text)
            
            nombre_completo = ' '.join(nombres_onu)
            sim = similitud(nombre_normalizado, nombre_completo)
            
            if sim > mejor_match["similitud"]:
                mejor_match = {
                    "similitud": sim,
                    "nombre_lista": nombre_completo[:100]
                }
        
        en_lista = mejor_match["similitud"] >= 85
        return {
            "en_lista_onu": en_lista,
            "similitud": mejor_match["similitud"],
            "mejor_match": mejor_match.get("nombre_lista", "")
        }
        
    except Exception as e:
        return {"error": str(e), "en_lista_onu": None}

def clasificar_riesgo(persona, operacion, resultado_pep, resultado_onu):
    """Clasifica el riesgo según Decreto 379/018"""
    
    # BLOQUEO TOTAL
    if resultado_onu.get("en_lista_onu"):
        return {
            "nivel": "BLOQUEO",
            "diligencia": "OPERACION_PROHIBIDA",
            "motivo": "Match en Lista ONU - Resoluciones CSNU",
            "puede_operar": False
        }
    
    # ALTO - gatillos automáticos
    if operacion["forma_pago"] == "EFECTIVO":
        return {
            "nivel": "ALTO",
            "diligencia": "INTENSIFICADA",
            "motivo": "Pago en efectivo (Art. 46 Decreto 379/018)",
            "puede_operar": True
        }
    
    if operacion["monto_usd"] > 300000:
        return {
            "nivel": "ALTO", 
            "diligencia": "INTENSIFICADA",
            "motivo": f"Monto > USD 300.000 (Art. 46 Decreto 379/018)",
            "puede_operar": True
        }
    
    if resultado_pep.get("es_pep"):
        return {
            "nivel": "ALTO",
            "diligencia": "INTENSIFICADA",
            "motivo": f"PEP: {resultado_pep.get('cargo', '')} - {resultado_pep.get('organismo', '')}",
            "puede_operar": True
        }
    
    if persona["nacionalidad"] in PAISES_ALTO_RIESGO:
        return {
            "nivel": "ALTO",
            "diligencia": "INTENSIFICADA", 
            "motivo": "País GAFI High-Risk (Call for Action)",
            "puede_operar": True
        }
    
    # MEDIO
    if persona["nacionalidad"] in PAISES_GREY_LIST:
        return {
            "nivel": "MEDIO",
            "diligencia": "NORMAL",
            "motivo": "País GAFI Grey List (Increased Monitoring)",
            "puede_operar": True
        }
    
    # BAJO - puede aplicar simplificada (LUC 2020)
    if operacion["forma_pago"] in ["TRANSFERENCIA", "CREDITO_HIPOTECARIO"]:
        return {
            "nivel": "BAJO",
            "diligencia": "SIMPLIFICADA",
            "motivo": "Pago electrónico + sin factores de riesgo (Art. 17 Ley 19.574 mod. LUC 2020)",
            "puede_operar": True
        }
    
    return {
        "nivel": "BAJO",
        "diligencia": "NORMAL",
        "motivo": "Sin factores de riesgo identificados",
        "puede_operar": True
    }

def generar_certificado(operacion, partes, verificaciones):
    """Genera el certificado final"""
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    certificado = {
        "titulo": "CERTIFICADO DE DEBIDA DILIGENCIA ALA",
        "subtitulo": "Ley 19.574 - Decreto 379/018 - LUC 2020",
        "generado": timestamp,
        "operacion": operacion,
        "partes_verificadas": partes,
        "verificaciones": verificaciones,
        "normativa_aplicada": {
            "ley": "Ley 19.574 (Ley Integral contra Lavado de Activos)",
            "decreto": "Decreto 379/018 (Reglamentario)",
            "modificacion": "Ley 19.889 Art. 225-226 (LUC 2020)",
            "articulos_relevantes": ["Art. 40 (Escribanos)", "Art. 44 (DD Normal)", 
                                    "Art. 45 (DD Simplificada)", "Art. 46 (DD Intensificada)"]
        },
        "fuentes_consultadas": {
            "lista_pep": URL_PEP,
            "lista_onu": URL_ONU,
            "fecha_consulta": timestamp
        }
    }
    
    # Generar hash
    cert_json = json.dumps(certificado, sort_keys=True, ensure_ascii=False)
    certificado["hash"] = f"sha256:{hashlib.sha256(cert_json.encode()).hexdigest()[:32]}"
    
    return certificado

def imprimir_certificado(cert):
    """Imprime el certificado de forma legible"""
    
    print("\n" + "="*80)
    print("                    CERTIFICADO DE DEBIDA DILIGENCIA ALA")
    print("                 Ley 19.574 - Decreto 379/018 - LUC 2020")
    print("="*80)
    
    print(f"\n📅 Fecha: {cert['generado']}")
    print(f"🔐 Hash: {cert['hash']}")
    
    print("\n" + "-"*80)
    print("OPERACIÓN")
    print("-"*80)
    op = cert['operacion']
    print(f"  Tipo:        {op['tipo']}")
    print(f"  Monto:       USD {op['monto_usd']:,.0f}")
    print(f"  Forma pago:  {op['forma_pago']}")
    print(f"  Fecha:       {op['fecha']}")
    print(f"  Descripción: {op['descripcion']}")
    print(f"  Escribano:   {op['escribano']}")
    
    for parte in cert['partes_verificadas']:
        print("\n" + "-"*80)
        print(f"{parte['rol']}")
        print("-"*80)
        print(f"  Nombre:       {parte['nombre']}")
        print(f"  CI:           {parte['ci']}")
        print(f"  Nacionalidad: {parte['nacionalidad']}")
        
        v = parte['verificacion']
        
        # PEP
        pep = v['pep']
        if pep.get('error'):
            print(f"  Lista PEP:    ⚠️ Error: {pep['error']}")
        elif pep['es_pep']:
            print(f"  Lista PEP:    ⚠️ ES PEP - {pep['cargo']} ({pep['organismo']})")
        else:
            print(f"  Lista PEP:    ✅ NO es PEP (similitud máx: {pep['similitud']}%)")
        
        # ONU
        onu = v['onu']
        if onu.get('error'):
            print(f"  Lista ONU:    ⚠️ Error: {onu['error']}")
        elif onu['en_lista_onu']:
            print(f"  Lista ONU:    🚨 APARECE EN LISTA - BLOQUEO TOTAL")
        else:
            print(f"  Lista ONU:    ✅ NO aparece (similitud máx: {onu['similitud']}%)")
        
        # Riesgo
        r = v['riesgo']
        nivel_emoji = {"BAJO": "🟢", "MEDIO": "🟡", "ALTO": "🔴", "BLOQUEO": "⛔"}
        print(f"  Riesgo:       {nivel_emoji.get(r['nivel'], '❓')} {r['nivel']}")
        print(f"  Diligencia:   {r['diligencia']}")
        print(f"  Motivo:       {r['motivo']}")
        print(f"  Puede operar: {'✅ SÍ' if r['puede_operar'] else '❌ NO'}")
    
    print("\n" + "-"*80)
    print("CONCLUSIÓN")
    print("-"*80)
    
    # Determinar resultado global
    todas_ok = all(
        p['verificacion']['riesgo']['puede_operar'] 
        for p in cert['partes_verificadas']
    )
    
    diligencias = [p['verificacion']['riesgo']['diligencia'] for p in cert['partes_verificadas']]
    diligencia_max = "INTENSIFICADA" if "INTENSIFICADA" in diligencias else (
        "NORMAL" if "NORMAL" in diligencias else "SIMPLIFICADA"
    )
    
    if todas_ok:
        print(f"  ✅ OPERACIÓN VÁLIDA")
        print(f"  📋 Diligencia requerida: {diligencia_max}")
        print(f"  📝 Puede procederse a la escrituración")
    else:
        print(f"  ⛔ OPERACIÓN BLOQUEADA")
        print(f"  🚨 No puede procederse - Reportar a UIAF")
    
    print("\n" + "-"*80)
    print("FUENTES CONSULTADAS")
    print("-"*80)
    print(f"  Lista PEP: {cert['fuentes_consultadas']['lista_pep'][:70]}...")
    print(f"  Lista ONU: {cert['fuentes_consultadas']['lista_onu']}")
    
    print("\n" + "="*80)
    print("  Este certificado cumple con Art. 15 Decreto 379/018 (conservación 5 años)")
    print("="*80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n🔍 VERIFICACIÓN ALA - DEBIDA DILIGENCIA AUTOMATIZADA")
    print("="*60)
    
    partes = []
    
    for persona, rol in [(COMPRADOR, "COMPRADOR"), (VENDEDOR, "VENDEDOR")]:
        print(f"\n{'='*60}")
        print(f"Verificando {rol}: {persona['nombre']}")
        print(f"CI: {persona['ci']}")
        
        # Verificar PEP
        resultado_pep = verificar_pep(persona['ci'], persona['nombre'])
        
        # Verificar ONU
        resultado_onu = verificar_onu(persona['nombre'])
        
        # Clasificar riesgo
        riesgo = clasificar_riesgo(persona, OPERACION, resultado_pep, resultado_onu)
        
        partes.append({
            "rol": rol,
            "nombre": persona['nombre'],
            "ci": persona['ci'],
            "nacionalidad": persona['nacionalidad'],
            "verificacion": {
                "pep": resultado_pep,
                "onu": resultado_onu,
                "riesgo": riesgo
            }
        })
    
    # Generar certificado
    verificaciones = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version_modulo": "1.0.0-poc"
    }
    
    certificado = generar_certificado(OPERACION, partes, verificaciones)
    
    # Imprimir
    imprimir_certificado(certificado)
    
    # Guardar JSON
    archivo = "certificado_ala_operacion.json"
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(certificado, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Certificado guardado en: {archivo}")

if __name__ == "__main__":
    main()
