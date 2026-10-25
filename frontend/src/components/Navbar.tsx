import React from 'react';
import { 
  Network, 
  AlertOctagon, 
  Sparkles, 
  ShieldCheck, 
  History, 
  RotateCcw,
  Zap,
  Cpu,
  Inbox,
} from 'lucide-react';
import { GroqStatus, UserProfile } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  projectName: string;
  onReset: () => void;
  isResetting: boolean;
  blockerCount: number;
  pendingApprovalsCount?: number;
  groqStatus: GroqStatus | null;
  onTestGroq: () => void;
  isTestingGroq: boolean;
  currentUser: UserProfile | null;
  availableUsers: UserProfile[];
  onSwitchUser: (user: UserProfile) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  projectName,
  onReset,
  isResetting,
  blockerCount,
  pendingApprovalsCount = 0,
  groqStatus,
  onTestGroq,
  isTestingGroq,
  currentUser,
  availableUsers,
  onSwitchUser,
}) => {
  const tabs = [
    { id: 'graph', label: 'Dependency Graph', icon: Network },
    { 
      id: 'blockers', 
      label: 'Deadlocks & Blockers', 
      icon: AlertOctagon,
      badge: blockerCount > 0 ? blockerCount : undefined,
      badgeColor: 'rose'
    },
    { id: 'resolutions', label: 'Resolutions & Proposals', icon: Sparkles },
    {
      id: 'approvals',
      label: 'Approvals Inbox',
      icon: Inbox,
      badge: pendingApprovalsCount > 0 ? pendingApprovalsCount : undefined,
      badgeColor: 'cyan'
    },
    { id: 'audit', label: 'Audit Trail', icon: History },
    { id: 'governance', label: 'Governance', icon: ShieldCheck },
  ];

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      height: '68px',
      backgroundColor: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-subtle)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backdropFilter: 'blur(12px)',
      gap: '16px',
    }}>
      {/* Brand logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexShrink: 0 }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: 'var(--radius-md)',
          background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(99, 102, 241, 0.5)',
        }}>
          <Zap size={20} color="#fff" style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))' }} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '-0.5px' }}>TIEBREAK</span>
            <span style={{ 
              fontSize: '11px', 
              fontWeight: 700, 
              backgroundColor: 'rgba(99, 102, 241, 0.15)', 
              color: 'var(--accent-primary)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>v1.0 Agent</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Project: <strong style={{ color: 'var(--text-primary)' }}>{projectName}</strong>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <nav style={{ display: 'flex', gap: '4px', flex: 1, justifyContent: 'center', overflow: 'hidden' }}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          const badgeColor = tab.badgeColor === 'cyan' ? 'var(--accent-cyan)' : 'var(--accent-rose)';
          const badgeBg = tab.badgeColor === 'cyan' ? 'rgba(6, 182, 212, 0.8)' : 'var(--accent-rose)';
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 12px',
                borderRadius: 'var(--radius-md)',
                fontSize: '12px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#fff' : 'var(--text-secondary)',
                backgroundColor: isActive ? 'var(--bg-tertiary)' : 'transparent',
                border: isActive ? '1px solid var(--border-active)' : '1px solid transparent',
                position: 'relative',
                whiteSpace: 'nowrap',
              }}
            >
              <Icon size={14} color={isActive ? 'var(--accent-primary)' : 'currentColor'} />
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span style={{
                  backgroundColor: badgeBg,
                  color: '#fff',
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '1px 5px',
                  borderRadius: 'var(--radius-full)',
                  marginLeft: '2px',
                }}>
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Right: User switcher + Groq badge + Reset */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
        {/* Identity Pill */}
        {currentUser && (
          <select
            value={currentUser.user_id}
            onChange={(e) => {
              const u = availableUsers.find((usr) => usr.user_id === e.target.value);
              if (u) onSwitchUser(u);
            }}
            title="Switch user identity to test authorization policies"
            style={{
              padding: '5px 8px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: 'rgba(99, 102, 241, 0.12)',
              color: 'var(--accent-primary)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              maxWidth: '180px',
            }}
          >
            {availableUsers.map((u) => (
              <option key={u.user_id} value={u.user_id} style={{ backgroundColor: '#1e293b', color: '#fff' }}>
                {u.name}
              </option>
            ))}
          </select>
        )}

        {/* Groq Live Badge */}
        <div
          onClick={onTestGroq}
          title="Click to run real Groq connection diagnostic"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '5px 10px',
            borderRadius: 'var(--radius-full)',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            backgroundColor: 
              groqStatus?.connected ? 'rgba(16, 185, 129, 0.15)' :
              groqStatus?.configured ? 'rgba(244, 63, 94, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            color: 
              groqStatus?.connected ? 'var(--accent-emerald)' :
              groqStatus?.configured ? 'var(--accent-rose)' : 'var(--accent-amber)',
            border: `1px solid ${
              groqStatus?.connected ? 'rgba(16, 185, 129, 0.3)' :
              groqStatus?.configured ? 'rgba(244, 63, 94, 0.3)' : 'rgba(245, 158, 11, 0.3)'
            }`,
          }}
        >
          <Cpu size={12} />
          <span>
            {isTestingGroq ? 'Testing...' :
             groqStatus?.connected ? `Groq ✓` :
             groqStatus?.configured ? `Groq ✗` : 'Demo Mode'}
          </span>
        </div>

        <button
          onClick={onReset}
          disabled={isResetting}
          title="Reset demo scenario to initial deadlocked state"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 12px',
            borderRadius: 'var(--radius-md)',
            fontSize: '12px',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            backgroundColor: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid var(--border-subtle)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = '#fff';
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text-secondary)';
            e.currentTarget.style.borderColor = 'var(--border-subtle)';
          }}
        >
          <RotateCcw size={13} className={isResetting ? 'animate-spin' : ''} />
          <span>{isResetting ? 'Resetting...' : 'Reset'}</span>
        </button>
      </div>
    </header>
  );
};
