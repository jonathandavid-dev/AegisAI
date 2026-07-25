import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from '../pages/LandingPage';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { DashboardPage } from '../pages/DashboardPage';
import { KnowledgeBasePage } from '../pages/KnowledgeBasePage';
import { ChatPage } from '../pages/ChatPage';
import { SettingsPage } from '../pages/SettingsPage';
import { SearchPage } from '../pages/SearchPage';
import { ProfilePage } from '../pages/ProfilePage';
import { WorkspaceSettingsPage } from '../pages/WorkspaceSettingsPage';
import { EvaluationDashboard } from '../pages/EvaluationDashboard';
import { MainLayout } from '../layouts/MainLayout';
import { ProtectedRoute } from './ProtectedRoute';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Landing Experience */}
      <Route path="/" element={<LandingPage />} />

      {/* Anonymous Authentication Entrypoints */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      
      {/* Protected Session Gateways (Layout Route without path prefix) */}
      <Route element={
        <ProtectedRoute>
          <MainLayout />
        </ProtectedRoute>
      }>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/knowledge" element={<KnowledgeBasePage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/evaluation" element={<EvaluationDashboard />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/settings/workspace" element={<WorkspaceSettingsPage />} />
      </Route>

      {/* Redirect Fallbacks */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
