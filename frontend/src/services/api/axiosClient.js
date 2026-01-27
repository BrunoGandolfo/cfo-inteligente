/**
 * Cliente Axios Centralizado
 * 
 * Configura interceptores para:
 * - Agregar token JWT a todas las requests
 * - Manejar errores 401 (redirigir a login)
 * 
 * @author Sistema CFO Inteligente
 * @date Diciembre 2025
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://cfo-inteligente-production.up.railway.app';

// Crear instancia de axios con configuración base
const axiosClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,  // 2 minutos para expedientes con muchos movimientos
  headers: {
    'Content-Type': 'application/json',
  },
});

// ═══════════════════════════════════════════════════════════════
// INTERCEPTOR DE REQUEST: Agregar token JWT
// ═══════════════════════════════════════════════════════════════

axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ═══════════════════════════════════════════════════════════════
// INTERCEPTOR DE RESPONSE: Manejar errores 401
// ═══════════════════════════════════════════════════════════════

axiosClient.interceptors.response.use(
  (response) => {
    // Respuesta exitosa, retornar sin cambios
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token inválido o expirado
      console.warn('Token inválido o expirado. Redirigiendo a login...');
      
      // Limpiar token del localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // Redirigir a login (si no estamos ya en login)
      if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default axiosClient;
export { API_BASE_URL };



