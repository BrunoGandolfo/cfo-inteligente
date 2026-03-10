import PropTypes from 'prop-types';
import { Dialog } from '@headlessui/react';
import { motion, AnimatePresence } from 'framer-motion';

export function Modal({ open, onClose, title, children, maxWidth = 'max-w-2xl' }) {
  return (
    <AnimatePresence>
      {open && (
        <Dialog as="div" className="fixed inset-0 z-50" open={open} onClose={onClose}>
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" aria-hidden="true" />
          <div className="fixed inset-0 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 4 }}
              transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
              className={`bg-surface rounded-xl w-full ${maxWidth} max-h-[85vh] overflow-hidden shadow-xl`}
            >
              <div className="border-b border-border px-6 py-4 flex items-center justify-between">
                <Dialog.Title className="text-lg font-semibold text-text-primary">{title}</Dialog.Title>
                <button onClick={onClose} className="text-text-muted hover:text-text-secondary" aria-label="Cerrar">×</button>
              </div>
              <div className="p-6 overflow-y-auto">{children}</div>
            </motion.div>
          </div>
        </Dialog>
      )}
    </AnimatePresence>
  );
}
Modal.propTypes = { open: PropTypes.bool, onClose: PropTypes.func, title: PropTypes.string, children: PropTypes.node, maxWidth: PropTypes.string };
export default Modal;

