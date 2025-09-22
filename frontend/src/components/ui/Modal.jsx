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
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              className={`bg-white dark:bg-slate-900 rounded-lg w-full ${maxWidth} max-h-[85vh] overflow-hidden shadow-elevated`}
            >
              <div className="border-b border-gray-200 dark:border-slate-800 px-6 py-4 flex items-center justify-between">
                <Dialog.Title className="text-lg font-semibold text-gray-900 dark:text-white">{title}</Dialog.Title>
                <button onClick={onClose} className="text-gray-400 hover:text-gray-600" aria-label="Cerrar">×</button>
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


