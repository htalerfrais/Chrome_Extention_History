import type { ReactNode } from 'react';

interface MainLayoutProps {
  children: ReactNode; // Main dashboard content
  chatComponent: ReactNode; // Chat window component
}

export default function MainLayout({ children, chatComponent }: MainLayoutProps) {
  return (
    <div className="flex h-[calc(100vh-64px)] bg-black">
      {/* Main content area - 70% */}
      <div className="flex-1 overflow-y-auto thin-scrollbar">
        {children}
      </div>
      
      {/* Chat sidebar - 30% */}
      <div className="w-[32%] min-w-[300px] border-l border-white/10 bg-[#080808]">
        {chatComponent}
      </div>
    </div>
  );
}
