/**
 * Hook para el chat de soporte AI con streaming
 * 
 * Maneja la comunicación con el endpoint de soporte,
 * el historial de mensajes y el estado de carga.
 * Usa streaming para mostrar respuestas de a poco.
 */

import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { readSSEStream } from '../utils/sseHelper';

// Helper para delay
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

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
      const esSocio = localStorage.getItem('esSocio')?.toLowerCase() === 'true';
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
            historial: mensajes,
            es_socio: esSocio
          })
        }
      );

      if (!response.ok) {
        throw new Error(`Error ${response.status}`);
      }

      await readSSEStream(response.body, async ({ data }) => {
        if (data === '[DONE]') {
          return;
        }

        try {
          const parsed = JSON.parse(data);
          if (parsed.text) {
            setMensajes(prev => {
              const updated = [...prev];
              const lastIndex = updated.length - 1;
              updated[lastIndex] = {
                ...updated[lastIndex],
                content: updated[lastIndex].content + parsed.text
              };
              return [...updated];
            });
            await delay(20);
          }

          if (parsed.error) {
            console.error('Error del servidor:', parsed.error);
            toast.error('Error al procesar la consulta');
          }
        } catch {
          // Ignorar líneas que no son JSON válido
        }
      });
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
