import { useState } from 'react';
import MetricsGrid from '../components/metrics/MetricsGrid';
import OperationsTable from '../components/operations/OperationsTable';
import OperationDetails from '../components/operations/OperationDetails';
import ModalIngreso from '../components/ModalIngreso';
import ModalGasto from '../components/ModalGasto';
import ModalRetiro from '../components/ModalRetiro';
import ModalDistribucion from '../components/ModalDistribucion';
import { useMetrics } from '../hooks/useMetrics';
import { formatMoney } from '../utils/formatters';
import Button from '../components/ui/Button';
import ChartsSection from '../components/charts/ChartsSection';
import { useOperations } from '../hooks/useOperations';
import { useChartData } from '../hooks/useChartData';
import ActiveFilters from '../components/filters/ActiveFilters';

function Dashboard() {
  const [showIngreso, setShowIngreso] = useState(false);
  const [showGasto, setShowGasto] = useState(false);
  const [showRetiro, setShowRetiro] = useState(false);
  const [showDistrib, setShowDistrib] = useState(false);
  const [loadingIngreso, setLoadingIngreso] = useState(false);
  const [loadingGasto, setLoadingGasto] = useState(false);
  const [loadingRetiro, setLoadingRetiro] = useState(false);
  const [loadingDistrib, setLoadingDistrib] = useState(false);
  const [detailOp, setDetailOp] = useState(null);

  const { loading, metricas, filtros, refreshKey } = useMetrics();
  const { operacionesAll, refetch } = useOperations(refreshKey);
  const { operaciones: chartData, loading: chartLoading } = useChartData();

  if (loading) {
    return <div className="min-h-screen bg-gray-50 dark:bg-slate-950 flex items-center justify-center text-gray-600 dark:text-slate-200">Cargando...</div>;
  }

  const moneda = metricas?.ingresos?.moneda || 'UYU';
  const ingresosVal = metricas?.ingresos?.valor || 0;
  const gastosVal = metricas?.gastos?.valor || 0;
  const margenOperativo = typeof metricas?.rentabilidad === 'number' ? metricas.rentabilidad.toFixed(2) : '0.00';
  const areaLider = metricas?.area_lider || null;

  return (
    <>
      <MetricsGrid
        ingresos={formatMoney(ingresosVal, moneda)}
        gastos={formatMoney(gastosVal, moneda)}
        margenOperativo={margenOperativo}
        areaLider={areaLider}
      />

      <ActiveFilters />

      <ChartsSection operaciones={chartData || []} />

      <section className="px-6 mb-8">
        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-5">Registrar Operación</h2>
          <div className="grid grid-cols-4 gap-4">
            <button
              onClick={() => setShowIngreso(true)}
              disabled={loadingIngreso}
              className="group relative overflow-hidden bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20 border-2 border-emerald-400 dark:border-emerald-600 rounded-xl p-6 hover:shadow-2xl hover:scale-105 hover:border-emerald-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="flex flex-col items-center justify-center text-center space-y-3">
                <div className="w-12 h-12 bg-emerald-500 dark:bg-emerald-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">
                  {loadingIngreso ? 'Procesando...' : 'Ingreso'}
                </span>
              </div>
            </button>

            <button
              onClick={() => setShowGasto(true)}
              disabled={loadingGasto}
              className="group relative overflow-hidden bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-2 border-red-400 dark:border-red-600 rounded-xl p-6 hover:shadow-2xl hover:scale-105 hover:border-red-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="flex flex-col items-center justify-center text-center space-y-3">
                <div className="w-12 h-12 bg-red-500 dark:bg-red-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                  </svg>
                </div>
                <span className="text-sm font-semibold text-red-700 dark:text-red-300">
                  {loadingGasto ? 'Procesando...' : 'Gasto'}
                </span>
              </div>
            </button>

            <button
              onClick={() => setShowRetiro(true)}
              disabled={loadingRetiro}
              className="group relative overflow-hidden bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20 border-2 border-amber-400 dark:border-amber-600 rounded-xl p-6 hover:shadow-2xl hover:scale-105 hover:border-amber-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="flex flex-col items-center justify-center text-center space-y-3">
                <div className="w-12 h-12 bg-amber-500 dark:bg-amber-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <span className="text-sm font-semibold text-amber-700 dark:text-amber-300">
                  {loadingRetiro ? 'Procesando...' : 'Retiro'}
                </span>
              </div>
            </button>

            <button
              onClick={() => setShowDistrib(true)}
              disabled={loadingDistrib}
              className="group relative overflow-hidden bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-2 border-blue-400 dark:border-blue-600 rounded-xl p-6 hover:shadow-2xl hover:scale-105 hover:border-blue-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="flex flex-col items-center justify-center text-center space-y-3">
                <div className="w-12 h-12 bg-blue-500 dark:bg-blue-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <span className="text-sm font-semibold text-blue-700 dark:text-blue-300">
                  {loadingDistrib ? 'Procesando...' : 'Distribución'}
                </span>
              </div>
            </button>
          </div>
        </div>
      </section>

      <OperationsTable refresh={refreshKey} onOpenDetails={(op) => setDetailOp(op)} />

      <OperationDetails open={!!detailOp} onClose={() => setDetailOp(null)} op={detailOp} />

      {showIngreso && (
        <ModalIngreso 
          isOpen={showIngreso} 
          onClose={() => setShowIngreso(false)} 
          onSuccess={() => { 
            setShowIngreso(false); 
            setLoadingIngreso(false); 
            refetch();
          }}
          setLoading={setLoadingIngreso}
        />
      )}
      {showGasto && (
        <ModalGasto 
          isOpen={showGasto} 
          onClose={() => setShowGasto(false)} 
          onSuccess={() => { 
            setShowGasto(false); 
            setLoadingGasto(false); 
            refetch();
          }}
          setLoading={setLoadingGasto}
        />
      )}
      {showRetiro && (
        <ModalRetiro 
          isOpen={showRetiro} 
          onClose={() => setShowRetiro(false)} 
          onSuccess={() => { 
            setShowRetiro(false); 
            setLoadingRetiro(false); 
            refetch();
          }}
          setLoading={setLoadingRetiro}
        />
      )}
      {showDistrib && (
        <ModalDistribucion 
          isOpen={showDistrib} 
          onClose={() => setShowDistrib(false)} 
          onSuccess={() => { 
            setShowDistrib(false); 
            setLoadingDistrib(false); 
            refetch();
          }}
          setLoading={setLoadingDistrib}
        />
      )}
    </>
  );
}
export default Dashboard;
