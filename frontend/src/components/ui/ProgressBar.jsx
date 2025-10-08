/**
 * ProgressBar Component
 * 
 * Barra de progreso animada.
 * 
 * @author Sistema CFO Inteligente
 * @date Octubre 2025
 */

import React from 'react';

export const ProgressBar = ({ progress, label, showPercentage = true }) => {
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
          {showPercentage && (
            <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
              {progress}%
            </span>
          )}
        </div>
      )}
      
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
        <div
          className="bg-gradient-to-r from-blue-500 to-blue-600 dark:from-blue-600 dark:to-blue-700 h-full rounded-full transition-all duration-300 ease-out"
          style={{ width: `${Math.min(progress, 100)}%` }}
        >
          <div className="h-full w-full bg-white/20 animate-pulse" />
        </div>
      </div>
    </div>
  );
};

