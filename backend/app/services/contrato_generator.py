"""
Servicio para generar contratos DOCX completados.
Reemplaza placeholders en documentos DOCX con valores proporcionados.
"""
from docx import Document
from io import BytesIO
import json
import re
import logging

logger = logging.getLogger(__name__)


class ContratoGenerator:
    """Genera contratos DOCX reemplazando placeholders con valores"""
    
    def __init__(self):
        logger.info("ContratoGenerator inicializado")
    
    def generar(self, contenido_docx: bytes, campos_editables: dict, valores: dict) -> bytes:
        try:
            doc = Document(BytesIO(contenido_docx))
            
            campos_ordenados = sorted(
                campos_editables.get('campos', []), 
                key=lambda x: x.get('orden', 999)
            )
            
            logger.info(f"ContratoGenerator: Procesando {len(campos_ordenados)} campos en orden")
            
            for campo in campos_ordenados:
                campo_id = campo.get('id')
                placeholder = campo.get('placeholder_original', '[___]')
                valor = valores.get(campo_id, '')
                
                if not valor:
                    continue
                
                reemplazado = self._reemplazar_primera_ocurrencia(doc, placeholder, valor)
                
                if reemplazado:
                    logger.debug(f"Campo '{campo_id}': '{placeholder}' -> '{valor[:20]}...'")
                else:
                    logger.warning(f"Campo '{campo_id}': placeholder '{placeholder}' no encontrado")
            
            output = BytesIO()
            doc.save(output)
            output.seek(0)
            resultado = output.read()
            
            logger.info(f"ContratoGenerator: Documento generado ({len(resultado)} bytes)")
            return resultado
            
        except Exception as e:
            logger.error(f"ContratoGenerator: Error generando documento: {e}", exc_info=True)
            raise
    
    def _reemplazar_primera_ocurrencia(self, doc, placeholder: str, valor: str) -> bool:
        for paragraph in doc.paragraphs:
            if placeholder in paragraph.text:
                texto_nuevo = paragraph.text.replace(placeholder, valor, 1)
                paragraph.clear()
                paragraph.add_run(texto_nuevo)
                return True
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if placeholder in paragraph.text:
                            texto_nuevo = paragraph.text.replace(placeholder, valor, 1)
                            paragraph.clear()
                            paragraph.add_run(texto_nuevo)
                            return True
        
        return False
