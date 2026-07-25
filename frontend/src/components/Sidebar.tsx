import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Database, MessageSquare, Settings, Search, Activity } from 'lucide-react';

interface SidebarItem {
  name: string;
  path: string;
  icon: React.FC<{ className?: string }>;
}

export const Sidebar: React.FC = () => {
  const menuItems: SidebarItem[] = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Knowledge Base', path: '/knowledge', icon: Database },
    { name: 'Semantic Search', path: '/search', icon: Search },
    { name: 'Agent Chat', path: '/chat', icon: MessageSquare },
    { name: 'AI Evaluation', path: '/evaluation', icon: Activity },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-brand-border/40 bg-brand-background/40 backdrop-blur-md p-4 flex flex-col h-[calc(100vh-4rem)] sticky left-0 z-30 justify-between">
      <nav className="space-y-1.5 flex-1">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3.5 px-4.5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 group relative overflow-hidden border ${
                isActive
                  ? 'bg-gradient-to-r from-brand-primary/15 to-brand-accent/5 border-brand-primary/40 text-white shadow-[0_0_15px_rgba(16,185,129,0.1)]'
                  : 'border-transparent text-brand-textSecondary hover:text-white hover:bg-brand-surface/30 hover:border-brand-border/40'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {/* Visual active indicator border strip */}
                {isActive && (
                  <div className="absolute left-0 top-1/4 bottom-1/4 w-1 rounded-r-md bg-brand-accent" />
                )}
                <item.icon className={`w-4.5 h-4.5 transition-transform duration-200 group-hover:scale-105 ${
                  isActive ? 'text-brand-accent' : 'text-brand-textMuted group-hover:text-brand-textSecondary'
                }`} />
                <span>{item.name}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-brand-border/30 pt-4 px-2 flex flex-col gap-1 select-none">
        <span className="text-[9px] text-brand-textMuted font-mono tracking-widest uppercase block">
          Aegis Platform v3.0
        </span>
        <span className="text-[8px] text-[#4B5563] font-mono block">
          Enterprise Intelligence OS
        </span>
      </div>
    </aside>
  );
};
