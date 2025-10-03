// MainLayout component - 70/30 layout for dashboard and chat
// Provides responsive layout with main content area and chat sidebar

import { ReactNode } from 'react';

interface MainLayoutProps {
  children: ReactNode; // Main dashboard content
  chatComponent: ReactNode; // Chat window component
}

export default function MainLayout({ children, chatComponent }: MainLayoutProps) {
  return (
    <div className="main-layout">
      {/* Main content area - 70% */}
      <div className="main-content">
        {children}
      </div>
      
      {/* Chat sidebar - 30% */}
      <div className="chat-sidebar">
        {chatComponent}
      </div>
    </div>
  );
}
