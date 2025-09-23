import { createContext, useContext, useEffect, useState } from 'react';
import { addDays } from 'date-fns';

const FilterContext = createContext();
export function FilterProvider({ children }) {
  const [from, setFrom] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const [to, setTo] = useState(() => addDays(new Date(), 0));
  const [localidad, setLocalidad] = useState('Todas');
  const [monedaVista, setMonedaVista] = useState(() => localStorage.getItem('moneda_vista') || 'UYU');
  const [version, setVersion] = useState(0);
  const apply = () => setVersion(v => v + 1);

  useEffect(() => {
    localStorage.setItem('moneda_vista', monedaVista);
  }, [monedaVista]);

  return (
    <FilterContext.Provider value={{ from, to, setFrom, setTo, localidad, setLocalidad, monedaVista, setMonedaVista, version, apply }}>
      {children}
    </FilterContext.Provider>
  );
}
export const useFilterContext = () => useContext(FilterContext);


