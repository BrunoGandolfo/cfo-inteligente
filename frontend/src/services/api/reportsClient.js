/**
 * Reports API Client
 * 
 * Cliente HTTP para endpoints de reportes.
 * 
 * @author Sistema CFO Inteligente
 * @date Octubre 2025
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Cliente de API de reportes.
 */
export const reportsClient = {
  /**
   * Genera reporte PDF dinámico.
   * 
   * @param {Object} config - Configuración del reporte
   * @param {Object} config.period - Configuración de período
   * @param {Object} config.comparison - Configuración de comparación (opcional)
   * @param {Object} config.options - Opciones del reporte
   * @returns {Promise<Object>} Blob del PDF + metadata
   */
  async generateDynamicReport(config) {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/reports/pdf/dinamico`,
        config,
        {
          responseType: 'blob', // Importante para PDF
          timeout: 120000, // 2 minutos timeout
          headers: { 'Content-Type': 'application/json' }
        }
      );

      // Extraer metadata de headers
      const metadata = {
        filename: this._getFilenameFromHeaders(response.headers),
        pages: parseInt(response.headers['x-report-pages'] || '0', 10),
        sizeKB: parseFloat(response.headers['x-report-size-kb'] || '0'),
        generationTime: parseFloat(response.headers['x-generation-time'] || '0'),
        warnings: response.headers['x-warnings']?.split(';').filter(Boolean) || []
      };

      return {
        blob: response.data,
        ...metadata
      };

    } catch (error) {
      console.error('Error generando reporte:', error);
      throw this._handleError(error);
    }
  },

  /**
   * Preview de reporte (solo metadata).
   * 
   * @param {Object} config - Configuración del reporte
   * @returns {Promise<Object>} Metadata del reporte
   */
  async previewReport(config) {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/reports/preview`,
        config
      );
      return response.data;

    } catch (error) {
      console.error('Error en preview:', error);
      throw this._handleError(error);
    }
  },

  /**
   * Health check del servicio de reportes.
   * 
   * @returns {Promise<Object>} Estado del servicio
   */
  async healthCheck() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/reports/health`);
      return response.data;

    } catch (error) {
      console.error('Error en health check:', error);
      throw this._handleError(error);
    }
  },

  /**
   * Extrae filename de headers Content-Disposition.
   * 
   * @private
   */
  _getFilenameFromHeaders(headers) {
    const disposition = headers['content-disposition'];
    if (disposition) {
      const filenameMatch = disposition.match(/filename="(.+)"/);
      if (filenameMatch) {
        return filenameMatch[1];
      }
    }
    return `Reporte_CFO_${new Date().toISOString().split('T')[0]}.pdf`;
  },

  /**
   * Maneja errores de API.
   * 
   * @private
   */
  _handleError(error) {
    if (error.response) {
      // Error de servidor
      const detail = error.response.data?.detail || error.response.statusText;
      return new Error(`Error ${error.response.status}: ${detail}`);
    } else if (error.request) {
      // Sin respuesta
      return new Error('Sin respuesta del servidor. Verifica tu conexión.');
    } else {
      // Error de configuración
      return new Error(error.message || 'Error desconocido');
    }
  }
};

