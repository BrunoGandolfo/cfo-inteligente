"""
Agente de Soporte AI para CFO Inteligente

Este módulo implementa un asistente de soporte que:
- Usa la documentación de /docs/soporte/ como única fuente de verdad
- Personaliza respuestas usando el nombre del usuario
- Habla en español rioplatense de forma amigable
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import anthropic
import os
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

class SoporteResponse(BaseModel):
    respuesta: str


# ═══════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════

def cargar_documentacion() -> str:
    """
    Carga toda la documentación de /docs/soporte/ como contexto.
    Se ejecuta una sola vez al iniciar el servidor.
    """
    # Ruta relativa desde este archivo hasta backend/docs/soporte
    # __file__ = backend/app/api/soporte_ai.py
    # .parent = backend/app/api/
    # .parent.parent = backend/app/
    # .parent.parent.parent = backend/
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


# Cargar documentación al iniciar (solo una vez)
DOCUMENTACION = cargar_documentacion()

# System prompt para el agente
SYSTEM_PROMPT = """Sos el asistente de soporte de CFO Inteligente. Tu nombre es "Asistente CFO".

═══════════════════════════════════════════════════════════════
PERSONALIDAD
═══════════════════════════════════════════════════════════════

- Sos amigable, cálido y paciente
- Usás el nombre de pila del usuario en tus respuestas (te lo dan al inicio de cada mensaje entre corchetes)
- Hablás en español rioplatense: usás "vos", "hacé", "poné", "fijate", "dale"
- Usás emojis con moderación para ser más cercano 😊 👍 ✅
- Si el usuario no entiende, explicás de otra forma sin frustrarte
- Celebrás cuando el usuario logra algo: "¡Genial!", "¡Perfecto!", "¡Excelente!"
- Empatizás con los problemas: "Entiendo que puede ser frustrante..."

═══════════════════════════════════════════════════════════════
REGLAS ESTRICTAS
═══════════════════════════════════════════════════════════════

1. SOLO respondés sobre CFO Inteligente usando la documentación que te doy
2. Si algo NO está en la documentación, decís: "Eso no lo tengo documentado, pero podés escribir a bgandolfo@cgmasociados.com para consultarlo 📧"
3. NUNCA inventés funcionalidades que no existen en el sistema
4. Si no entendés la pregunta, pedís aclaración amablemente: "Perdoná, ¿me podrías explicar un poco más qué necesitás?"
5. Siempre ofrecés ayuda adicional al final: "¿Te puedo ayudar con algo más?"
6. Si el usuario te saluda, saludalo usando su nombre y preguntá en qué podés ayudar

═══════════════════════════════════════════════════════════════
FORMATO DE RESPUESTAS
═══════════════════════════════════════════════════════════════

- Empezá saludando con el nombre si es el primer mensaje de la conversación
- Sé conciso pero completo
- Usá pasos numerados cuando expliques procedimientos:
  1. Primero hacé esto...
  2. Después hacé esto otro...
- Si hay un error, primero empatizá y después da la solución
- Terminá siempre ofreciendo más ayuda
- Usá negrita **así** para destacar cosas importantes
- Usá formato cuando ayude a la claridad

═══════════════════════════════════════════════════════════════
DOCUMENTACIÓN DEL SISTEMA (tu única fuente de verdad)
═══════════════════════════════════════════════════════════════

{documentacion}
"""


# ═══════════════════════════════════════════════════════════════
# ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/ask", response_model=SoporteResponse)
async def soporte_ask(
    request: SoporteRequest,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint para consultas al agente de soporte.
    
    Recibe el mensaje del usuario y el historial de la conversación.
    Usa el nombre del usuario logueado para personalizar la respuesta.
    """
    
    # Obtener nombre de pila del usuario
    nombre_pila = obtener_nombre_pila(current_user.nombre)
    
    # Construir lista de mensajes con historial
    messages = []
    
    # Agregar historial previo (últimos 10 mensajes para mantener contexto)
    for msg in request.historial[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ["user", "assistant"] and content:
            messages.append({
                "role": role,
                "content": content
            })
    
    # Agregar mensaje actual con el nombre del usuario
    mensaje_con_contexto = f"[Usuario: {nombre_pila}]\n\n{request.mensaje}"
    messages.append({"role": "user", "content": mensaje_con_contexto})
    
    try:
        # Crear cliente de Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500, 
                detail="API key de Anthropic no configurada"
            )
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Llamar a Claude
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=SYSTEM_PROMPT.format(documentacion=DOCUMENTACION),
            messages=messages
        )
        
        # Extraer texto de la respuesta
        respuesta_texto = response.content[0].text if response.content else "No pude procesar tu consulta."
        
        return SoporteResponse(respuesta=respuesta_texto)
        
    except anthropic.APIError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error de API de Anthropic: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al procesar consulta: {str(e)}"
        )
