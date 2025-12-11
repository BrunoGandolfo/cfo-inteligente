import { Moon, SunMedium } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

export function ThemeToggle() {
  const { dark, toggle } = useTheme();
  return (
    <button onClick={toggle} className="px-2 py-1 rounded-md hover:bg-gray-100 dark:hover:bg-slate-800" aria-label="Tema">
      {dark ? (
        <SunMedium className="w-5 h-5 text-yellow-400" />
      ) : (
        <Moon className="w-5 h-5 text-gray-700 dark:text-slate-200" />
      )}
    </button>
  );
}
export default ThemeToggle;


