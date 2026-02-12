import { useNavigate, useLocation } from 'react-router-dom';
import { LayoutGrid, BrainCircuit, TrendingDown, Settings } from 'lucide-react';
import SessionList from '../features/sessions/components/SessionList';
import { extensionBridge } from '../services/extensionBridge';

const navItems = [
  { path: '/sessions', label: 'Sessions', icon: LayoutGrid },
  { path: '/quiz', label: 'Quiz', icon: BrainCircuit },
  { path: '/tracking', label: 'Tracking', icon: TrendingDown },
] as const;

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const openSettings = () => {
    const config = extensionBridge.getConfig();
    const constants = extensionBridge.getConstants();
    const currentEnv = config.currentEnvironment;
    const apiUrl = config.getApiBaseUrl();
    const sessionGap = constants.SESSION_GAP_MINUTES;
    alert(`Settings\n\nEnvironment: ${currentEnv}\nAPI URL: ${apiUrl}\nSession Gap: ${sessionGap} minutes\n\nTo switch environments, modify extension/api/config.js`);
  };

  return (
    <div className="flex flex-col h-full bg-[#060606] border-r border-white/10">
      {/* Logo */}
      <div className="px-4 py-4 flex items-center justify-between">
        <h1 className="text-sm tracking-widest uppercase text-white">Obra</h1>
        <button
          onClick={openSettings}
          className="p-1 text-white/40 hover:text-white transition-colors"
          title="Settings"
        >
          <Settings size={16} />
        </button>
      </div>

      {/* Nav buttons */}
      <nav className="flex flex-col gap-1 px-2">
        {navItems.map(({ path, label, icon: Icon }) => {
          const isActive = location.pathname === path;
          return (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`flex items-center gap-3 px-3 py-2 rounded text-left transition-colors ${
                isActive
                  ? 'bg-white/10 text-white'
                  : 'text-white/50 hover:bg-white/5 hover:text-white/70'
              }`}
            >
              <Icon size={16} />
              <span className="text-xs uppercase tracking-[0.2em]">{label}</span>
            </button>
          );
        })}
      </nav>

      {/* Divider */}
      <div className="mx-3 my-3 border-t border-white/10" />

      {/* Session list */}
      <div className="px-2 mb-1">
        <span className="px-3 text-[10px] uppercase tracking-[0.25em] text-white/30">
          Sessions
        </span>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto thin-scrollbar">
        <SessionList />
      </div>
    </div>
  );
}
