import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Sidebar } from '../components/Sidebar';

export const MainLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-brand-background text-brand-text flex flex-col">
      {/* Top Banner Navigation */}
      <Navbar />
      
      {/* Side Navigation + Main Content Area */}
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-4rem)] bg-brand-background">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
