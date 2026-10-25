import React, { useState } from 'react';
import { Blocker, BlockerType } from '../../types';
import { 
  AlertOctagon, 
  RefreshCw, 
  Sparkles, 
  ChevronRight, 
  CheckCircle,
  HelpCircle,
  Users,
  ShieldAlert,
  Flame
} from 'lucide-react';

interface BlockersViewProps {
  blockers: Blocker[];
  onDetect: () => void;
  isDetecting: boolean;
  onSelectBlockerForResolution: (blocker: Blocker) => void;
}

export const BlockersView: React.FC<BlockersViewProps> = ({
  blockers,
  onDetect,
  isDetecting,
  onSelectBlockerForResolution,
}) => {
  const [selectedBlocker, setSelectedBlocker] = useState<Blocker | null>(
    blockers.length > 0 ? blockers[0] : null
  );

  const getBlockerIcon = (type: BlockerType) => {
    switch (type) {
      case 'CIRCULAR_DEPENDENCY':
        return <AlertOctagon size={18} color="var(--accent-rose)" />;
      case 'MISSING_DECISION':
        return <HelpCircle size={18} color="var(--accent-amber)" />;
      case 'RESOURCE_CONFLICT':
        return <Users size={18} color="var(--accent-cyan)" />;
      case 'DEADLINE_RISK':
        return <Flame size={18} color="var(--accent-rose)" />;
      case 'MANDATORY_REVIEW':
        return <ShieldAlert size={18} color="var(--accent-primary)" />;
      default:
        return <AlertOctagon size={18} color="var(--accent-amber)" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    let bg = 'rgba(244, 63, 94, 0.15)';
    let color = 'var(--accent-rose)';
    if (severity === 'MEDIUM') {
      bg = 'rgba(245, 158, 11, 0.15)';
      color = 'var(--accent-amber)';
    } else if (severity === 'LOW') {
      bg = 'rgba(16, 185, 129, 0.15)';
      color = 'var(--accent-emerald)';
    }
    return (
      <span style={{
        fontSize: '11px',
        fontWeight: 700,
        padding: '2px 8px',
        borderRadius: 'var(--radius-full)',
        backgroundColor: bg,
        color: color,
        border: `1px solid ${color}33`,
      }}>
        {severity}
      </span>
    );
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '24px', height: 'calc(100vh - 120px)' }}>
      {/* Left List of Blockers */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <h2 style={{ fontSize: '15px', fontWeight: 700 }}>Active Deadlocks & Blockers</h2>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {blockers.length} issues identified by analysis engine
            </p>
          </div>
          <button
            onClick={onDetect}
            disabled={isDetecting}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: 'var(--radius-md)',
              fontSize: '12px',
              fontWeight: 600,
              backgroundColor: 'var(--bg-tertiary)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <RefreshCw size={13} className={isDetecting ? 'animate-spin' : ''} />
            <span>Scan Graph</span>
          </button>
        </div>

        {/* Blocker List items */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
          {blockers.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <CheckCircle size={32} color="var(--accent-emerald)" style={{ margin: '0 auto 12px' }} />
              <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>No Deadlocks or Blockers</p>
              <p style={{ fontSize: '12px', marginTop: '4px' }}>All dependencies and workflows are progressing normally.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {blockers.map((blk) => {
                const isSelected = selectedBlocker?.blocker_id === blk.blocker_id;
                const isCircular = blk.blocker_type === 'CIRCULAR_DEPENDENCY';
                return (
                  <div
                    key={blk.blocker_id}
                    onClick={() => setSelectedBlocker(blk)}
                    style={{
                      padding: '14px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isSelected ? 'var(--bg-tertiary)' : 'rgba(255, 255, 255, 0.02)',
                      border: isSelected 
                        ? '1px solid var(--border-active)' 
                        : isCircular 
                          ? '1px solid rgba(244, 63, 94, 0.3)' 
                          : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      boxShadow: isSelected ? 'var(--shadow-glow)' : 'none',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {getBlockerIcon(blk.blocker_type)}
                        <span style={{ fontSize: '13px', fontWeight: 700 }}>
                          {blk.blocker_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      {getSeverityBadge(blk.severity)}
                    </div>
                    <p style={{ fontSize: '12px', color: 'var(--text-primary)', marginTop: '8px', fontWeight: 500, lineHeight: 1.35 }}>
                      {blk.title}
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px', fontSize: '11px', color: 'var(--text-muted)' }}>
                      <span>{blk.affected_task_ids.length} affected task(s)</span>
                      <ChevronRight size={14} color={isSelected ? 'var(--accent-primary)' : 'var(--text-muted)'} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Right Detail Pane */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        padding: '24px',
        overflowY: 'auto',
      }}>
        {selectedBlocker ? (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Header */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontFamily: 'monospace', fontSize: '12px', color: 'var(--accent-primary)' }}>
                  ID: {selectedBlocker.blocker_id}
                </span>
                {getSeverityBadge(selectedBlocker.severity)}
              </div>
              <h1 style={{ fontSize: '20px', fontWeight: 800, marginTop: '6px' }}>
                {selectedBlocker.title}
              </h1>
            </div>

            {/* Explanation card */}
            <div style={{
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--border-subtle)',
            }}>
              <h4 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Autonomous Deadlock Analysis
              </h4>
              <p style={{ fontSize: '14px', lineHeight: 1.5, color: '#e2e8f0' }}>
                {selectedBlocker.explanation}
              </p>
              <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                <strong style={{ fontSize: '12px', color: 'var(--accent-amber)' }}>Root Cause: </strong>
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{selectedBlocker.root_cause}</span>
              </div>
            </div>

            {/* Evidence items */}
            {selectedBlocker.evidence && selectedBlocker.evidence.length > 0 && (
              <div>
                <h4 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Forensic Evidence & Proof Chain
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {selectedBlocker.evidence.map((ev, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '10px 14px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--bg-tertiary)',
                        borderLeft: ev.startsWith('FACT:') 
                          ? '3px solid var(--accent-cyan)' 
                          : ev.startsWith('Cycle') 
                            ? '3px solid var(--accent-rose)' 
                            : '3px solid var(--accent-amber)',
                        fontSize: '12px',
                        fontFamily: 'monospace',
                        color: 'var(--text-primary)',
                      }}
                    >
                      {ev}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Affected and Downstream */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div style={{
                padding: '14px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--border-subtle)',
              }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Directly Affected Tasks ({selectedBlocker.affected_task_ids.length})
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {selectedBlocker.affected_task_ids.map((id) => (
                    <span
                      key={id}
                      style={{
                        padding: '4px 8px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'rgba(244, 63, 94, 0.15)',
                        color: '#fca5a5',
                        fontSize: '11px',
                        fontFamily: 'monospace',
                        fontWeight: 600,
                      }}
                    >
                      {id}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{
                padding: '14px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--border-subtle)',
              }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Downstream Blast Radius ({selectedBlocker.downstream_impact.length})
                </div>
                {selectedBlocker.downstream_impact.length === 0 ? (
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>None directly blocked</span>
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {selectedBlocker.downstream_impact.map((id) => (
                      <span
                        key={id}
                        style={{
                          padding: '4px 8px',
                          borderRadius: 'var(--radius-sm)',
                          backgroundColor: 'var(--bg-tertiary)',
                          color: 'var(--text-secondary)',
                          fontSize: '11px',
                          fontFamily: 'monospace',
                        }}
                      >
                        {id}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Action Trigger */}
            <div style={{
              marginTop: '10px',
              padding: '18px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%)',
              border: '1px solid var(--border-active)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div>
                <h4 style={{ fontSize: '14px', fontWeight: 700 }}>Ready to resolve this deadlock?</h4>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Synthesize multi-action proposals evaluated against governance constraints.
                </p>
              </div>
              <button
                onClick={() => onSelectBlockerForResolution(selectedBlocker)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 18px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '13px',
                  fontWeight: 700,
                  backgroundColor: 'var(--accent-primary)',
                  color: '#fff',
                  boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#4f46e5';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--accent-primary)';
                }}
              >
                <Sparkles size={16} />
                <span>Generate Proposals</span>
              </button>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
            Select a blocker from the left column to view its diagnosis and evidence.
          </div>
        )}
      </div>
    </div>
  );
};
