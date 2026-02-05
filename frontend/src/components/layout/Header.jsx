import { Bell, Filter, TrendingUp, Menu } from 'lucide-react';
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

export function Header({ onMobileMenuToggle }) {
  const [now, setNow] = useState(new Date());
  const [isFilterDrawerOpen, setIsFilterDrawerOpen] = useState(false);
  
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

  return (
    <>
    <header className={`fixed top-0 w-full bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 z-50 ${esSocio ? 'h-16' : 'h-20'}`}>
      <div className="h-full flex items-center min-w-0">
        
        {/* Botón hamburguesa - SOLO MÓVIL, visible para todos los usuarios */}
        <button
          onClick={onMobileMenuToggle}
          className="lg:hidden p-3 ml-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 shrink-0"
          aria-label="Abrir menú"
        >
          <Menu className="w-6 h-6 text-gray-700 dark:text-slate-200" />
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
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                Bienvenido, {userName}
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                {fecha} | {horaConAmPm()}
              </p>
            </div>

            {/* ZONA 3: ThemeToggle + Cerrar sesión */}
            <div className="w-[180px] flex items-center gap-3 justify-end px-4 shrink-0">
              <ThemeToggle />
              <button
                className="inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium bg-white hover:bg-red-50 dark:bg-slate-800 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 border-2 border-red-600 dark:border-red-800 hover:border-red-700 dark:hover:border-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 transition-all duration-200"
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
          {/* HEADER PARA SOCIOS (sin cambios) */}
          {/* ═══════════════════════════════════════════════════════════════ */}
          {/* ZONA 1: Logo (oculto en móvil, visible en lg+) */}
          <div className="hidden lg:flex w-[250px] items-center px-4 xl:px-6 border-r border-gray-200 dark:border-slate-800 shrink-0">
            <img src="/logo-conexion.png" alt="Conexión" className="h-14 xl:h-16 w-auto object-contain" />
          </div>

          {/* ZONA 2: Centro - ADAPTATIVO */}
          <div className="flex-1 min-w-0 flex items-center justify-center px-2 xl:px-6">
            <div className="flex items-center gap-2 xl:gap-3 text-sm min-w-0">
              
              {/* Fecha ADAPTATIVA */}
              <div className="flex items-center shrink-0">
                {/* Fecha larga en 2XL+ */}
                <span className="hidden 2xl:inline text-gray-600 dark:text-gray-400 capitalize">{fecha}</span>
                {/* Fecha corta en LG-<2XL */}
                <span className="hidden lg:inline 2xl:hidden text-gray-600 dark:text-gray-400">{fechaCorta}</span>
                {/* Solo hora en <LG */}
                <span className="inline lg:hidden text-gray-600 dark:text-gray-400">{hora}</span>
                
                <span className="mx-2 text-gray-300 dark:text-slate-700 hidden lg:inline">|</span>
                <span className="hidden lg:inline text-gray-900 dark:text-white">{hora}</span>
              </div>
              
              {/* Solo mostrar filtros si es socio */}
              {esSocio && (
                <>
                  <div className="h-8 w-px bg-gray-300 dark:bg-slate-700 shrink-0"></div>
                  
                  {/* Botón FILTROS (visible hasta 2XL) */}
                  <button
                    onClick={() => setIsFilterDrawerOpen(!isFilterDrawerOpen)}
                    className="flex 2xl:hidden items-center gap-2 px-3 py-1.5 rounded-lg border-2 border-blue-400 dark:border-blue-600 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors shrink-0"
                    aria-label="Abrir filtros"
                    aria-expanded={isFilterDrawerOpen}
                  >
                    <Filter className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    <span className="text-sm font-medium text-blue-700 dark:text-blue-300">Filtros</span>
                    {activeFiltersCount > 0 && (
                      <span className="px-1.5 py-0.5 text-xs font-bold text-white bg-blue-600 dark:bg-blue-500 rounded-full">
                        {activeFiltersCount}
                      </span>
                    )}
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
                  </div>
                </>
              )}
            </div>
          </div>

          {/* ZONA 3: Usuario (derecha) */}
          <div className="flex items-center gap-2 xl:gap-4 px-2 xl:px-6 shrink-0">
            <button 
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-slate-800 shrink-0" 
              aria-label="Notificaciones"
            >
              <Bell className="w-5 h-5 text-gray-700 dark:text-slate-200" />
            </button>
            
            <ThemeToggle />
            
            <div className="h-8 w-px bg-gray-300 dark:bg-slate-700 hidden xl:block shrink-0"></div>
            
            <Avatar name={userName} />
            
            <span className="hidden 2xl:inline text-sm text-gray-700 dark:text-slate-200 shrink-0">
              {`Hola, ${userName}`}
            </span>
            
            <button
              className="inline-flex items-center justify-center rounded-md px-2 xl:px-4 py-1.5 xl:py-2 text-xs xl:text-sm font-medium bg-white hover:bg-red-50 dark:bg-slate-800 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 border-2 border-red-600 dark:border-red-800 hover:border-red-700 dark:hover:border-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 transition-all duration-200 shrink-0"
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
      {esSocio && (
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
        />
      )}
    </>
  );
}

Header.propTypes = {
  onMobileMenuToggle: PropTypes.func
};

export default Header;
