/**
 * useReportGenerator Hook
 * 
 * Custom hook para generación de reportes PDF.
 * Maneja estado, loading, errores y descarga.
 * 
 * @author Sistema CFO Inteligente
 * @date Octubre 2025
 */

import { useState, useCallback } from 'react';
import { reportsClient } from '../services/api/reportsClient';

/**
 * Hook para generación de reportes.
 * 
 * @returns {Object} Estado y funciones
 */
export const useReportGenerator = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [reportMetadata, setReportMetadata] = useState(null);

  /**
   * Genera reporte PDF.
   * 
   * @param {Object} config - Configuración del reporte
   * @returns {Promise<void>}
   */
  const generateReport = useCallback(async (config) => {
    setIsGenerating(true);
    setProgress(0);
    setError(null);
    setReportMetadata(null);

    try {
      // Simular progreso (ya que no tenemos WebSocket aún)
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      // Generar reporte
      const result = await reportsClient.generateDynamicReport(config);

      clearInterval(progressInterval);
      setProgress(100);

      // Guardar metadata
      setReportMetadata({
        filename: result.filename,
        pages: result.pages,
        sizeKB: result.sizeKB,
        generationTime: result.generationTime,
        warnings: result.warnings
      });

      // Descargar PDF automáticamente
      const blob = result.blob;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename || 'Reporte_CFO.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      return result;

    } catch (err) {
      console.error('Error generando reporte:', err);
      setError(err.message || 'Error generando reporte');
      throw err;

    } finally {
      setIsGenerating(false);
    }
  }, []);

  /**
   * Preview de reporte (solo metadata, sin generar PDF).
   * 
   * @param {Object} config - Configuración del reporte
   * @returns {Promise<Object>}
   */
  const previewReport = useCallback(async (config) => {
    try {
      const metadata = await reportsClient.previewReport(config);
      return metadata;
    } catch (err) {
      console.error('Error en preview:', err);
      throw err;
    }
  }, []);

  /**
   * Reset del estado.
   */
  const reset = useCallback(() => {
    setIsGenerating(false);
    setProgress(0);
    setError(null);
    setReportMetadata(null);
  }, []);

  return {
    isGenerating,
    progress,
    error,
    reportMetadata,
    generateReport,
    previewReport,
    reset
  };
};

