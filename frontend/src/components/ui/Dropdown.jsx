import { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';

export function Dropdown({ button, children }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, []);
  return (
    <div className="relative" ref={ref}>
      <div onClick={() => setOpen(v => !v)}>{button}</div>
      {open && (
        <div className="absolute right-0 mt-2 w-44 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-md shadow-lg py-1 z-50">
          {children({ close: () => setOpen(false) })}
        </div>
      )}
    </div>
  );
}
Dropdown.propTypes = { button: PropTypes.node, children: PropTypes.func };
export default Dropdown;


