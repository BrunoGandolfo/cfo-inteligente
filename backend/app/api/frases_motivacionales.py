from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.core.logger import get_logger
from app.models.usuario import Usuario
import anthropic
from app.core.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/api/frases", tags=["frases"])

PERFILES = {
    "kblanco@grupoconexion.uy": {
        "nombre": "Karina",
        "perfil": "La alegría del estudio. Siempre con una sonrisa. Le encanta el baile y todo lo relacionado al aire. Genera una energía hermosa.",
        "tono": "HABLARLE DIRECTO usando 'vos sos', 'qué linda', tuteo rioplatense. SIEMPRE incluir un pequeño poema de 2-3 versos dedicado a ella. Celebrar su alegría y energía."
    },
    "naraujo@grupoconexion.uy": {
        "nombre": "Nicolás", 
        "perfil": "Contador, ex jugador de básquetbol. Hincha de Independiente básquetbol. Muy querido por las clientas.",
        "tono": "HABLARLE DIRECTO usando tuteo rioplatense. Referencias a básquet o números."
    },
    "gferrari@grupoconexion.uy": {
        "nombre": "Gerardo",
        "perfil": "Abogado muy apuesto. Morocho de ojos verdes. Musculoso. Escudoso. Encantador y conquistador. Muy divertido aunque parece serio.",
        "tono": "HABLARLE DIRECTO alabando su belleza: 'qué lindo estás', 'esos ojos verdes', 'morocho encantador', 'qué musculoso'. Halagos directos con humor."
    },
    "bgandolfo@cgmasociados.com": {
        "nombre": "Bruno",
        "perfil": "CFO y Partner. Apasionado por la tecnología y los sistemas financieros. Fanático de la filosofía estoica.",
        "tono": "HABLARLE DIRECTO con tuteo rioplatense. Frases inspiradas en estoicos: Marco Aurelio, Séneca, Epicteto. Reflexiones sobre control, disciplina, virtud y aceptación. Motivar con sabiduría estoica aplicada al trabajo."
    }
}

@router.get("/motivacional")
async def get_frase_motivacional(
    current_user: Usuario = Depends(get_current_user)
):
    perfil = PERFILES.get(current_user.email.lower())
    
    if not perfil:
        return {"frase": "¡A seguir registrando con excelencia!"}
    
    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        
        prompt = f"""Genera UNA frase motivacional corta (máximo 15 palabras) para {perfil['nombre']}.

PERFIL: {perfil['perfil']}
TONO: {perfil['tono']}

REGLAS:
- NO inventes datos personales que no estén en el perfil
- NO menciones nombres de familiares o datos que no tengas
- Solo usa la información del perfil
- Que sea motivacional para registrar operaciones financieras
- Puede ser graciosa o inspiradora según el tono

Responde SOLO con la frase, sin comillas ni explicación."""

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        frase = response.content[0].text.strip()
        return {"frase": frase}
        
    except Exception as e:
        logger.error(f"Error generando frase: {e}")
        return {"frase": "¡A seguir registrando con excelencia!"}


