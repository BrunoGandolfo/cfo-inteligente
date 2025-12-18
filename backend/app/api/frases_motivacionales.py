from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.models.usuario import Usuario
import anthropic
import os

router = APIRouter(prefix="/api/frases", tags=["frases"])

PERFILES = {
    "kblanco@grupoconexion.uy": {
        "nombre": "Karina",
        "perfil": "Persona muy alegre que le gusta bailar zumba. Siempre está con una sonrisa. Genera una hermosa energía en el estudio.",
        "tono": "alegre, positivo, con energía"
    },
    "naraujo@grupoconexion.uy": {
        "nombre": "Nicolás", 
        "perfil": "Contador, ex jugador de básquetbol (ya juega poco). Hincha de Independiente básquetbol. Muy querido por las clientas.",
        "tono": "amigable, referencias a básquet o números"
    },
    "gferrari@grupoconexion.uy": {
        "nombre": "Gerardo",
        "perfil": "Abogado que parece serio pero es divertido. Le encanta el derecho y las frases en latín jurídico.",
        "tono": "profesional con humor sutil, frases latín jurídico"
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
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
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
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        frase = response.content[0].text.strip()
        return {"frase": frase}
        
    except Exception as e:
        print(f"Error generando frase: {e}")
        return {"frase": "¡A seguir registrando con excelencia!"}


