import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles } from 'lucide-react';
import axiosClient from '../../services/api/axiosClient';

export default function WelcomeModal({ isOpen, onClose, frasePreCargada, fraseLoading }) {
  const [frase, setFrase] = useState('');
  const [displayedText, setDisplayedText] = useState('');
  const [loading, setLoading] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const typingRef = useRef(null);
  const onCloseRef = useRef(onClose);
  const hasFetchedRef = useRef(false);
  const DURATION = 8000; // 8 segundos

  // Reset estados cuando se cierra el modal
  useEffect(() => {
    if (!isOpen) {
      setFrase('');
      setDisplayedText('');
      setLoading(true);
      setIsTyping(false);
      hasFetchedRef.current = false;
    }
  }, [isOpen]);

  // Usar frase pre-cargada cuando esté disponible
  useEffect(() => {
    if (isOpen && frasePreCargada && !fraseLoading && !frase) {
      setFrase(frasePreCargada);
      setLoading(false);
      hasFetchedRef.current = true;
    }
  }, [isOpen, frasePreCargada, fraseLoading, frase]);

  // Fetch de frase (con protección contra doble ejecución)
  useEffect(() => {
    if (!isOpen) return;
    
    // Si ya tenemos frase pre-cargada, usarla (no hacer fetch)
    if (frasePreCargada && !fraseLoading) return;
    
    // Si está cargando la frase pre-cargada, esperar
    if (fraseLoading) return;
    
    // Prevenir doble ejecución
    if (hasFetchedRef.current) return;
    
    hasFetchedRef.current = true;
    
    const fetchFrase = async () => {
      try {
        const { data } = await axiosClient.get('/api/frases/motivacional');
        setFrase(data.frase);
      } catch {
        setFrase('¡A seguir construyendo con excelencia!');
      } finally {
        setLoading(false);
      }
    };

    fetchFrase();
  }, [isOpen, frasePreCargada, fraseLoading]);

  // Mantener ref de onClose actualizada
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  // Efecto typewriter
  useEffect(() => {
    if (!frase || loading) return;
    
    // Limpiar primero
    setDisplayedText('');
    setIsTyping(false);
    
    // Delay para asegurar que estado se actualizó
    const timeout = setTimeout(() => {
      setIsTyping(true);
      let index = 0;
      
      typingRef.current = setInterval(() => {
        if (index < frase.length) {
          setDisplayedText(frase.slice(0, index + 1));
          index++;
        } else {
          clearInterval(typingRef.current);
          setIsTyping(false);
        }
      }, 35);
    }, 50);
    
    return () => {
      clearTimeout(timeout);
      if (typingRef.current) clearInterval(typingRef.current);
    };
  }, [frase, loading]);

  // Auto-cerrar 5 segundos DESPUÉS de terminar el typewriter
  useEffect(() => {
    if (!isOpen || isTyping || !displayedText) return;
    
    const timer = setTimeout(() => {
      onCloseRef.current();
    }, 5000);
    
    return () => {
      clearTimeout(timer);
    };
  }, [isOpen, isTyping, displayedText]); // SIN onClose en dependencias

  const userName = localStorage.getItem('userName') || 'Usuario';

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm"
        >
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.3 }}
            className="relative mx-4 max-w-md w-full bg-slate-900 border border-slate-700/50 rounded-lg shadow-xl overflow-hidden"
          >
            {/* Barra de progreso superior */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-slate-800">
              <motion.div
                initial={{ width: '100%' }}
                animate={{ width: '0%' }}
                transition={{ duration: DURATION / 1000, ease: 'linear' }}
                className="h-full bg-indigo-500"
              />
            </div>

            {/* Header */}
            <div className="flex items-center justify-between px-5 pt-5 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <span className="text-sm font-medium text-slate-400">CFO Inteligente</span>
              </div>
              <button
                onClick={onClose}
                className="text-slate-500 hover:text-slate-300 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* Contenido */}
            <div className="px-5 pb-6">
              <h2 className="text-lg font-semibold text-white mb-4">
                Bienvenido, {userName}
              </h2>
              
              {loading ? (
                <div className="flex items-center gap-2 py-2">
                  <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                  <span className="text-slate-400 text-sm">Preparando tu mensaje...</span>
                </div>
              ) : (
                <p className="text-slate-300 leading-relaxed min-h-[60px]">
                  {displayedText}
                  {isTyping && (
                    <span className="inline-block w-0.5 h-4 bg-indigo-400 ml-0.5 animate-pulse align-middle" />
                  )}
                </p>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
