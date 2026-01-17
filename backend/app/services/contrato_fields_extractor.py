"""
Servicio de Extracción de Campos Editables para Contratos

Analiza el contenido_texto de contratos usando Claude para identificar
y extraer automáticamente todos los placeholders (____________, [___], [...]).

Autor: Sistema CFO Inteligente
Fecha: Enero 2026
"""

import json
import re
from datetime import datetime
from typing import Optional, Dict, List, Any

from app.core.logger import get_logger
from app.services.ai.claude_client import ClaudeClient

logger = get_logger(__name__)


class ContratoFieldsExtractor:
    """
    Extrae campos editables de contratos usando Claude.
    
    Analiza el contenido_texto y detecta placeholders como:
    - ____________ (líneas de subrayado)
    - [___] (corchetes con guiones)
    - [...] (corchetes con puntos)
    
    Para cada placeholder detectado, Claude determina:
    - ID único
    - Nombre descriptivo
    - Tipo de dato (fecha, texto, cédula, etc.)
    - Si es requerido
    - Contexto donde aparece
    - Orden de aparición
    """
    
    # Tipos de campos válidos
    TIPOS_VALIDOS = [
        "texto",
        "fecha",
        "cedula",
        "rut",
        "moneda",
        "numero",
        "telefono",
        "email",
        "direccion"
    ]
    
    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        """
        Constructor.
        
        Args:
            claude_client: Instancia de ClaudeClient (opcional, se crea si no se provee)
        """
        self.claude_client = claude_client or ClaudeClient()
        logger.info("ContratoFieldsExtractor inicializado")
    
    def extract_fields(self, contenido_texto: str) -> Optional[Dict[str, Any]]:
        """
        Extrae campos editables del contenido_texto usando Claude.
        
        Args:
            contenido_texto: Texto plano del contrato
            
        Returns:
            Dict con estructura validada de campos extraídos, o None si falla
            
        Estructura retornada:
        {
            "version": "1.0",
            "extraido_por": "claude-sonnet-4",
            "fecha_extraccion": "2026-01-15T10:30:00Z",
            "campos": [
                {
                    "id": "fecha_contrato",
                    "nombre": "Fecha del contrato",
                    "tipo": "fecha",
                    "requerido": true,
                    "placeholder_original": "____________",
                    "contexto": "el día ____________ quienes suscriben",
                    "orden": 1
                }
            ],
            "total_campos": 1
        }
        """
        if not contenido_texto or not contenido_texto.strip():
            logger.warning("ContratoFieldsExtractor: contenido_texto vacío")
            return None
        
        logger.info(f"Extrayendo campos de contrato ({len(contenido_texto)} caracteres)")
        
        # Construir prompt para Claude
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(contenido_texto)
        
        try:
            # Llamar a Claude con reintento
            response_text = self.claude_client.complete_with_retry(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1,  # Baja temperatura para respuestas consistentes
                max_tokens=16000,  # Aumentado para contratos con 100+ placeholders (~140 campos max)
                timeout=90,  # Timeout más largo para análisis complejos
                max_retries=2  # Reintentar 1 vez adicional (total 2 intentos)
            )
            
            if not response_text:
                logger.error("ContratoFieldsExtractor: Claude no retornó respuesta")
                return None
            
            # Logging del response raw para debugging
            logger.info(f"ContratoFieldsExtractor: Response de Claude ({len(response_text)} chars)")
            logger.debug(f"ContratoFieldsExtractor: Response raw (primeros 500 chars): {response_text[:500]}")
            logger.debug(f"ContratoFieldsExtractor: Response raw (últimos 500 chars): {response_text[-500:]}")
            
            # Extraer JSON de la respuesta (puede tener texto antes/después)
            json_data = self._extract_json_from_response(response_text)
            
            if not json_data:
                logger.error("ContratoFieldsExtractor: No se pudo extraer JSON válido")
                logger.error(f"ContratoFieldsExtractor: Response completo para debugging:\n{response_text}")
                return None
            
            # Logging del JSON parseado
            logger.debug(f"ContratoFieldsExtractor: JSON parseado: {json.dumps(json_data, indent=2, ensure_ascii=False)[:1000]}")
            
            # Validar estructura
            validated_data = self._validate_structure(json_data)
            
            if not validated_data:
                logger.error("ContratoFieldsExtractor: Estructura JSON inválida")
                return None
            
            logger.info(
                f"ContratoFieldsExtractor: Extraídos {validated_data.get('total_campos', 0)} campos"
            )
            
            return validated_data
            
        except Exception as e:
            logger.error(f"ContratoFieldsExtractor: Error extrayendo campos - {e}", exc_info=True)
            return None
    
    def _build_system_prompt(self) -> str:
        """
        Construye el system prompt para Claude.
        
        Returns:
            String con instrucciones del sistema
        """
        return """Eres un experto en análisis de documentos legales y contratos.

Tu tarea es analizar el texto de un contrato y extraer TODOS los placeholders (campos editables) que encuentres.

TIPOS DE PLACEHOLDERS A BUSCAR:
1. Líneas de subrayado: ____________ (5 o más guiones bajos)
2. Corchetes con guiones: [___] o [____]
3. Corchetes con puntos: [...] o [....]

TIPOS DE CAMPOS VÁLIDOS:
- texto: Texto libre (nombres, descripciones, etc.)
- fecha: Fechas (día, mes, año)
- cedula: Cédula de identidad uruguaya
- rut: RUT uruguayo
- moneda: Montos en pesos o dólares
- numero: Números (años, cantidades, etc.)
- telefono: Números de teléfono
- email: Direcciones de correo electrónico
- direccion: Direcciones físicas

INSTRUCCIONES:
1. Identifica TODOS los placeholders en el texto
2. Para cada placeholder, determina:
   - Un ID único (snake_case, descriptivo)
   - Un nombre legible en español
   - El tipo de dato más apropiado
   - Si es requerido (true/false)
   - El contexto donde aparece (frase completa con el placeholder)
   - El orden de aparición (1, 2, 3...)
3. Si encuentras placeholders duplicados (mismo contexto), usa el mismo ID
4. Responde SOLO con JSON válido, sin texto adicional antes o después

IMPORTANTE:
- El JSON debe ser válido y parseable
- No agregues explicaciones fuera del JSON
- Si no encuentras placeholders, retorna {"campos": [], "total_campos": 0}"""
    
    def _build_user_prompt(self, contenido_texto: str) -> str:
        """
        Construye el user prompt con el contenido del contrato.
        
        Args:
            contenido_texto: Texto del contrato
            
        Returns:
            String con el prompt del usuario
        """
        # Limitar tamaño del texto para evitar tokens excesivos
        # Claude puede manejar ~200k tokens, pero limitamos a ~50k caracteres
        texto_limitado = contenido_texto[:50000] if len(contenido_texto) > 50000 else contenido_texto
        
        if len(contenido_texto) > 50000:
            logger.warning(
                f"ContratoFieldsExtractor: Texto truncado de {len(contenido_texto)} "
                f"a {len(texto_limitado)} caracteres"
            )
        
        return f"""Analiza el siguiente contrato y extrae TODOS los placeholders (campos editables) que encuentres.

CONTRATO:
{texto_limitado}

Retorna SOLO un JSON válido con esta estructura exacta:
{{
  "version": "1.0",
  "extraido_por": "claude-sonnet-4",
  "fecha_extraccion": "ISO datetime",
  "campos": [
    {{
      "id": "fecha_contrato",
      "nombre": "Fecha del contrato",
      "tipo": "fecha",
      "requerido": true,
      "placeholder_original": "____________",
      "contexto": "el día ____________ quienes suscriben",
      "orden": 1
    }}
  ],
  "total_campos": 1
}}

CRÍTICO - FORMATO DE RESPUESTA:

Responde con UN SOLO objeto JSON
El objeto DEBE tener una key "campos" que sea un ARRAY
NO devuelvas objetos separados por cada campo
NO devuelvas un array directamente, debe ser un objeto con key "campos"
Si no encuentras placeholders, devuelve: {{"campos": [], "total_campos": 0}}

Recuerda:
- Identifica TODOS los placeholders
- Usa IDs únicos y descriptivos
- Determina el tipo correcto para cada campo
- Incluye el contexto completo donde aparece cada placeholder
- Responde SOLO con JSON, sin texto adicional"""
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extrae JSON de la respuesta de Claude.
        
        Claude puede retornar JSON con texto antes/después, así que buscamos
        el bloque JSON válido.
        
        Args:
            response_text: Respuesta completa de Claude
            
        Returns:
            Dict con JSON parseado, o None si no se encuentra JSON válido
        """
        # INTENTO 1: Parsear directamente
        try:
            parsed = json.loads(response_text.strip())
            if isinstance(parsed, dict):
                logger.debug("ContratoFieldsExtractor: JSON parseado directamente")
                return parsed
        except json.JSONDecodeError:
            pass
        
        # INTENTO 2: Buscar JSON dentro de bloques de código markdown (```json ... ```)
        # Extraer TODO el contenido entre ```json y ```, luego buscar JSON dentro
        code_block_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', response_text)
        if code_block_match:
            block_content = code_block_match.group(1).strip()
            # Buscar desde el primer { hasta el último } dentro del bloque
            start = block_content.find('{')
            end = block_content.rfind('}') + 1
            if start != -1 and end > start:
                json_str = block_content[start:end]
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        logger.debug("ContratoFieldsExtractor: JSON encontrado en bloque markdown")
                        return parsed
                except json.JSONDecodeError:
                    logger.debug("ContratoFieldsExtractor: Bloque markdown encontrado pero JSON inválido")
        
        # INTENTO 2b: Bloque markdown sin cierre (JSON truncado por max_tokens)
        # Si empieza con ```json pero no tiene ``` de cierre
        if '```json' in response_text or '```\n{' in response_text:
            # Extraer desde ```json hasta el final
            json_start_match = re.search(r'```(?:json)?\s*\n?', response_text)
            if json_start_match:
                content_after_marker = response_text[json_start_match.end():]
                start = content_after_marker.find('{')
                end = content_after_marker.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content_after_marker[start:end]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict):
                            logger.debug("ContratoFieldsExtractor: JSON encontrado en bloque markdown sin cierre")
                            return parsed
                    except json.JSONDecodeError:
                        logger.debug("ContratoFieldsExtractor: Bloque markdown sin cierre, JSON inválido")
        
        # INTENTO 3: Buscar primer { y último } en todo el response (JSON completo)
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response_text[start:end]
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    logger.debug("ContratoFieldsExtractor: JSON extraído del texto (primer { hasta último })")
                    return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        
        # INTENTO 4: Buscar múltiples bloques JSON y elegir el más grande/válido
        # Patrón para JSON con hasta 3 niveles de anidación
        json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        # Ordenar por tamaño (el más grande probablemente es el correcto)
        matches.sort(key=len, reverse=True)
        
        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict):
                    logger.debug(f"ContratoFieldsExtractor: JSON encontrado con patrón regex ({len(match)} chars)")
                    return parsed
            except json.JSONDecodeError:
                continue
        
        # INTENTO 5: Buscar variantes del nombre del campo ('fields' en vez de 'campos')
        # A veces Claude usa nombres en inglés
        for variant in ['fields', 'campos', 'field_list', 'editable_fields']:
            pattern = rf'"{variant}"\s*:\s*\['
            if re.search(pattern, response_text, re.IGNORECASE):
                logger.debug(f"ContratoFieldsExtractor: Encontrado campo '{variant}', intentando parsear...")
                # Intentar extraer JSON que contenga este campo
                try:
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    if start != -1 and end > start:
                        json_str = response_text[start:end]
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict):
                            # Normalizar nombre del campo si es diferente
                            if variant != 'campos' and variant in parsed:
                                parsed['campos'] = parsed.pop(variant)
                            logger.debug(f"ContratoFieldsExtractor: JSON parseado con campo '{variant}' normalizado")
                            return parsed
                except (json.JSONDecodeError, ValueError):
                    continue
        
        logger.warning("ContratoFieldsExtractor: No se encontró JSON válido en la respuesta")
        logger.debug(f"ContratoFieldsExtractor: Primeros 1000 chars del response: {response_text[:1000]}")
        return None
    
    def _validate_structure(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Valida y normaliza la estructura del JSON retornado por Claude.
        
        Args:
            data: Dict con datos crudos de Claude
            
        Returns:
            Dict validado y normalizado, o None si es inválido
        """
        try:
            # Validar estructura base
            if not isinstance(data, dict):
                logger.error("ContratoFieldsExtractor: data no es un dict")
                return None
            
            # Validar campos requeridos (aceptar variantes)
            campos_key = None
            for key in ['campos', 'fields', 'field_list', 'editable_fields']:
                if key in data:
                    campos_key = key
                    break
            
            if not campos_key:
                logger.error("ContratoFieldsExtractor: falta campo 'campos' (o variantes: fields, field_list, editable_fields)")
                logger.error(f"ContratoFieldsExtractor: Keys encontrados en JSON: {list(data.keys())}")
                return None
            
            # Normalizar nombre del campo si es diferente
            if campos_key != 'campos':
                logger.info(f"ContratoFieldsExtractor: Normalizando campo '{campos_key}' a 'campos'")
                data['campos'] = data.pop(campos_key)
            
            campos = data.get("campos", [])
            if not isinstance(campos, list):
                logger.error("ContratoFieldsExtractor: 'campos' no es una lista")
                return None
            
            # Validar y normalizar cada campo
            campos_validados = []
            for i, campo in enumerate(campos):
                if not isinstance(campo, dict):
                    logger.warning(f"ContratoFieldsExtractor: Campo {i} no es un dict, saltando")
                    continue
                
                campo_validado = self._validate_campo(campo, i + 1)
                if campo_validado:
                    campos_validados.append(campo_validado)
            
            # Construir estructura final validada
            estructura_final = {
                "version": data.get("version", "1.0"),
                "extraido_por": data.get("extraido_por", "claude-sonnet-4"),
                "fecha_extraccion": data.get("fecha_extraccion", datetime.utcnow().isoformat() + "Z"),
                "campos": campos_validados,
                "total_campos": len(campos_validados)
            }
            
            return estructura_final
            
        except Exception as e:
            logger.error(f"ContratoFieldsExtractor: Error validando estructura - {e}", exc_info=True)
            return None
    
    def _validate_campo(self, campo: Dict[str, Any], orden_default: int) -> Optional[Dict[str, Any]]:
        """
        Valida y normaliza un campo individual.
        
        Args:
            campo: Dict con datos del campo
            orden_default: Orden por defecto si no se especifica
            
        Returns:
            Dict con campo validado, o None si es inválido
        """
        try:
            # Validar campos requeridos
            id_campo = campo.get("id")
            if not id_campo or not isinstance(id_campo, str):
                logger.warning(f"ContratoFieldsExtractor: Campo sin ID válido, saltando")
                return None
            
            # Normalizar ID (snake_case)
            id_campo = re.sub(r'[^a-z0-9_]', '_', id_campo.lower())
            id_campo = re.sub(r'_+', '_', id_campo).strip('_')
            
            if not id_campo:
                logger.warning(f"ContratoFieldsExtractor: ID normalizado vacío, saltando")
                return None
            
            # Validar tipo
            tipo = campo.get("tipo", "texto")
            if tipo not in self.TIPOS_VALIDOS:
                logger.warning(
                    f"ContratoFieldsExtractor: Tipo '{tipo}' inválido para campo '{id_campo}', "
                    f"usando 'texto' por defecto"
                )
                tipo = "texto"
            
            # Construir campo validado
            campo_validado = {
                "id": id_campo,
                "nombre": campo.get("nombre", id_campo.replace("_", " ").title()),
                "tipo": tipo,
                "requerido": bool(campo.get("requerido", True)),
                "placeholder_original": campo.get("placeholder_original", ""),
                "contexto": campo.get("contexto", ""),
                "orden": int(campo.get("orden", orden_default))
            }
            
            return campo_validado
            
        except Exception as e:
            logger.warning(f"ContratoFieldsExtractor: Error validando campo - {e}")
            return None
