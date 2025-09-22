import { Bell } from 'lucide-react';
import { useEffect, useState } from 'react';
import ThemeToggle from './ThemeToggle';
import Avatar from '../ui/Avatar';
import DateRangePicker from '../filters/DateRangePicker';
import LocalityFilter from '../filters/LocalityFilter';
import Button from '../ui/Button';
import { useFilters } from '../../hooks/useFilters';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

export function Header() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(id);
  }, []);
  const fecha = format(now, "EEEE, d 'de' MMMM yyyy", { locale: es });
  const hora = format(now, 'HH:mm', { locale: es });
  const userName = localStorage.getItem('userName') || 'Usuario';
  const { from, to, setFrom, setTo, localidad, setLocalidad, apply } = useFilters();

  return (
    <header className="h-16 fixed top-0 w-full bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 z-40">
      <div className="h-full flex items-center">
        {/* ZONA 1: Logo (ancho fijo) */}
        <div className="w-64 flex items-center px-6 border-r border-gray-200 dark:border-slate-800">
          <img src="/logo-conexion.png" alt="Conexión" className="h-14 max-h-14 w-auto object-contain" />
        </div>

        {/* ZONA 2: Centro con filtros */}
        <div className="flex-1 flex items-center justify-center px-6">
          <div className="flex items-center gap-4">
            {/* Fecha y hora juntas */}
            <div className="text-sm flex items-center">
              <span className="text-gray-600 dark:text-slate-300 capitalize">{fecha}</span>
              <span className="mx-2 text-gray-300">|</span>
              <span className="text-gray-900 dark:text-white">{hora}</span>
            </div>
            {/* Separador vertical */}
            <div className="h-8 w-px bg-gray-300 dark:bg-slate-700"></div>
            {/* Filtros de fecha */}
            <DateRangePicker from={from} to={to} onFrom={setFrom} onTo={setTo} />
            {/* Localidad */}
            <LocalityFilter value={localidad} onChange={setLocalidad} />
            {/* Botón aplicar */}
            <Button variant="primary" onClick={apply}>Aplicar filtros</Button>
          </div>
        </div>

        {/* ZONA 3: Usuario (derecha) */}
        <div className="flex items-center gap-4 px-6">
          <button className="px-2 py-1 rounded-md hover:bg-gray-100 dark:hover:bg-slate-800" aria-label="Notificaciones">
            <Bell className="w-5 h-5 text-gray-700 dark:text-slate-200" />
          </button>
          <ThemeToggle />
          <div className="h-8 w-px bg-gray-300 dark:bg-slate-700"></div>
          <Avatar name={userName} />
          <span className="hidden md:inline text-sm text-gray-700 dark:text-slate-200">{`Hola, ${userName}`}</span>
          <Button
            variant="ghost"
            onClick={() => { localStorage.clear(); window.location.href = '/login'; }}
          >
            Cerrar sesión
          </Button>
        </div>
      </div>
    </header>
  );
}
export default Header;


