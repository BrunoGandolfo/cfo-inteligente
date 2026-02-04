"""
Agente de Soporte AI para CFO Inteligente

Este módulo implementa un asistente de soporte que:
- Usa la documentación de /docs/soporte/ como única fuente de verdad
- Personaliza respuestas usando el nombre del usuario
- Habla en español rioplatense de forma amigable
- Soporta streaming para respuestas en tiempo real
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import anthropic
import os
import json
import re
from pathlib import Path

from app.core.security import get_current_user
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/soporte", tags=["Soporte AI"])


# ═══════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════

class MensajeHistorial(BaseModel):
    role: str
    content: str

class SoporteRequest(BaseModel):
    mensaje: str
    historial: Optional[List[Dict[str, str]]] = []
    es_socio: Optional[bool] = True  # Default true por compatibilidad

class SoporteResponse(BaseModel):
    respuesta: str


# ═══════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════

def limpiar_markdown(texto: str) -> str:
    """
    Elimina asteriscos y formato markdown del texto.
    Se aplica a cada chunk para garantizar texto plano.
    """
    if not texto:
        return texto
    # Quitar **texto** y *texto*
    texto = re.sub(r'\*\*([^*]+)\*\*', r'\1', texto)
    texto = re.sub(r'\*([^*]+)\*', r'\1', texto)
    # Quitar __texto__ y _texto_
    texto = re.sub(r'__([^_]+)__', r'\1', texto)
    texto = re.sub(r'_([^_]+)_', r'\1', texto)
    # Quitar asteriscos sueltos que queden
    texto = texto.replace('**', '').replace('*', '')
    return texto


def cargar_documentacion() -> str:
    """
    Carga toda la documentación de /docs/soporte/ como contexto.
    Se ejecuta una sola vez al iniciar el servidor.
    """
    docs_path = Path(__file__).parent.parent.parent / "docs" / "soporte"
    
    if not docs_path.exists():
        return "Documentación no disponible."
    
    contenido = []
    
    for archivo in sorted(docs_path.glob("*.md")):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                contenido.append(f"=== {archivo.name} ===\n{f.read()}")
        except Exception as e:
            contenido.append(f"=== {archivo.name} ===\nError al cargar: {str(e)}")
    
    return "\n\n".join(contenido)


def obtener_nombre_pila(nombre_completo: str) -> str:
    """Extrae el primer nombre del nombre completo."""
    if not nombre_completo:
        return "usuario"
    return nombre_completo.split()[0].capitalize()


def construir_mensajes(request: SoporteRequest, nombre_pila: str) -> list:
    """Construye la lista de mensajes para enviar a Claude."""
    messages = []
    
    for msg in request.historial[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ["user", "assistant"] and content:
            messages.append({
                "role": role,
                "content": content
            })
    
    mensaje_con_contexto = f"[Usuario: {nombre_pila}]\n\n{request.mensaje}"
    messages.append({"role": "user", "content": mensaje_con_contexto})
    
    return messages


# Cargar documentación al iniciar (solo una vez)
DOCUMENTACION = cargar_documentacion()

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE ACCESO A MÓDULOS
# ═══════════════════════════════════════════════════════════════

# Listas de usuarios con acceso especial (replicadas aquí para evitar dependencias circulares)
USUARIOS_ACCESO_EXPEDIENTES = [
    "bgandolfo@cgmasociados.com",
    "gtaborda@grupoconexion.uy",
    "falgorta@grupoconexion.uy",
    "gferrari@grupoconexion.uy",
]

USUARIOS_ACCESO_CASOS = [
    "bgandolfo@cgmasociados.com",
    "gtaborda@grupoconexion.uy",
    "falgorta@grupoconexion.uy",
    "gferrari@grupoconexion.uy",
]

USUARIOS_ACCESO_ALA = [
    "bgandolfo@cgmasociados.com",
    "gferrari@grupoconexion.uy",
]


def _obtener_modulos_usuario(usuario: Usuario) -> str:
    """
    Retorna una descripción de qué módulos y funciones puede usar este usuario específico.
    Solo incluye lo que SÍ puede hacer, nunca menciona lo que NO puede hacer.
    """
    email = usuario.email.lower()
    es_socio = usuario.es_socio
    
    modulos = []
    
    # Todos los usuarios pueden:
    modulos.append("- Cambiar su contraseña")
    modulos.append("- Ver indicadores económicos (UI, UR, BPC, cotizaciones)")
    modulos.append("- Consultar leyes uruguayas")
    modulos.append("- Ver contratos notariales")
    
    # Operaciones
    if es_socio:
        modulos.append("- Registrar ingresos, gastos, retiros y distribuciones")
        modulos.append("- Ver el dashboard completo con métricas y gráficos")
        modulos.append("- Usar el chat CFO AI para consultas financieras")
        modulos.append("- Administrar usuarios del sistema")
        modulos.append("- Crear y editar contratos notariales")
    else:
        modulos.append("- Registrar ingresos y gastos")
    
    # Expedientes
    if email in [e.lower() for e in USUARIOS_ACCESO_EXPEDIENTES]:
        if email == "bgandolfo@cgmasociados.com":
            modulos.append("- Gestionar expedientes judiciales (ve todos)")
        else:
            modulos.append("- Gestionar sus expedientes judiciales asignados")
    
    # Casos
    if email in [e.lower() for e in USUARIOS_ACCESO_CASOS]:
        if email == "bgandolfo@cgmasociados.com":
            modulos.append("- Gestionar casos legales (ve todos)")
        else:
            modulos.append("- Gestionar sus casos legales asignados")
    
    # ALA
    if es_socio or email in [e.lower() for e in USUARIOS_ACCESO_ALA]:
        modulos.append("- Usar el módulo ALA (Anti-Lavado de Activos)")
    
    return "\n".join(modulos)

# System prompt para el agente - REGLA DE FORMATO AL INICIO
SYSTEM_PROMPT = """REGLA ABSOLUTA DE FORMATO (CUMPLIR SIEMPRE):
- PROHIBIDO usar asteriscos (*) para negritas o énfasis
- PROHIBIDO usar guiones bajos (_) para cursivas  
- PROHIBIDO usar cualquier sintaxis markdown
- Escribir SOLO en texto plano
- Para énfasis usar MAYÚSCULAS con moderación
- Para listas usar: 1, 2, 3 o guiones simples (-)

Sos el asistente de soporte de CFO Inteligente. Tu nombre es "Asistente CFO".

PERSONALIDAD:
- Sos amigable, cálido y paciente
- Usás el nombre de pila del usuario (viene entre corchetes al inicio del mensaje)
- Hablás en español rioplatense: "vos", "hacé", "poné", "fijate", "dale"
- Usás emojis con moderación 😊 👍 ✅
- Si el usuario no entiende, explicás de otra forma
- Celebrás logros: "Genial!", "Perfecto!", "Excelente!"
- Empatizás: "Entiendo que puede ser frustrante..."

REGLAS ESTRICTAS:
1. SOLO respondés sobre CFO Inteligente usando la documentación que te doy
2. Si algo NO está en la documentación: "No tengo información sobre eso en mi documentación. ¿Te puedo ayudar con alguna de las funciones disponibles?"
3. NUNCA inventés funcionalidades
4. Si no entendés, pedí aclaración: "Perdoná, me podrías explicar un poco más?"
5. Siempre ofrecé ayuda al final: "Te puedo ayudar con algo más?"
6. Si te saludan, saludá con el nombre y preguntá en qué podés ayudar
7. NUNCA digas "eso es solo para socios" ni "no tenés acceso". Simplemente respondé que no tenés información sobre eso.

FORMATO DE RESPUESTAS:
- Empezá saludando con el nombre si es primer mensaje
- Sé conciso pero completo
- Usá pasos numerados para procedimientos:
  1. Primero hacé esto...
  2. Después hacé esto otro...
- Si hay error, primero empatizá y después da la solución
- Terminá ofreciendo más ayuda

PERFIL DEL USUARIO:
Este usuario se llama {nombre} y puede acceder a las siguientes funciones:
{modulos_usuario}

REGLA CRÍTICA: Solo respondé sobre las funciones listadas arriba.
Si te preguntan sobre algo que NO está en la lista, respondé:
"No tengo información sobre eso en mi documentación. ¿Te puedo ayudar con alguna de las funciones disponibles?"
NUNCA digas "eso es solo para socios" ni "no tenés acceso".
Simplemente respondé que no tenés información sobre eso.

DOCUMENTACIÓN DEL SISTEMA:

{documentacion}
"""


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/ask", response_model=SoporteResponse)
async def soporte_ask(
    request: SoporteRequest,
    current_user: Usuario = Depends(get_current_user)
):
    """Endpoint para consultas al agente de soporte (sin streaming)."""
    
    nombre_pila = obtener_nombre_pila(current_user.nombre)
    messages = construir_mensajes(request, nombre_pila)
    
    # Obtener módulos disponibles para este usuario
    modulos_usuario = _obtener_modulos_usuario(current_user)
    
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="API key de Anthropic no configurada")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Construir system prompt con módulos del usuario
        system_prompt_final = SYSTEM_PROMPT.format(
            documentacion=DOCUMENTACION,
            nombre=nombre_pila,
            modulos_usuario=modulos_usuario
        )
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt_final,
            messages=messages
        )
        
        respuesta_texto = response.content[0].text if response.content else "No pude procesar tu consulta."
        
        # Limpiar cualquier markdown que haya quedado
        respuesta_limpia = limpiar_markdown(respuesta_texto)
        
        return SoporteResponse(respuesta=respuesta_limpia)
        
    except anthropic.APIError as e:
        raise HTTPException(status_code=500, detail=f"Error de API de Anthropic: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar consulta: {str(e)}")


@router.post("/ask/stream")
async def soporte_ask_stream(
    request: SoporteRequest,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint de streaming para soporte.
    Devuelve la respuesta en chunks usando Server-Sent Events (SSE).
    """
    
    nombre_pila = obtener_nombre_pila(current_user.nombre)
    messages = construir_mensajes(request, nombre_pila)
    
    # Obtener módulos disponibles para este usuario
    modulos_usuario = _obtener_modulos_usuario(current_user)
    
    # Construir system prompt con módulos del usuario
    system_prompt_final = SYSTEM_PROMPT.format(
        documentacion=DOCUMENTACION,
        nombre=nombre_pila,
        modulos_usuario=modulos_usuario
    )
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key de Anthropic no configurada")
    
    def generate():
        """Generador síncrono para streaming SSE."""
        try:
            client = anthropic.Anthropic(api_key=api_key)
            
            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=system_prompt_final,
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    # Limpiar markdown de cada chunk
                    texto_limpio = limpiar_markdown(text)
                    if texto_limpio:
                        yield f"data: {json.dumps({'text': texto_limpio})}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except anthropic.APIError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
