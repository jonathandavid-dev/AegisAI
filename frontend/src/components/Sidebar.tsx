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
    <aside className="w-64 border-r border-brand-border/60 bg-[#0B0F19] p-4 flex flex-col h-[calc(100vh-4rem)] sticky left-0 z-30">
      <nav className="flex-1 space-y-1">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-brand-primary text-white shadow-lg shadow-brand-primary/20'
                  : 'text-gray-400 hover:text-brand-text hover:bg-brand-surface/65'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-brand-border/40 pt-4 text-center">
        <span className="text-[10px] text-gray-500 font-mono tracking-widest uppercase">
          Aegis Platform v1.0
        </span>
      </div>
    </aside>
  );
};
