import React, { ReactNode } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { WorkspaceProvider } from '../context/WorkspaceContext';
import { KnowledgeUniverseProvider } from '../context/KnowledgeUniverseContext';

export const AppProviders: React.FC<{ children: ReactNode }> = ({ children }) => {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <WorkspaceProvider>
          <KnowledgeUniverseProvider>
            {children}
          </KnowledgeUniverseProvider>
        </WorkspaceProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};
