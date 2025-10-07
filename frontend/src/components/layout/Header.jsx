import { Bell } from 'lucide-react';
import { useEffect, useState } from 'react';
import ThemeToggle from './ThemeToggle';
import Avatar from '../ui/Avatar';
import DateRangePicker from '../filters/DateRangePicker';
import LocalityFilter from '../filters/LocalityFilter';
import { useFilters } from '../../hooks/useFilters';
import MonedaToggle from '../filters/MonedaToggle';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import toast from 'react-hot-toast';

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
        {/* ZONA 1: Izquierda (250px fijo) */}
        <div className="w-[250px] flex items-center px-6 border-r border-gray-200 dark:border-slate-800">
          <img src="/logo-conexion.png" alt="Conexión" className="h-16 w-auto object-contain" />
        </div>

        {/* ZONA 2: Centro (flex-1) — filtros en línea con gap-3 */}
        <div className="flex-1 flex items-center justify-center px-6">
          <div className="flex items-center gap-3 text-sm">
            <div className="flex items-center">
              <span className="text-gray-600 dark:text-gray-400 capitalize">{fecha}</span>
              <span className="mx-2 text-gray-300 dark:text-slate-700">|</span>
              <span className="text-gray-900 dark:text-white">{hora}</span>
            </div>
            <div className="h-8 w-px bg-gray-300 dark:bg-slate-700"></div>
            <MonedaToggle />
            <DateRangePicker from={from} to={to} onFrom={(d)=>{ setFrom(d); apply(); }} onTo={(d)=>{ setTo(d); apply(); }} />
            <LocalityFilter value={localidad} onChange={(v)=>{ setLocalidad(v); apply(); }} />
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
          <button
            className="inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium bg-white hover:bg-red-50 dark:bg-slate-800 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 border-2 border-red-200 dark:border-red-800 hover:border-red-300 dark:hover:border-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 transition-all duration-200"
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
      </div>
    </header>
  );
}
export default Header;


