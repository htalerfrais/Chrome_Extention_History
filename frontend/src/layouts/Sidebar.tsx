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
    <div className="flex flex-col h-full bg-bg-deep">
      {/* Logo */}
      <div className="px-5 py-5 flex items-center justify-between">
        <h1 className="text-sm font-semibold tracking-widest uppercase text-text">Obra</h1>
        <button
          onClick={openSettings}
          className="p-1.5 rounded text-text-tertiary hover:text-text-secondary hover:bg-surface transition-colors duration-150"
          title="Settings"
        >
          <Settings size={15} />
        </button>
      </div>

      {/* Nav buttons */}
      <nav className="flex flex-col gap-0.5 px-3">
        {navItems.map(({ path, label, icon: Icon }) => {
          const isActive = location.pathname === path;
          return (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors duration-150 ${
                isActive
                  ? 'bg-accent-muted text-accent-hover border-l-2 border-accent'
                  : 'text-text-secondary hover:bg-surface hover:text-text'
              }`}
            >
              <Icon size={16} strokeWidth={isActive ? 2 : 1.5} />
              <span className="text-xs font-medium tracking-wide">{label}</span>
            </button>
          );
        })}
      </nav>

      {/* Divider */}
      <div className="mx-4 my-4 border-t border-line" />

      {/* Session list header */}
      <div className="px-5 mb-2">
        <span className="text-xxs font-medium uppercase tracking-[0.2em] text-text-ghost">
          Sessions
        </span>
      </div>

      {/* Session list */}
      <div className="flex-1 min-h-0 overflow-y-auto thin-scrollbar">
        <SessionList />
      </div>
    </div>
  );
}
