/**
 * ReportGeneratorModal Component
 * 
 * Modal completo para configurar y generar reportes PDF.
 * 
 * @author Sistema CFO Inteligente
 * @date Octubre 2025
 */

import React, { useState } from 'react';
import { useReportGenerator } from '../../hooks/useReportGenerator';
import { DateRangePicker } from '../ui/DateRangePicker';
import { ProgressBar } from '../ui/ProgressBar';

export const ReportGeneratorModal = ({ isOpen, onClose }) => {
  // Hook de generación
  const {
    isGenerating,
    progress,
    error,
    reportMetadata,
    generateReport,
    previewReport,
    reset
  } = useReportGenerator();

  // Estado del formulario
  const [periodType, setPeriodType] = useState('mes_actual');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [comparisonEnabled, setComparisonEnabled] = useState(false);
  const [comparisonType, setComparisonType] = useState('periodo_anterior');
  const [includeProjections, setIncludeProjections] = useState(true);
  const [includeAIInsights, setIncludeAIInsights] = useState(true);
  const [includeScenarios, setIncludeScenarios] = useState(false);
  const [format, setFormat] = useState('ejecutivo');
  const [palette, setPalette] = useState('moderna_2024');

  const handleGenerate = async () => {
    const config = {
      period: {
        tipo: periodType,
        ...(periodType === 'custom' && {
          fecha_inicio: customStartDate,
          fecha_fin: customEndDate
        })
      },
      comparison: comparisonEnabled ? {
        activo: true,
        tipo: comparisonType
      } : null,
      options: {
        incluir_proyecciones: includeProjections,
        incluir_insights_ia: includeAIInsights,
        incluir_escenarios: includeScenarios,
        formato: format,
        paleta: palette
      }
    };

    try {
      await generateReport(config);
    } catch (err) {
      console.error('Error:', err);
    }
  };

  const handlePreview = async () => {
    const config = {
      period: {
        tipo: periodType,
        ...(periodType === 'custom' && {
          fecha_inicio: customStartDate,
          fecha_fin: customEndDate
        })
      },
      comparison: comparisonEnabled ? {
        activo: true,
        tipo: comparisonType
      } : null,
      options: {
        incluir_proyecciones: includeProjections,
        incluir_insights_ia: includeAIInsights,
        incluir_escenarios: includeScenarios,
        formato: format,
        paleta: palette
      }
    };

    try {
      const metadata = await previewReport(config);
      alert(
        `Vista Previa del Reporte\n\n` +
        `Archivo: ${metadata.metadata?.filename || 'Reporte_CFO.pdf'}\n` +
        `Páginas estimadas: ${metadata.metadata?.pages || 'N/A'}\n` +
        `Período: ${metadata.metadata?.period_label || periodType}\n` +
        `Comparación: ${metadata.metadata?.has_comparison ? 'Sí' : 'No'}\n` +
        `Proyecciones: ${metadata.metadata?.has_projections ? 'Sí' : 'No'}\n` +
        `Insights IA: ${metadata.metadata?.has_ai_insights ? 'Sí' : 'No'}`
      );
    } catch (err) {
      console.error('Error en preview:', err);
      alert('Error obteniendo vista previa: ' + (err.message || 'Error desconocido'));
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" onClick={handleClose} />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="sticky top-0 bg-white dark:bg-gray-800 border-b dark:border-gray-700 px-6 py-4 flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Generar Reporte CFO
            </h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Período */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Período del Reporte
              </label>
              <select
                value={periodType}
                onChange={(e) => setPeriodType(e.target.value)}
                disabled={isGenerating}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="mes_actual">Mes Actual</option>
                <option value="mes_anterior">Mes Anterior</option>
                <option value="trimestre_actual">Trimestre Actual</option>
                <option value="semestre_actual">Semestre Actual</option>
                <option value="anio_2025">Año 2025</option>
                <option value="custom">Personalizado</option>
              </select>

              {periodType === 'custom' && (
                <div className="mt-4">
                  <DateRangePicker
                    startDate={customStartDate}
                    endDate={customEndDate}
                    onStartDateChange={setCustomStartDate}
                    onEndDateChange={setCustomEndDate}
                    disabled={isGenerating}
                  />
                </div>
              )}
            </div>

            {/* Comparación */}
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={comparisonEnabled}
                  onChange={(e) => setComparisonEnabled(e.target.checked)}
                  disabled={isGenerating}
                  className="w-4 h-4 text-blue-600 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Comparar con período anterior
                </span>
              </label>

              {comparisonEnabled && (
                <select
                  value={comparisonType}
                  onChange={(e) => setComparisonType(e.target.value)}
                  disabled={isGenerating}
                  className="mt-2 w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="periodo_anterior">Período Anterior</option>
                  <option value="mismo_periodo_año_pasado">Mismo Período Año Pasado</option>
                </select>
              )}
            </div>

            {/* Opciones */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Contenido del Reporte</h3>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={includeProjections}
                  onChange={(e) => setIncludeProjections(e.target.checked)}
                  disabled={isGenerating}
                  className="w-4 h-4 text-blue-600 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Incluir proyecciones con regresión lineal
                </span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={includeAIInsights}
                  onChange={(e) => setIncludeAIInsights(e.target.checked)}
                  disabled={isGenerating}
                  className="w-4 h-4 text-blue-600 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Incluir insights generados por Claude Sonnet 4.5
                </span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={includeScenarios}
                  onChange={(e) => setIncludeScenarios(e.target.checked)}
                  disabled={isGenerating}
                  className="w-4 h-4 text-blue-600 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Incluir escenarios de estrés (experimental)
                </span>
              </label>
            </div>

            {/* Formato */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Formato
                </label>
                <select
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  disabled={isGenerating}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ejecutivo">Ejecutivo (10 páginas)</option>
                  <option value="completo">Completo (20+ páginas)</option>
                  <option value="resumido">Resumido (5 páginas)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Paleta
                </label>
                <select
                  value={palette}
                  onChange={(e) => setPalette(e.target.value)}
                  disabled={isGenerating}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="moderna_2024">Moderna 2024</option>
                  <option value="institucional">Institucional</option>
                </select>
              </div>
            </div>

            {/* Progress */}
            {isGenerating && (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <ProgressBar
                  progress={progress}
                  label="Generando reporte PDF..."
                />
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                  Este proceso puede tomar 30-60 segundos
                </p>
              </div>
            )}

            {/* Success */}
            {reportMetadata && !isGenerating && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-800 font-semibold mb-2">
                  ✓ Reporte generado exitosamente
                </p>
                <div className="text-sm text-green-700 space-y-1">
                  <p>Archivo: {reportMetadata.filename}</p>
                  <p>Páginas: {reportMetadata.pages}</p>
                  <p>Tamaño: {reportMetadata.sizeKB?.toFixed(1)} KB</p>
                  <p>Tiempo: {reportMetadata.generationTime?.toFixed(2)}s</p>
                </div>
              </div>
            )}

            {/* Error */}
            {error && !isGenerating && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800 font-semibold mb-1">
                  Error generando reporte
                </p>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="sticky bottom-0 bg-gray-50 dark:bg-gray-900 border-t dark:border-gray-700 px-6 py-4 flex justify-end space-x-3">
            <button
              onClick={handleClose}
              disabled={isGenerating}
              className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition disabled:opacity-50"
            >
              Cerrar
            </button>
            <button
              onClick={handlePreview}
              disabled={isGenerating}
              className="px-6 py-2 border border-blue-600 text-blue-600 dark:border-blue-500 dark:text-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition disabled:opacity-50"
            >
              Vista Previa
            </button>
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? 'Generando...' : 'Generar Reporte'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

