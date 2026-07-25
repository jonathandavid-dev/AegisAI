import React from 'react';
import { LucideIcon } from 'lucide-react';

// ==========================================
// 1. Button Primitive
// ==========================================
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyle = 'inline-flex items-center justify-center font-semibold transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer';
  
  const variants = {
    primary: 'bg-gradient-to-r from-brand-primary to-brand-primaryHover text-white hover:opacity-95 hover:shadow-[0_0_20px_rgba(59,130,246,0.25)] border border-transparent',
    secondary: 'bg-brand-surface/40 hover:bg-brand-surface/80 border border-brand-border text-brand-text hover:border-brand-borderHover',
    danger: 'bg-gradient-to-r from-red-600 to-red-700 text-white hover:opacity-95 hover:shadow-[0_0_20px_rgba(220,38,38,0.25)]',
    ghost: 'bg-transparent hover:bg-brand-surface/40 text-brand-textSecondary hover:text-white',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-xs rounded-lg gap-1.5',
    md: 'px-5 py-2.5 text-sm rounded-xl gap-2',
    lg: 'px-6 py-3.5 text-base rounded-2xl gap-2.5',
  };

  return (
    <button
      disabled={disabled || loading}
      className={`${baseStyle} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin shrink-0" />
      ) : null}
      {children}
    </button>
  );
};

// ==========================================
// 2. Card Primitive
// ==========================================
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glow?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, glow, className = '', ...props }) => {
  return (
    <div
      className={`glass-card ${glow ? 'hover:border-brand-primary/50 hover:shadow-[0_0_30px_rgba(59,130,246,0.08)]' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

// ==========================================
// 3. MetricCard Primitive
// ==========================================
interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  iconColor?: string;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-brand-primary',
  className = '',
}) => {
  return (
    <Card className={`relative overflow-hidden group ${className}`} glow>
      <div className="flex justify-between items-start mb-3">
        <span className="text-xs font-semibold text-brand-textMuted uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-lg bg-brand-surface/60 border border-brand-border/40 ${iconColor} group-hover:scale-110 transition-transform duration-300`}>
            <Icon className="w-4.5 h-4.5" />
          </div>
        )}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-extrabold text-white tracking-tight">{value}</span>
      </div>
      {subtitle && <p className="text-xs text-brand-textSecondary mt-2">{subtitle}</p>}
    </Card>
  );
};

// ==========================================
// 4. Input Primitive
// ==========================================
export const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement>> = ({ className = '', ...props }) => {
  return (
    <input
      className={`glass-input w-full ${className}`}
      {...props}
    />
  );
};

// ==========================================
// 5. Textarea Primitive
// ==========================================
export const Textarea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement>> = ({ className = '', ...props }) => {
  return (
    <textarea
      className={`glass-input w-full min-h-[100px] resize-none ${className}`}
      {...props}
    />
  );
};

// ==========================================
// 6. Select Primitive
// ==========================================
export const Select: React.FC<React.SelectHTMLAttributes<HTMLSelectElement>> = ({ children, className = '', ...props }) => {
  return (
    <select
      className={`glass-input appearance-none pr-10 cursor-pointer ${className}`}
      {...props}
    >
      {children}
    </select>
  );
};

// ==========================================
// 7. Avatar Primitive
// ==========================================
interface AvatarProps {
  name?: string;
  src?: string;
  size?: 'sm' | 'md' | 'lg';
  status?: 'online' | 'offline' | 'away';
  className?: string;
}

export const Avatar: React.FC<AvatarProps> = ({
  name = '',
  src,
  size = 'md',
  status,
  className = '',
}) => {
  const sizes = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-14 h-14 text-lg',
  };

  const statusColors = {
    online: 'bg-green-400',
    offline: 'bg-gray-500',
    away: 'bg-yellow-400',
  };

  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="relative inline-block shrink-0">
      <div className={`rounded-xl border border-brand-border/60 bg-[#162035] text-brand-accent flex items-center justify-center font-bold overflow-hidden shadow-sm ${sizes[size]} ${className}`}>
        {src ? (
          <img src={src} alt={name} className="w-full h-full object-cover" />
        ) : (
          <span>{initials || '?'}</span>
        )}
      </div>
      {status && (
        <span className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border border-brand-background ${statusColors[status]} animate-pulse`} />
      )}
    </div>
  );
};

// ==========================================
// 8. Badge Primitive
// ==========================================
interface BadgeProps {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  className?: string;
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'primary', className = '' }) => {
  const variants = {
    primary: 'bg-brand-primary/10 border-brand-primary/30 text-brand-primary',
    secondary: 'bg-brand-surfaceElevated border-brand-border text-brand-textSecondary',
    success: 'bg-green-500/10 border-green-500/30 text-green-400',
    warning: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
    danger: 'bg-red-500/10 border-red-500/30 text-red-400',
  };

  return (
    <span className={`px-2 py-0.5 rounded-md border text-[10px] font-mono uppercase tracking-wider font-semibold ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};

// ==========================================
// 9. Progress Bar Primitive
// ==========================================
interface ProgressProps {
  value: number;
  max?: number;
  className?: string;
  glow?: boolean;
}

export const Progress: React.FC<ProgressProps> = ({ value, max = 100, className = '', glow }) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  return (
    <div className={`w-full bg-[#0D0D0D] border border-brand-border/40 rounded-full h-2.5 overflow-hidden ${className}`}>
      <div
        className={`bg-gradient-to-r from-brand-primary to-brand-accent h-full rounded-full transition-all duration-300 ${glow ? 'shadow-[0_0_10px_rgba(52,211,153,0.5)]' : ''}`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

// ==========================================
// 10. Skeleton Loader Primitive
// ==========================================
export const Skeleton: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', ...props }) => {
  return (
    <div
      className={`shimmer-loading animate-shimmer rounded-xl border border-brand-border/40 ${className}`}
      {...props}
    />
  );
};

// ==========================================
// 11. Empty State Primitive
// ==========================================
interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, description, icon: Icon, action }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 border border-dashed border-brand-border/60 rounded-2xl bg-brand-surface/20 text-center max-w-md mx-auto">
      {Icon && (
        <div className="p-4 rounded-full bg-brand-surface/40 border border-brand-border/60 text-brand-textMuted mb-4">
          <Icon className="w-8 h-8" />
        </div>
      )}
      <h3 className="text-base font-bold text-white mb-1">{title}</h3>
      <p className="text-xs text-brand-textSecondary mb-5 leading-relaxed">{description}</p>
      {action}
    </div>
  );
};

// ==========================================
// 12. Loading Spinner Primitive
// ==========================================
export const LoadingSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
  const sizes = {
    sm: 'w-5 h-5 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  };
  return (
    <div className="flex items-center justify-center">
      <div className={`border-brand-primary/20 border-t-brand-primary rounded-full animate-spin ${sizes[size]}`} />
    </div>
  );
};
