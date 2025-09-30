import React, { createContext, useContext, useState } from 'react';
import BlochSpinner from '../components/BlochSpinner';

const LoadingContext = createContext();

export const useLoading = () => {
  const context = useContext(LoadingContext);
  if (!context) {
    throw new Error('useLoading must be used within a LoadingProvider');
  }
  return context;
};

export const LoadingProvider = ({ children }) => {
  const [loadingStates, setLoadingStates] = useState({});

  const setLoading = (key, isLoading, message = 'Processing...') => {
    setLoadingStates(prev => ({
      ...prev,
      [key]: isLoading ? { isLoading: true, message } : { isLoading: false, message: null }
    }));
  };

  const isLoading = (key) => {
    return loadingStates[key]?.isLoading || false;
  };

  const getLoadingMessage = (key) => {
    return loadingStates[key]?.message || 'Processing...';
  };

  const hasAnyLoading = () => {
    return Object.values(loadingStates).some(state => state.isLoading);
  };

  const getCurrentLoadingMessage = () => {
    const activeState = Object.values(loadingStates).find(state => state.isLoading);
    return activeState?.message || 'Processing...';
  };

  return (
    <LoadingContext.Provider 
      value={{ 
        setLoading, 
        isLoading, 
        getLoadingMessage,
        hasAnyLoading,
        getCurrentLoadingMessage
      }}
    >
      {children}
      {/* Global loading spinner in bottom-right corner */}
      {hasAnyLoading() && (
        <BlochSpinner 
          className="bloch-spinner-fixed"
          size={40}
          speed={1.5}
          ariaLabel={getCurrentLoadingMessage()}
        />
      )}
    </LoadingContext.Provider>
  );
};