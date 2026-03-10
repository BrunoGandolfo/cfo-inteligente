import { LineChart, Line, PieChart, Pie, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ResponsiveContainer } from 'recharts';
import Card from '../ui/Card';

const COLORS = ['#10B981', '#EF4444', '#3B82F6', '#8B5CF6', '#F59E0B'];
const CHART_TICK = { fill: 'rgb(148,163,184)', fontSize: 12 };
const CHART_AXIS_LINE = { stroke: 'rgba(148,163,184,0.15)' };
const CHART_LEGEND_STYLE = { fontSize: 12, color: 'rgb(148,163,184)' };

export function ChartsSection({ operaciones }) {
  // 🔍 DIAGNÓSTICO: Ver qué datos recibe el componente

  // Tooltips personalizados
  const CustomTooltipEvolution = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const ingresos = payload[0]?.value || 0;
      const gastos = payload[1]?.value || 0;
      const margen = ingresos > 0 ? ((ingresos - gastos) / ingresos * 100).toFixed(1) : 0;
      return (
        <div className="bg-surface p-3 rounded-lg shadow-lg border border-border">
          <p className="font-semibold text-text-primary mb-2">{label}</p>
          <p className="text-sm text-success">Ingresos: ${ingresos.toLocaleString('es-UY')}</p>
          <p className="text-sm text-danger">Gastos: ${gastos.toLocaleString('es-UY')}</p>
          <p className="text-xs text-text-secondary mt-1 pt-1 border-t border-border">Margen: {margen}%</p>
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
        <div className="bg-surface p-3 rounded-lg shadow-lg border border-border">
          <p className="font-semibold text-text-primary">{data.name}</p>
          <p className="text-sm text-text-secondary">${data.value.toLocaleString('es-UY')}</p>
          <p className="text-sm font-medium text-info">{Number(percentage).toFixed(1)}% del total</p>
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
        <div className="bg-surface p-3 rounded-lg shadow-lg border border-border">
          <p className="font-semibold text-text-primary mb-2">{label}</p>
          <p className="text-sm text-success">Ingresos: ${ingresos.toLocaleString('es-UY')}</p>
          <p className="text-sm text-danger">Gastos: ${gastos.toLocaleString('es-UY')}</p>
          <p className="text-xs text-text-secondary mt-1 pt-1 border-t border-border">Rentabilidad: {rentabilidad}%</p>
        </div>
      );
    }
    return null;
  };
  const evolutionData = prepareEvolutionData(operaciones || []);
  const areaData = prepareAreaData(operaciones || []);
  const locationData = prepareLocationData(operaciones || []);

  return (
    <section className="px-4 xl:px-6 mb-8 grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 xl:gap-5">
      <Card className="p-5 xl:p-6">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-text-secondary mb-5">Evolución Mensual</h3>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={evolutionData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
            <XAxis dataKey="mes" tick={CHART_TICK} axisLine={CHART_AXIS_LINE} />
            <YAxis 
              tick={CHART_TICK}
              axisLine={CHART_AXIS_LINE}
              tickFormatter={(value) => {
                if (value >= 1000000) return `$${(value/1000000).toFixed(1)}M`;
                if (value >= 1000) return `$${(value/1000).toFixed(0)}K`;
                return `$${value}`;
              }}
              width={80}
            />
            <Tooltip content={<CustomTooltipEvolution />} />
            <Legend wrapperStyle={CHART_LEGEND_STYLE} />
            <Line type="monotone" dataKey="ingresos" stroke="#10B981" strokeWidth={2} />
            <Line type="monotone" dataKey="gastos" stroke="#EF4444" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card className="p-5 xl:p-6">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-text-secondary mb-5">Distribución por Área</h3>
        <ResponsiveContainer width="100%" height={280}>
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

      <Card className="p-5 xl:p-6">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-text-secondary mb-5">Comparación por Localidad</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={locationData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
            <XAxis dataKey="localidad" tick={CHART_TICK} axisLine={CHART_AXIS_LINE} />
            <YAxis 
              tick={CHART_TICK}
              axisLine={CHART_AXIS_LINE}
              tickFormatter={(value) => {
                if (value >= 1000000) return `$${(value/1000000).toFixed(1)}M`;
                if (value >= 1000) return `$${(value/1000).toFixed(0)}K`;
                return `$${value}`;
              }}
              width={80}
            />
            <Tooltip content={<CustomTooltipBars />} />
            <Legend wrapperStyle={CHART_LEGEND_STYLE} />
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
    // Usar año-mes como key para ordenar correctamente
    const yearMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    const monthLabel = d.toLocaleDateString('es-UY', { month: 'short' });
    
    if (!months[yearMonth]) {
      months[yearMonth] = { 
        mes: monthLabel, 
        ingresos: 0, 
        gastos: 0,
        sortKey: yearMonth  // Para ordenar
      };
    }
    
    const tipo = (op.tipo || op.tipo_operacion || '').toUpperCase();
    const monto = Number(op.monto_uyu || 0);
    if (tipo === 'INGRESO') months[yearMonth].ingresos += monto;
    if (tipo === 'GASTO') months[yearMonth].gastos += monto;
  });
  
  
  // Convertir a array y ordenar cronológicamente
  const allMonths = Object.values(months).sort((a, b) => a.sortKey.localeCompare(b.sortKey));
  
  const result = allMonths.slice(-6);
  
  return result;
}

function prepareAreaData(operaciones) {
  
  
  const ingresos = operaciones.filter(op => (op.tipo || op.tipo_operacion || '').toUpperCase() === 'INGRESO');
  
  const areas = {};
  ingresos.forEach(op => {
    const areaName = op.area || 'Sin Área';
    areas[areaName] = (areas[areaName] || 0) + Number(op.monto_uyu || 0);
  });
  
  
  const total = Object.values(areas).reduce((sum, val) => sum + val, 0);
  
  const result = Object.entries(areas).map(([name, value]) => ({
    name,
    value,
    total,
    percentage: total > 0 ? (value / total * 100).toFixed(1) : 0
  }));
  
  
  return result;
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
    } else if (loc) {
    }
  });
  
  
  const result = [
    { localidad: 'Montevideo', ...data.MONTEVIDEO },
    { localidad: 'Mercedes', ...data.MERCEDES }
  ];
  
  
  return result;
}

export default ChartsSection;
