import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './index.css';
import './themes.css';
import DashboardClassic from './components/DashboardClassic';
import DashboardModern from './components/DashboardModern';
import DashboardAnalytics from './components/DashboardAnalytics';
import DashboardExecutive from './components/DashboardExecutive';
import DashboardRouter from './components/DashboardRouter';
import ConfigPage from './components/ConfigPage';
import SetupPage from './components/SetupPage';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement,
);

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardRouter />} />
        <Route path="/classic" element={<DashboardClassic />} />
        <Route path="/modern" element={<DashboardModern />} />
        <Route path="/analytics" element={<DashboardAnalytics />} />
        <Route path="/executive" element={<DashboardExecutive />} />
        <Route path="/config" element={<ConfigPage />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);