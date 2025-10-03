import { useState } from 'react';
import toast from 'react-hot-toast';

export default function useOperacionForm(initialState, onSuccess) {
  const [formData, setFormData] = useState(initialState);
  const [isLoading, setIsLoading] = useState(false);

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setFormData(initialState);
  };

  const handleSubmit = async (apiCall) => {
    setIsLoading(true);
    try {
      await apiCall(formData);
      toast.success('Operación registrada exitosamente');
      resetForm();
      if (onSuccess) onSuccess();
    } catch (error) {
      toast.error(error.message || 'Error al registrar operación');
    } finally {
      setIsLoading(false);
    }
  };

  return {
    formData,
    updateField,
    resetForm,
    handleSubmit,
    isLoading,
    setFormData
  };
}

