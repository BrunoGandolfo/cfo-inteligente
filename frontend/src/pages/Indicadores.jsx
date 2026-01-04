/**
 * Página de Indicadores Económicos de Uruguay.
 * 
 * Muestra UI, UR, IPC, BPC, inflación y cotizaciones de monedas.
 * Incluye calculadoras para honorarios, ITP, alquileres e IRPF.
 * Incluye buscador de legislación IMPO.
 */

import { useState } from 'react';
import PropTypes from 'prop-types';
import { ArrowLeft, RefreshCw, TrendingUp, Landmark, DollarSign, Percent } from 'lucide-react';
import { useIndicadores } from '../hooks/useIndicadores';
import IndicadorCard from '../components/indicadores/IndicadorCard';
import CalculadoraHonorarios from '../components/indicadores/CalculadoraHonorarios';
import CalculadoraITP from '../components/indicadores/CalculadoraITP';
import CalculadoraIRPF from '../components/indicadores/CalculadoraIRPF';
import BuscadorIMPO from '../components/indicadores/BuscadorIMPO';

// Formateo de números
const formatearIndicador = (valor, decimales = 4) => {
  if (valor === null || valor === undefined) return '-';
  return new Intl.NumberFormat('es-UY', {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  }).format(valor);
};

const formatearPesos = (valor) => {
  if (valor === null || valor === undefined) return '-';
  return `$ ${new Intl.NumberFormat('es-UY', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(valor)}`;
};

export default function Indicadores({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('indicadores');
  const { indicadores, loading, error, refetch } = useIndicadores();

  // Fecha de última actualización
  const fechaActualizacion = indicadores?.actualizado 
    ? new Date(indicadores.actualizado).toLocaleDateString('es-UY', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '-';

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col max-w-6xl mx-auto px-4 overflow-y-auto">
      {/* Botón volver */}
      <button
        onClick={() => onNavigate?.('dashboard')}
        className="flex items-center gap-2 text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 mb-3 transition-colors"
      >
        <ArrowLeft size={18} />
        <span className="text-sm">Volver al Dashboard</span>
      </button>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <BarChart3 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              Indicadores Económicos
            </h1>
            <p className="text-sm text-gray-500 dark:text-slate-400">
              Uruguay — {fechaActualizacion}
            </p>
          </div>
        </div>
        <button
          onClick={refetch}
          disabled={loading}
          className="flex items-center gap-2 text-sm bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 px-3 py-2 rounded-lg transition-colors text-gray-700 dark:text-slate-300 disabled:opacity-50"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Actualizar
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-gray-200 dark:border-slate-700">
        <button
          onClick={() => setActiveTab('indicadores')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'indicadores'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300'
          }`}
        >
          Indicadores
        </button>
        <button
          onClick={() => setActiveTab('calculadoras')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'calculadoras'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300'
          }`}
        >
          Calculadoras
        </button>
        <button
          onClick={() => setActiveTab('legislacion')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'legislacion'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300'
          }`}
        >
          Legislación
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && !indicadores && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      )}

      {/* Tab: Indicadores */}
      {activeTab === 'indicadores' && indicadores && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 pb-6">
          {/* UI */}
          <IndicadorCard
            titulo="Unidad Indexada (UI)"
            valor={`$ ${formatearIndicador(indicadores.ui?.valor, 4)}`}
            subtitulo={`Actualización diaria — ${indicadores.ui?.fuente || ''}`}
            icono={TrendingUp}
            colorBorde="border-amber-500"
            colorIcono="text-amber-500"
          />

          {/* UR */}
          <IndicadorCard
            titulo="Unidad Reajustable (UR)"
            valor={`$ ${formatearIndicador(indicadores.ur?.valor, 2)}`}
            subtitulo={`Actualización mensual — ${indicadores.ur?.fuente || ''}`}
            icono={TrendingUp}
            colorBorde="border-cyan-500"
            colorIcono="text-cyan-500"
          />

          {/* BPC */}
          <IndicadorCard
            titulo="BPC (Base Prestaciones)"
            valor={`$ ${formatearIndicador(indicadores.bpc?.valor, 0)}`}
            subtitulo={`Actualización anual — ${indicadores.bpc?.fuente || ''}`}
            icono={Landmark}
            colorBorde="border-rose-500"
            colorIcono="text-rose-500"
          />

          {/* Inflación */}
          <IndicadorCard
            titulo="Inflación Anual"
            valor={`${formatearIndicador(indicadores.inflacion?.valor, 2)} %`}
            subtitulo={`Últimos 12 meses — ${indicadores.inflacion?.fuente || ''}`}
            icono={Percent}
            colorBorde="border-red-500"
            colorIcono="text-red-500"
          />

          {/* USD */}
          <IndicadorCard
            titulo="Dólar USD"
            valor={`C: ${formatearPesos(indicadores.cotizaciones?.usd?.compra)} / V: ${formatearPesos(indicadores.cotizaciones?.usd?.venta)}`}
            subtitulo="DolarApi — Tiempo real"
            icono={DollarSign}
            colorBorde="border-green-500"
            colorIcono="text-green-500"
          />

          {/* EUR */}
          <IndicadorCard
            titulo="Euro EUR"
            valor={`C: ${formatearPesos(indicadores.cotizaciones?.eur?.compra)} / V: ${formatearPesos(indicadores.cotizaciones?.eur?.venta)}`}
            subtitulo="DolarApi — Tiempo real"
            icono={DollarSign}
            colorBorde="border-blue-500"
            colorIcono="text-blue-500"
          />

          {/* BRL */}
          <IndicadorCard
            titulo="Real BRL"
            valor={`C: ${formatearPesos(indicadores.cotizaciones?.brl?.compra)} / V: ${formatearPesos(indicadores.cotizaciones?.brl?.venta)}`}
            subtitulo="DolarApi — Tiempo real"
            icono={DollarSign}
            colorBorde="border-orange-500"
            colorIcono="text-orange-500"
          />
        </div>
      )}

      {/* Tab: Calculadoras */}
      {activeTab === 'calculadoras' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 pb-6">
          <CalculadoraHonorarios valorUR={indicadores?.ur?.valor || 1841.56} />
          <CalculadoraITP />
          <CalculadoraIRPF valorUI={indicadores?.ui?.valor || 6.4243} />
        </div>
      )}

      {/* Tab: Legislación */}
      {activeTab === 'legislacion' && (
        <div className="pb-6">
          <BuscadorIMPO />
        </div>
      )}
    </div>
  );
}

Indicadores.propTypes = {
  onNavigate: PropTypes.func,
};
