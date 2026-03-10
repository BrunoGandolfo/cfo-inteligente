import { Filter, TrendingUp, Menu, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import ThemeToggle from './ThemeToggle';
import Avatar from '../ui/Avatar';
import DateRangePicker from '../filters/DateRangePicker';
import LocalityFilter from '../filters/LocalityFilter';
import FilterDrawer from './FilterDrawer';
import { useFilters } from '../../hooks/useFilters';
import MonedaToggle from '../filters/MonedaToggle';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import toast from 'react-hot-toast';
import axiosClient from '../../services/api/axiosClient';

export function Header({ onMobileMenuToggle }) {
  const [now, setNow] = useState(new Date());
  const [isFilterDrawerOpen, setIsFilterDrawerOpen] = useState(false);
  const [exportingExcel, setExportingExcel] = useState(false);
  
  // Verificar si el usuario es socio (colaboradores no ven filtros)
  const esSocio = localStorage.getItem('esSocio') === 'true';
  
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(id);
  }, []);
  
  const fecha = format(now, "EEEE, d 'de' MMMM yyyy", { locale: es });
  const fechaCorta = format(now, "d MMM yyyy", { locale: es });
  const hora = format(now, 'HH:mm', { locale: es });
  const userName = localStorage.getItem('userName') || 'Usuario';
  const { from, to, setFrom, setTo, localidad, setLocalidad, apply } = useFilters();
  
  // Calcular filtros activos
  const activeFiltersCount = [
    from !== null && to !== null,
    localidad && localidad !== 'Todas' && localidad !== ''
  ].filter(Boolean).length;

  // Formateo de hora con AM/PM para colaboradores
  const horaConAmPm = () => {
    const hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const hour12 = hours % 12 || 12;
    return `${hour12}:${minutes} ${ampm}`;
  };
  
  // Handler para limpiar filtros
  const handleClearFilters = () => {
    // Resetear a valores por defecto del FilterContext (NO null)
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    
    setFrom(firstDayOfMonth);   // Primer día del mes actual (valor default)
    setTo(today);               // Hoy (valor default)
    setLocalidad('Todas');
    
    apply();
    setIsFilterDrawerOpen(false);
  };

  const handleExportExcel = async () => {
    try {
      setExportingExcel(true);
      const params = new URLSearchParams();
      params.append('fecha_desde', format(from, 'yyyy-MM-dd'));
      params.append('fecha_hasta', format(to, 'yyyy-MM-dd'));

      const response = await axiosClient.get(
        `/api/operaciones/export-excel?${params.toString()}`,
        { responseType: 'blob' }
      );

      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const contentDisposition = response.headers['content-disposition'];
      a.download = contentDisposition
        ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
        : `operaciones_${format(new Date(), 'yyyy-MM-dd')}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Excel descargado');
    } catch (error) {
      console.error('Error exportando Excel:', error);
      toast.error('Error al exportar Excel');
    } finally {
      setExportingExcel(false);
    }
  };

  return (
    <>
    <header className={`fixed top-0 w-full bg-surface border-b border-border z-50 ${esSocio ? 'h-16' : 'h-20'}`}>
      <div className="h-full flex items-center min-w-0">
        
        {/* Botón hamburguesa - SOLO MÓVIL, visible para todos los usuarios */}
        <button
          onClick={onMobileMenuToggle}
          className="lg:hidden p-3 ml-2 rounded-lg hover:bg-surface-alt shrink-0"
          aria-label="Abrir menú"
        >
          <Menu className="w-6 h-6 text-text-primary" />
        </button>
        
        {/* ═══════════════════════════════════════════════════════════════ */}
        {/* HEADER PARA COLABORADORES */}
        {/* ═══════════════════════════════════════════════════════════════ */}
        {!esSocio ? (
          <>
            {/* ZONA 1: Ícono TrendingUp */}
            <div className="w-[180px] flex items-center justify-center px-4 shrink-0">
              <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/20">
                <TrendingUp className="w-14 h-14 text-emerald-600 dark:text-emerald-400" />
              </div>
            </div>

            {/* ZONA 2: Centro - Bienvenida + Fecha/Hora */}
            <div className="flex-1 flex flex-col items-center justify-center">
              <h1 className="text-xl font-bold text-text-primary">
                Bienvenido, {userName}
              </h1>
              <p className="text-sm text-text-secondary capitalize">
                {fecha} | {horaConAmPm()}
              </p>
            </div>

            {/* ZONA 3: ThemeToggle + Cerrar sesión */}
            <div className="w-[180px] flex items-center gap-3 justify-end px-4 shrink-0">
              <ThemeToggle />
              <button
                className="inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium text-red-400 border border-red-400/30 rounded-lg hover:bg-red-500/10 hover:border-red-400/50 transition-all duration-200"
                onClick={() => {
                  toast.success('Sesión cerrada correctamente');
                  setTimeout(() => {
                    localStorage.clear();
                    window.location.href = '/login';
                  }, 500);
                }}
              >
                Cerrar sesión
              </button>
            </div>
          </>
        ) : (
          <>
          {/* ═══════════════════════════════════════════════════════════════ */}
          {/* HEADER PARA SOCIOS */}
          {/* ═══════════════════════════════════════════════════════════════ */}
          {/* ZONA 1: Centro - ADAPTATIVO */}
          <div className="flex-1 min-w-0 flex items-center justify-center px-2 xl:px-6">
            <div className="flex items-center gap-2 xl:gap-3 text-sm min-w-0">
              
              {/* Fecha ADAPTATIVA */}
              <div className="flex items-center shrink-0">
                {/* Fecha larga en 2XL+ */}
                <span className="hidden 2xl:inline text-text-secondary capitalize">{fecha}</span>
                {/* Fecha corta en LG-<2XL */}
                <span className="hidden lg:inline 2xl:hidden text-text-secondary">{fechaCorta}</span>
                {/* Solo hora en <LG */}
                <span className="inline lg:hidden text-text-secondary">{hora}</span>
                
                <span className="mx-2 text-text-muted hidden lg:inline">|</span>
                <span className="hidden lg:inline text-text-primary">{hora}</span>
              </div>
              
              {/* Solo mostrar filtros si es socio */}
              {esSocio ? (
                <>
                  <div className="h-8 w-px bg-border shrink-0"></div>
                  
                  {/* Botón FILTROS (visible hasta 2XL) */}
                  <button
                    onClick={() => setIsFilterDrawerOpen(!isFilterDrawerOpen)}
                    className="flex 2xl:hidden items-center gap-2 px-3 py-1.5 rounded-lg border-2 border-info bg-info/10 hover:bg-info/20 transition-colors shrink-0"
                    aria-label="Abrir filtros"
                    aria-expanded={isFilterDrawerOpen}
                  >
                    <Filter className="w-4 h-4 text-info" />
                    <span className="text-sm font-medium text-info">Filtros</span>
                    {activeFiltersCount > 0 ? (
                      <span className="px-1.5 py-0.5 text-xs font-bold text-white bg-info rounded-full">
                        {activeFiltersCount}
                      </span>
                    ) : null}
                  </button>
                  
                  {/* Filtros INLINE (solo visible en 2XL+) */}
                  <div className="hidden 2xl:flex items-center gap-3 min-w-0">
                    <MonedaToggle />
                    <DateRangePicker 
                      from={from} 
                      to={to} 
                      onFrom={(d) => { setFrom(d); apply(); }} 
                      onTo={(d) => { setTo(d); apply(); }}
                      compact={false}
                    />
                    <LocalityFilter
                      value={localidad}
                      onChange={(v) => { setLocalidad(v); apply(); }}
                      compact={false}
                    />
                    <button
                      onClick={handleExportExcel}
                      disabled={exportingExcel}
                      className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-success text-success hover:bg-success/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                      title="Exportar operaciones a Excel"
                    >
                      {exportingExcel ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className="w-5 h-5" fill="none">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" fill="#185C37"/>
                          <path d="M14 2v6h6" fill="#21A366"/>
                          <path d="M14 2L20 8H14V2z" fill="#33C481"/>
                          <path d="M2 7h10v10H2z" fill="#107C41" rx="1"/>
                          <text x="7" y="15" textAnchor="middle" fill="white" fontSize="7" fontWeight="bold" fontFamily="Arial">X</text>
                        </svg>
                      )}
                      <span className="hidden 2xl:inline text-sm font-medium">Excel</span>
                    </button>
                  </div>
                </>
              ) : null}
            </div>
          </div>

          {/* ZONA 3: Usuario (derecha) */}
          <div className="flex items-center gap-2 xl:gap-4 px-2 xl:px-6 shrink-0">
            <ThemeToggle />
            
            <div className="h-8 w-px bg-border hidden xl:block shrink-0"></div>
            
            <Avatar name={userName} />
            
            <span className="hidden 2xl:inline text-sm text-text-primary shrink-0">
              {`Hola, ${userName}`}
            </span>
            
            <button
              className="inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium text-red-400 border border-red-400/30 rounded-lg hover:bg-red-500/10 hover:border-red-400/50 transition-all duration-200 shrink-0"
              onClick={() => {
                toast.success('Sesión cerrada correctamente');
                setTimeout(() => {
                  localStorage.clear();
                  window.location.href = '/login';
                }, 500);
              }}
            >
              <span className="hidden lg:inline">Cerrar sesión</span>
              <span className="inline lg:hidden">Salir</span>
            </button>
          </div>
          </>
        )}
        </div>
      </header>
      
      {/* FilterDrawer Component - Solo para socios */}
      {esSocio ? (
        <FilterDrawer
          isOpen={isFilterDrawerOpen}
          onClose={() => setIsFilterDrawerOpen(false)}
          from={from}
          to={to}
          localidad={localidad}
          setFrom={setFrom}
          setTo={setTo}
          setLocalidad={setLocalidad}
          apply={apply}
          onClearFilters={handleClearFilters}
          activeFiltersCount={activeFiltersCount}
          onExportExcel={handleExportExcel}
          exportingExcel={exportingExcel}
        />
      ) : null}
    </>
  );
}

Header.propTypes = {
  onMobileMenuToggle: PropTypes.func
};

export default Header;
