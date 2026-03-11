import { useState, useRef, useEffect, useCallback } from 'react';
import axiosClient from '../../services/api/axiosClient';

function AutocompleteInput({ value, onChange, searchEndpoint, placeholder, label, id, required }) {
  const [suggestions, setSuggestions] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const wrapperRef = useRef(null);
  const debounceRef = useRef(null);

  const fetchSuggestions = useCallback(async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }
    try {
      const response = await axiosClient.get(`${searchEndpoint}?q=${encodeURIComponent(query)}`);
      const results = response.data || [];
      setSuggestions(results);
      setIsOpen(results.length > 0);
      setActiveIndex(-1);
    } catch {
      setSuggestions([]);
      setIsOpen(false);
    }
  }, [searchEndpoint]);

  const handleChange = (e) => {
    const val = e.target.value;
    onChange(val);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(val), 300);
  };

  const handleSelect = (nombre) => {
    onChange(nombre);
    setSuggestions([]);
    setIsOpen(false);
    setActiveIndex(-1);
  };

  const handleKeyDown = (e) => {
    if (!isOpen || suggestions.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      handleSelect(suggestions[activeIndex].nombre);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setActiveIndex(-1);
    }
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
        setActiveIndex(-1);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, []);

  return (
    <div ref={wrapperRef} className="relative">
      {label && (
        <label htmlFor={id} className="block text-xs font-medium text-text-secondary">
          {label}
        </label>
      )}
      <input
        id={id}
        type="text"
        required={required}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={() => { if (suggestions.length > 0) setIsOpen(true); }}
        autoComplete="off"
        placeholder={placeholder}
        className="w-full px-1 py-1 border border-border rounded text-xs bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
      />
      {isOpen && suggestions.length > 0 && (
        <ul className="absolute z-50 w-full mt-0.5 max-h-40 overflow-y-auto rounded border border-border-strong bg-surface shadow-lg">
          {suggestions.map((item, idx) => (
            <li
              key={item.id}
              onMouseDown={() => handleSelect(item.nombre)}
              onMouseEnter={() => setActiveIndex(idx)}
              className={`px-2 py-1.5 text-xs cursor-pointer transition-colors ${
                idx === activeIndex
                  ? 'bg-accent/20 text-text-primary'
                  : 'text-text-secondary hover:bg-accent/10'
              }`}
            >
              {item.nombre}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default AutocompleteInput;
