import { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext({ dark: true, toggle: () => {} });

export function ThemeProvider({ children }) {
  // Default a 'dark' si no hay valor en localStorage
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem('theme');
    // Si no hay valor guardado, default es dark (true)
    return stored === null ? true : stored === 'dark';
  });
  
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }, [dark]);
  
  return (
    <ThemeContext.Provider value={{ dark, toggle: () => setDark(v => !v) }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useThemeContext = () => useContext(ThemeContext);
