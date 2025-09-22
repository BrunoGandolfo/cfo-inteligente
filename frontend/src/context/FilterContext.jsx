import { createContext, useContext, useState } from 'react';
import { addDays } from 'date-fns';

const FilterContext = createContext();
export function FilterProvider({ children }) {
  const [from, setFrom] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const [to, setTo] = useState(() => addDays(new Date(), 0));
  const [localidad, setLocalidad] = useState('Todas');
  const [version, setVersion] = useState(0);
  const apply = () => setVersion(v => v + 1);

  return (
    <FilterContext.Provider value={{ from, to, setFrom, setTo, localidad, setLocalidad, version, apply }}>
      {children}
    </FilterContext.Provider>
  );
}
export const useFilterContext = () => useContext(FilterContext);


