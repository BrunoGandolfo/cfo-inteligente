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

function Dashboard() {
  const [showIngreso, setShowIngreso] = useState(false);
  const [showGasto, setShowGasto] = useState(false);
  const [showRetiro, setShowRetiro] = useState(false);
  const [showDistrib, setShowDistrib] = useState(false);
  const [detailOp, setDetailOp] = useState(null);

  const { loading, metricas, filtros, refreshKey } = useMetrics();

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

      <section className="px-6 mb-8">
        <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Acciones</h2>
          <div className="flex flex-wrap gap-4">
            <Button variant="success" onClick={() => setShowIngreso(true)}>Registrar Ingreso</Button>
            <Button variant="danger" onClick={() => setShowGasto(true)}>Registrar Gasto</Button>
            <Button variant="primary" onClick={() => setShowRetiro(true)}>Registrar Retiro</Button>
            <Button variant="primary" onClick={() => setShowDistrib(true)}>Registrar Distribución</Button>
          </div>
        </div>
      </section>

      <OperationsTable refresh={refreshKey} onOpenDetails={(op) => setDetailOp(op)} />

      <OperationDetails open={!!detailOp} onClose={() => setDetailOp(null)} op={detailOp} />

      {showIngreso && (
        <ModalIngreso isOpen={showIngreso} onClose={() => setShowIngreso(false)} onSuccess={() => setShowIngreso(false)} />
      )}
      {showGasto && (
        <ModalGasto isOpen={showGasto} onClose={() => setShowGasto(false)} onSuccess={() => setShowGasto(false)} />
      )}
      {showRetiro && (
        <ModalRetiro isOpen={showRetiro} onClose={() => setShowRetiro(false)} onSuccess={() => setShowRetiro(false)} />
      )}
      {showDistrib && (
        <ModalDistribucion isOpen={showDistrib} onClose={() => setShowDistrib(false)} onSuccess={() => setShowDistrib(false)} />
      )}
    </>
  );
}
export default Dashboard;
