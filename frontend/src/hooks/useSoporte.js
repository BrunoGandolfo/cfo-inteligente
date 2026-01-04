/**
 * Hook para el chat de soporte AI
 * 
 * Maneja la comunicación con el endpoint de soporte,
 * el historial de mensajes y el estado de carga.
 */

import { useState, useCallback } from 'react';
import axiosClient from '../services/api/axiosClient';
import toast from 'react-hot-toast';

export function useSoporte() {
  const [loading, setLoading] = useState(false);
  const [mensajes, setMensajes] = useState([]);

  /**
   * Envía un mensaje al agente de soporte
   * @param {string} mensaje - Texto del mensaje del usuario
   * @returns {Promise<string|null>} - Respuesta del agente o null si hay error
   */
  const enviarMensaje = useCallback(async (mensaje) => {
    if (!mensaje.trim()) return null;

    // Agregar mensaje del usuario al historial
    const nuevoMensajeUsuario = { role: 'user', content: mensaje };
    setMensajes(prev => [...prev, nuevoMensajeUsuario]);
    
    setLoading(true);
    
    try {
      const { data } = await axiosClient.post('/api/soporte/ask', {
        mensaje,
        historial: mensajes
      });
      
      // Agregar respuesta del asistente al historial
      const respuestaAsistente = { role: 'assistant', content: data.respuesta };
      setMensajes(prev => [...prev, respuestaAsistente]);
      
      return data.respuesta;
    } catch (error) {
      console.error('Error en soporte:', error);
      
      // No mostrar toast para no duplicar feedback
      // toast.error('Error al contactar soporte');
      
      // Agregar mensaje de error amigable
      const mensajeError = { 
        role: 'assistant', 
        content: '😕 Ups, tuve un problema técnico. ¿Podés intentar de nuevo en unos segundos? Si sigue fallando, escribí a bgandolfo@cgmasociados.com' 
      };
      setMensajes(prev => [...prev, mensajeError]);
      
      return null;
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
