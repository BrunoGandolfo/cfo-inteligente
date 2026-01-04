/**
 * Hook para el chat de soporte AI con streaming
 * 
 * Maneja la comunicación con el endpoint de soporte,
 * el historial de mensajes y el estado de carga.
 * Usa streaming para mostrar respuestas de a poco.
 */

import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';

export function useSoporte() {
  const [loading, setLoading] = useState(false);
  const [mensajes, setMensajes] = useState([]);

  /**
   * Envía un mensaje al agente de soporte con streaming
   * @param {string} mensaje - Texto del mensaje del usuario
   */
  const enviarMensaje = useCallback(async (mensaje) => {
    if (!mensaje.trim()) return;

    // Agregar mensaje del usuario al historial
    const nuevoMensajeUsuario = { role: 'user', content: mensaje };
    setMensajes(prev => [...prev, nuevoMensajeUsuario]);
    
    // Agregar mensaje vacío del asistente que se irá llenando
    setMensajes(prev => [...prev, { role: 'assistant', content: '' }]);
    
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const apiUrl = import.meta.env.VITE_API_URL || 'https://cfo-inteligente-production.up.railway.app';
      
      const response = await fetch(
        `${apiUrl}/api/soporte/ask/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ 
            mensaje, 
            historial: mensajes 
          })
        }
      );

      if (!response.ok) {
        throw new Error(`Error ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ') && !line.includes('[DONE]')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.text) {
                // Actualizar el último mensaje (el del asistente)
                setMensajes(prev => {
                  const updated = [...prev];
                  const lastIndex = updated.length - 1;
                  updated[lastIndex] = {
                    ...updated[lastIndex],
                    content: updated[lastIndex].content + data.text
                  };
                  return updated;
                });
              }
              if (data.error) {
                console.error('Error del servidor:', data.error);
                toast.error('Error al procesar la consulta');
              }
            } catch (e) {
              // Ignorar líneas que no son JSON válido
            }
          }
        }
      }
    } catch (error) {
      console.error('Error en soporte:', error);
      
      // Actualizar el mensaje del asistente con error
      setMensajes(prev => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        updated[lastIndex] = {
          ...updated[lastIndex],
          content: '😕 Ups, tuve un problema técnico. ¿Podés intentar de nuevo en unos segundos? Si sigue fallando, escribí a bgandolfo@cgmasociados.com'
        };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  }, [mensajes]);

  /**
   * Limpia el historial de chat para empezar una nueva conversación
   */
  const limpiarChat = useCallback(() => {
    setMensajes([]);
  }, []);

  return {
    mensajes,
    loading,
    enviarMensaje,
    limpiarChat
  };
}

export default useSoporte;
