import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import ToastContainer from '../common/ToastContainer';
import AddTransactionModal from '../transactions/AddTransactionModal';
import DemoNotice from '../common/DemoNotice';

export default function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[var(--color-outer-bg)] flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        <div className="px-4 pt-3 sm:px-6 lg:px-8">
          <DemoNotice />
        </div>
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>

      <ToastContainer />
      <AddTransactionModal />
    </div>
  );
}
