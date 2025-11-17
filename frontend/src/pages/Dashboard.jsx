import { useState } from 'react';
import axios from 'axios';
import MetricsGrid from '../components/metrics/MetricsGrid';
import ModalIngreso from '../components/ModalIngreso';
import ModalGasto from '../components/ModalGasto';
import ModalRetiro from '../components/ModalRetiro';
import ModalDistribucion from '../components/ModalDistribucion';
import { ReportGeneratorModal } from '../components/reports/ReportGeneratorModal';
import { useMetrics } from '../hooks/useMetrics';
import { formatMoney } from '../utils/formatters';
import Button from '../components/ui/Button';
import ChartsSection from '../components/charts/ChartsSection';
import { useOperations } from '../hooks/useOperations';
import { useChartData } from '../hooks/useChartData';
import ActiveFilters from '../components/filters/ActiveFilters';
import { FileText, TrendingUp, TrendingDown, Wallet, Users } from 'lucide-react';
import OperationButton from '../components/operations/OperationButton';

function Dashboard() {
  const [showIngreso, setShowIngreso] = useState(false);
  const [showGasto, setShowGasto] = useState(false);
  const [showRetiro, setShowRetiro] = useState(false);
  const [showDistrib, setShowDistrib] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [loadingIngreso, setLoadingIngreso] = useState(false);
  const [loadingGasto, setLoadingGasto] = useState(false);
  const [loadingRetiro, setLoadingRetiro] = useState(false);
  const [loadingDistrib, setLoadingDistrib] = useState(false);

  const { loading, metricas, filtros, refreshKey } = useMetrics();
  const { operacionesAll, refetch } = useOperations(refreshKey);
  const { operaciones: chartData, loading: chartLoading } = useChartData();

  // Helper function para obtener nombre del mes actual
  const getCurrentMonthName = () => {
    const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    return months[new Date().getMonth()];
  };

  // 🔍 DIAGNÓSTICO Dashboard
  console.log('🏠 DASHBOARD - Estado actual:');
  console.log('  refreshKey:', refreshKey);
  console.log('  operacionesAll:', operacionesAll?.length || 0, 'operaciones');
  console.log('  chartData:', chartData?.length || 0, 'operaciones');
  console.log('  loading:', loading);

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

      <section className="px-4 xl:px-6 mb-8">
        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg shadow-sm p-4 xl:p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg xl:text-xl font-bold text-gray-900 dark:text-white">Registrar Operación</h2>
            <button
              onClick={() => setShowReportModal(true)}
              className="px-3 xl:px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg text-sm xl:text-base font-medium shadow-md hover:shadow-lg transition-all duration-200 flex items-center gap-2 shrink-0"
            >
              <FileText className="w-4 xl:w-5 h-4 xl:h-5" />
              <span className="hidden xl:inline">Generar Reporte PDF</span>
              <span className="inline xl:hidden">Reporte</span>
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 xl:gap-5">
            
            <OperationButton
              variant="ingreso"
              title="Registrar Ingreso"
              description="Facturación, cobros y ventas del estudio"
              lastActivity={`${getCurrentMonthName()} ${new Date().getFullYear()}: ${formatMoney(ingresosVal, moneda)}`}
              shortcut="⌘ + 1"
              icon={TrendingUp}
              onClick={() => setShowIngreso(true)}
              loading={loadingIngreso}
              disabled={loadingIngreso}
            />
            
            <OperationButton
              variant="gasto"
              title="Registrar Gasto"
              description="Gastos operativos, servicios y honorarios"
              lastActivity={`${getCurrentMonthName()} ${new Date().getFullYear()}: ${formatMoney(gastosVal, moneda)}`}
              shortcut="⌘ + 2"
              icon={TrendingDown}
              onClick={() => setShowGasto(true)}
              loading={loadingGasto}
              disabled={loadingGasto}
            />
            
            <OperationButton
              variant="retiro"
              title="Retiro de Empresa"
              description="Retiros vinculados a operaciones de la empresa"
              lastActivity="Se realiza a fin de mes"
              shortcut="⌘ + 3"
              icon={Wallet}
              onClick={() => setShowRetiro(true)}
              loading={loadingRetiro}
              disabled={loadingRetiro}
            />
            
            <OperationButton
              variant="distribucion"
              title="Distribución de Utilidades"
              description="Distribución mensual de utilidades entre socios"
              lastActivity="Se realiza a fin de mes"
              shortcut="⌘ + 4"
              icon={Users}
              onClick={() => setShowDistrib(true)}
              loading={loadingDistrib}
              disabled={loadingDistrib}
            />
            
          </div>
        </div>
      </section>

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
      {showReportModal && (
        <ReportGeneratorModal 
          isOpen={showReportModal} 
          onClose={() => setShowReportModal(false)} 
        />
      )}
    </>
  );
}
export default Dashboard;
