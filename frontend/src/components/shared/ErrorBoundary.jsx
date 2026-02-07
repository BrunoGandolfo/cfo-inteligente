import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error capturado por ErrorBoundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-8">
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-md text-center">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              Algo salió mal
            </h2>
            <p className="text-gray-600 mb-6">
              Ocurrió un error inesperado. Por favor recargá la página.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-amber-500 hover:bg-amber-600 text-white font-medium py-2 px-6 rounded-lg"
            >
              Recargar página
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
