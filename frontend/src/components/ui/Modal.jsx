import { useEffect, useId } from 'react';
import PropTypes from 'prop-types';
import { motion, AnimatePresence } from 'framer-motion';

export function Modal({ open, onClose, title, children, maxWidth = 'max-w-2xl' }) {
  const titleId = useId();

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-labelledby={titleId}>
          <button
            type="button"
            className="fixed inset-0 bg-black/40 backdrop-blur-sm"
            aria-label="Cerrar modal"
            onClick={onClose}
          />
          <div className="fixed inset-0 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 4 }}
              transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
              className={`bg-surface rounded-xl w-full ${maxWidth} max-h-[85vh] overflow-hidden shadow-xl`}
              onClick={(event) => event.stopPropagation()}
            >
              <div className="border-b border-border px-6 py-4 flex items-center justify-between">
                <h2 id={titleId} className="text-lg font-semibold text-text-primary">{title}</h2>
                <button onClick={onClose} className="text-text-muted hover:text-text-secondary" aria-label="Cerrar">×</button>
              </div>
              <div className="p-6 overflow-y-auto">{children}</div>
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
}
Modal.propTypes = { open: PropTypes.bool, onClose: PropTypes.func, title: PropTypes.string, children: PropTypes.node, maxWidth: PropTypes.string };
export default Modal;
