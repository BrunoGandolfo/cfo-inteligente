import { useFilters } from '../../hooks/useFilters';

export default function MonedaToggle() {
  const { monedaVista, setMonedaVista, apply } = useFilters();

  const setUYU = () => { setMonedaVista('UYU'); apply(); };
  const setUSD = () => { setMonedaVista('USD'); apply(); };

  return (
    <div className="flex items-center rounded-md bg-gray-100 dark:bg-slate-800 p-0.5 transition-colors">
      <button
        onClick={setUYU}
        className={`px-3 py-2 text-xs md:text-sm rounded-md transition-all duration-200 ${
          monedaVista==='UYU'
            ? 'bg-white dark:bg-slate-900 text-gray-900 dark:text-white shadow'
            : 'text-gray-600 dark:text-slate-300'
        }`}
        aria-pressed={monedaVista==='UYU'}
      >
        $ UYU
      </button>
      <button
        onClick={setUSD}
        className={`ml-1 px-3 py-2 text-xs md:text-sm rounded-md transition-all duration-200 ${
          monedaVista==='USD'
            ? 'bg-white dark:bg-slate-900 text-gray-900 dark:text-white shadow'
            : 'text-gray-600 dark:text-slate-300'
        }`}
        aria-pressed={monedaVista==='USD'}
      >
        US$ USD
      </button>
    </div>
  );
}


