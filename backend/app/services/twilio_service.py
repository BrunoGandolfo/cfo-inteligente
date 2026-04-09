"""
Servicio para envío de notificaciones via WhatsApp (Twilio).
"""

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import json
from typing import List, Dict, Any, Optional

from app.core.config import Settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Configuración Twilio (desde variables de entorno)
TWILIO_ACCOUNT_SID = Settings().twilio_account_sid
TWILIO_AUTH_TOKEN = Settings().twilio_auth_token
TWILIO_WHATSAPP_FROM = Settings().twilio_whatsapp_from

# Cliente Twilio (lazy initialization)
_twilio_client: Optional[Client] = None


def _get_twilio_client() -> Optional[Client]:
    """Obtiene el cliente Twilio, inicializándolo si es necesario."""
    global _twilio_client
    
    if _twilio_client is None:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            logger.warning("Credenciales Twilio no configuradas")
            return None
        
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("Cliente Twilio inicializado")
    
    return _twilio_client


def enviar_whatsapp(
    numero_destino: str,
    mensaje: str
) -> Dict[str, Any]:
    """
    Envía un mensaje de WhatsApp.
    
    Args:
        numero_destino: Número en formato internacional (ej: +59899123456)
        mensaje: Texto del mensaje
        
    Returns:
        Dict con resultado: {"exito": bool, "sid": str, "error": str}
    """
    client = _get_twilio_client()
    
    if client is None:
        return {"exito": False, "sid": None, "error": "Twilio no configurado"}
    
    # Formatear números para WhatsApp
    whatsapp_to = f"whatsapp:{numero_destino}" if not numero_destino.startswith("whatsapp:") else numero_destino
    
    try:
        message = client.messages.create(
            body=mensaje,
            from_=TWILIO_WHATSAPP_FROM,
            to=whatsapp_to
        )
        
        logger.info(f"WhatsApp enviado a {numero_destino} - SID: {message.sid}")
        return {"exito": True, "sid": message.sid, "error": None}
        
    except TwilioRestException as e:
        logger.error(f"Error Twilio: {e}")
        return {"exito": False, "sid": None, "error": str(e)}


def generar_mensaje_inteligente(movimientos: List[Dict[str, Any]]) -> Optional[str]:
    """
    Genera mensaje de notificación usando Claude.
    
    Args:
        movimientos: Lista de movimientos de expedientes
        
    Returns:
        Mensaje generado por Claude o None si falla
    """
    try:
        from app.services.ai.claude_client import ClaudeClient
        
        client = ClaudeClient()
        
        prompt = f"""Eres el asistente CFO Inteligente de un estudio jurídico-contable en Uruguay.

Analiza estos movimientos de expedientes judiciales y genera un mensaje de WhatsApp conciso (máximo 500 caracteres) para notificar a los socios.

El mensaje debe:
1. Empezar con 🔔 CFO Inteligente
2. Ser profesional pero cercano
3. Destacar lo más importante (decretos, vencimientos, cambios de estado)
4. Si hay vencimientos próximos, alertar con ⚠️
5. No listar todos los movimientos, resumir lo relevante

Movimientos:
{json.dumps(movimientos, default=str, ensure_ascii=False)}

Genera SOLO el mensaje, sin explicaciones adicionales."""
        
        response = client.complete(
            prompt=prompt,
            temperature=0.3,
            max_tokens=300,
            timeout=15
        )
        
        mensaje = response.strip()
        
        # Validar que no exceda 500 caracteres (límite WhatsApp recomendado)
        if len(mensaje) > 500:
            mensaje = mensaje[:497] + "..."
        
        logger.info(f"✅ Mensaje generado con Claude ({len(mensaje)} caracteres)")
        return mensaje
        
    except Exception as e:
        logger.error(f"❌ Error generando mensaje con Claude: {e}")
        return None


def notificar_movimientos_expedientes(
    movimientos: List[Dict[str, Any]],
    numero_destino: str
) -> Dict[str, Any]:
    """
    Envía notificación de nuevos movimientos de expedientes.
    
    Args:
        movimientos: Lista de movimientos (de obtener_movimientos_sin_notificar)
        numero_destino: Número WhatsApp del socio
        
    Returns:
        Dict con resumen de envío
    """
    if not movimientos:
        return {"enviados": 0, "mensaje": "Sin movimientos pendientes"}
    
    # Intentar generar mensaje inteligente con Claude
    mensaje = generar_mensaje_inteligente(movimientos)
    
    # Si Claude falla, usar template original
    if not mensaje:
        logger.info("📝 Usando template original (Claude no disponible)")
        # Agrupar por expediente
        por_expediente = {}
        for mov in movimientos:
            iue = mov["iue"]
            if iue not in por_expediente:
                por_expediente[iue] = {
                    "caratula": mov["caratula"],
                    "movimientos": []
                }
            por_expediente[iue]["movimientos"].append(mov)
        
        # Construir mensaje
        lineas = ["🔔 *CFO Inteligente - Nuevos Movimientos*\n"]
        
        for iue, data in por_expediente.items():
            caratula_corta = (data["caratula"][:50] + "...") if data["caratula"] and len(data["caratula"]) > 50 else data["caratula"]
            lineas.append(f"📁 *{iue}*")
            lineas.append(f"   {caratula_corta}")
            
            for mov in data["movimientos"][:3]:  # Máximo 3 movimientos por expediente
                fecha = mov["fecha"].strftime("%d/%m") if mov["fecha"] else "S/F"
                tipo = mov["tipo"] or "Movimiento"
                decreto = f" - {mov['decreto']}" if mov["decreto"] else ""
                lineas.append(f"   • {fecha}: {tipo}{decreto}")
            
            if len(data["movimientos"]) > 3:
                lineas.append(f"   ... y {len(data['movimientos']) - 3} más")
            
            lineas.append("")
        
        mensaje = "\n".join(lineas)
    
    # Enviar
    resultado = enviar_whatsapp(numero_destino, mensaje)
    
    # Calcular estadísticas
    por_expediente = {}
    for mov in movimientos:
        iue = mov["iue"]
        if iue not in por_expediente:
            por_expediente[iue] = {"movimientos": []}
        por_expediente[iue]["movimientos"].append(mov)
    
    resultado["total_movimientos"] = len(movimientos)
    resultado["total_expedientes"] = len(por_expediente)
    
    return resultado


def enviar_test(numero_destino: str) -> Dict[str, Any]:
    """Envía mensaje de prueba para verificar configuración."""
    mensaje = "✅ *CFO Inteligente*\n\nConexión con WhatsApp verificada correctamente."
    return enviar_whatsapp(numero_destino, mensaje)


def notificar_a_todos_los_socios(movimientos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Envía notificación de movimientos a todos los socios configurados.
    
    Lee los números de la variable TWILIO_NOTIFY_NUMBERS (separados por coma).
    
    Returns:
        Dict con resumen: enviados_ok, enviados_error, detalles
    """
    numeros_str = Settings().twilio_notify_numbers
    
    if not numeros_str:
        logger.warning("⚠️ TWILIO_NOTIFY_NUMBERS no configurado")
        return {"enviados_ok": 0, "enviados_error": 0, "detalles": []}
    
    numeros = [n.strip() for n in numeros_str.split(",") if n.strip()]
    
    if not numeros:
        return {"enviados_ok": 0, "enviados_error": 0, "detalles": []}
    
    enviados_ok = 0
    enviados_error = 0
    detalles = []
    
    for numero in numeros:
        resultado = notificar_movimientos_expedientes(movimientos, numero)
        
        if resultado.get("exito"):
            enviados_ok += 1
            detalles.append({"numero": numero, "exito": True, "sid": resultado.get("sid")})
        else:
            enviados_error += 1
            detalles.append({"numero": numero, "exito": False, "error": resultado.get("error")})
    
    logger.info(f"📱 Notificaciones enviadas: {enviados_ok} OK, {enviados_error} errores")
    
    return {
        "enviados_ok": enviados_ok,
        "enviados_error": enviados_error,
        "total_numeros": len(numeros),
        "detalles": detalles
    }

