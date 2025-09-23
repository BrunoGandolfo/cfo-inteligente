import { LineChart, Line, PieChart, Pie, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ResponsiveContainer } from 'recharts';
import Card from '../ui/Card';

const COLORS = ['#10B981', '#EF4444', '#3B82F6', '#8B5CF6', '#F59E0B'];

export function ChartsSection({ operaciones }) {
  // Tooltips personalizados
  const CustomTooltipEvolution = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const ingresos = payload[0]?.value || 0;
      const gastos = payload[1]?.value || 0;
      const margen = ingresos > 0 ? ((ingresos - gastos) / ingresos * 100).toFixed(1) : 0;
      return (
        <div className="bg-white dark:bg-slate-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700">
          <p className="font-semibold text-gray-900 dark:text-white mb-2">{label}</p>
          <p className="text-sm text-green-600 dark:text-green-400">Ingresos: ${ingresos.toLocaleString('es-UY')}</p>
          <p className="text-sm text-red-600 dark:text-red-400">Gastos: ${gastos.toLocaleString('es-UY')}</p>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 pt-1 border-t border-gray-200 dark:border-slate-700">Margen: {margen}%</p>
        </div>
      );
    }
    return null;
  };

  const CustomTooltipPie = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      const percentage = data.payload.percentage || ((data.value / data.payload.total) * 100);
      return (
        <div className="bg-white dark:bg-slate-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700">
          <p className="font-semibold text-gray-900 dark:text-white">{data.name}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400">${data.value.toLocaleString('es-UY')}</p>
          <p className="text-sm font-medium text-blue-600 dark:text-blue-400">{Number(percentage).toFixed(1)}% del total</p>
        </div>
      );
    }
    return null;
  };

  const CustomTooltipBars = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const ingresos = payload.find(p => p.dataKey === 'ingresos')?.value || 0;
      const gastos = payload.find(p => p.dataKey === 'gastos')?.value || 0;
      const rentabilidad = ingresos > 0 ? ((ingresos - gastos) / ingresos * 100).toFixed(1) : 0;
      return (
        <div className="bg-white dark:bg-slate-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700">
          <p className="font-semibold text-gray-900 dark:text-white mb-2">{label}</p>
          <p className="text-sm text-green-600 dark:text-green-400">Ingresos: ${ingresos.toLocaleString('es-UY')}</p>
          <p className="text-sm text-red-600 dark:text-red-400">Gastos: ${gastos.toLocaleString('es-UY')}</p>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 pt-1 border-t border-gray-200 dark:border-slate-700">Rentabilidad: {rentabilidad}%</p>
        </div>
      );
    }
    return null;
  };
  const evolutionData = prepareEvolutionData(operaciones || []);
  const areaData = prepareAreaData(operaciones || []);
  const locationData = prepareLocationData(operaciones || []);

  return (
    <section className="px-6 mb-8 grid grid-cols-3 gap-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Evolución Mensual</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={evolutionData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="mes" />
            <YAxis />
            <Tooltip content={<CustomTooltipEvolution />} />
            <Legend />
            <Line type="monotone" dataKey="ingresos" stroke="#10B981" strokeWidth={2} />
            <Line type="monotone" dataKey="gastos" stroke="#EF4444" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Distribución por Área</h3>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie data={areaData} cx="50%" cy="50%" labelLine={false}
                 label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                 outerRadius={80} dataKey="value">
              {areaData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltipPie />} />
          </PieChart>
        </ResponsiveContainer>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Comparación por Localidad</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={locationData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="localidad" />
            <YAxis />
            <Tooltip content={<CustomTooltipBars />} />
            <Legend />
            <Bar dataKey="ingresos" fill="#10B981" />
            <Bar dataKey="gastos" fill="#EF4444" />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </section>
  );
}

function prepareEvolutionData(operaciones) {
  const months = {};
  operaciones.forEach(op => {
    const d = new Date(op.fecha);
    const month = d.toLocaleDateString('es-UY', { month: 'short' });
    if (!months[month]) months[month] = { mes: month, ingresos: 0, gastos: 0 };
    const tipo = (op.tipo || op.tipo_operacion || '').toUpperCase();
    const monto = Number(op.monto_uyu || 0);
    if (tipo === 'INGRESO') months[month].ingresos += monto;
    if (tipo === 'GASTO') months[month].gastos += monto;
  });
  return Object.values(months).slice(-6);
}

function prepareAreaData(operaciones) {
  const AREAS_MAP = {
    'd3aff49c-748c-4d1d-bc47-cdda1cfb913d': 'Jurídica',
    '53ba7821-8836-4e74-ad56-a288d290881d': 'Notarial',
    '14700c01-3b3d-49c6-8e2e-f3ebded1b1bb': 'Contable',
    '11c64c64-c7f6-4e85-9c26-b577c3d7a5b7': 'Recuperación',
    'b11006d3-6cfc-4766-9201-ab56274401a6': 'Gastos Generales'
  };
  const areas = {};
  operaciones
    .filter(op => (op.tipo || op.tipo_operacion || '').toUpperCase() === 'INGRESO')
    .forEach(op => {
      const areaName = AREAS_MAP[op.area_id] || 'Otros';
      areas[areaName] = (areas[areaName] || 0) + Number(op.monto_uyu || 0);
    });
  const total = Object.values(areas).reduce((sum, val) => sum + val, 0);
  return Object.entries(areas).map(([name, value]) => ({
    name,
    value,
    total,
    percentage: total > 0 ? (value / total * 100).toFixed(1) : 0
  }));
}

function prepareLocationData(operaciones) {
  const data = { MONTEVIDEO: { ingresos: 0, gastos: 0 }, MERCEDES: { ingresos: 0, gastos: 0 } };
  operaciones.forEach(op => {
    const loc = (op.localidad || '').toUpperCase();
    const tipo = (op.tipo || op.tipo_operacion || '').toUpperCase();
    const monto = Number(op.monto_uyu || 0);
    if (loc && data[loc]) {
      if (tipo === 'INGRESO') data[loc].ingresos += monto;
      if (tipo === 'GASTO') data[loc].gastos += monto;
    }
  });
  return [
    { localidad: 'Montevideo', ...data.MONTEVIDEO },
    { localidad: 'Mercedes', ...data.MERCEDES }
  ];
}

export default ChartsSection;


