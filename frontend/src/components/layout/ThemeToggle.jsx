import { Moon, SunMedium } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

export function ThemeToggle() {
  const { dark, toggle } = useTheme();
  return (
    <button onClick={toggle} className="px-2 py-1 rounded-md hover:bg-gray-100 dark:hover:bg-slate-800" aria-label="Tema">
      {dark ? <SunMedium className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
    </button>
  );
}
export default ThemeToggle;


