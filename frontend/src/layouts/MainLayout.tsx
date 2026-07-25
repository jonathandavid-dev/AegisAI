import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Sidebar } from '../components/Sidebar';
import { CinematicBackdrop } from '../components/ui/CinematicBackdrop';
import { LivingKnowledgeUniverse } from '../components/LivingKnowledgeUniverse';

export const MainLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-brand-background text-brand-text flex flex-col relative overflow-hidden">
      {/* Cinematic Layered Backgrounds & Living Knowledge Universe */}
      <CinematicBackdrop />
      <LivingKnowledgeUniverse />
      
      {/* Top Navigation */}
      <Navbar />
      
      {/* Side Navigation + Main Content Area */}
      <div className="flex flex-1 relative z-10">
        <Sidebar />
        <main className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-4rem)] bg-transparent">
          <div className="animate-fade-in-up">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
