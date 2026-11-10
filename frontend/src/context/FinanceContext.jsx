import React, { createContext, useContext, useState, useCallback } from 'react';

const FinanceContext = createContext(null);

export function FinanceProvider({ children }) {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isAddTxModalOpen, setIsAddTxModalOpen] = useState(false);
  const [addTxDefaultType, setAddTxDefaultType] = useState('Expense');
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('All');
  const [toasts, setToasts] = useState([]);
  const [notifications, setNotifications] = useState([]);

  const notify = useCallback((message, type = 'success') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const triggerRefresh = useCallback(() => {
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  const filterByCategory = useCallback((category) => {
    setSelectedCategoryFilter(category);
  }, []);

  const openAddTx = useCallback((type = 'Expense') => {
    setAddTxDefaultType(type);
    setIsAddTxModalOpen(true);
  }, []);

  const closeAddTx = useCallback(() => {
    setIsAddTxModalOpen(false);
  }, []);

  return (
    <FinanceContext.Provider
      value={{
        refreshTrigger,
        triggerRefresh,
        isAddTxModalOpen,
        addTxDefaultType,
        openAddTx,
        closeAddTx,
        selectedCategoryFilter,
        filterByCategory,
        notify,
        toasts,
        notifications,
        setNotifications,
      }}
    >
      {children}
    </FinanceContext.Provider>
  );
}

export function useFinance() {
  const context = useContext(FinanceContext);
  if (!context) {
    throw new Error('useFinance must be used within a FinanceProvider');
  }
  return context;
}
