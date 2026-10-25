import React from 'react';
import { AuditEvent } from '../../types';
import { History, Shield, CheckCircle, FileText, ArrowRight } from 'lucide-react';

interface AuditTrailViewProps {
  events: AuditEvent[];
}

export const AuditTrailView: React.FC<AuditTrailViewProps> = ({ events }) => {
  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--border-subtle)',
      padding: '24px',
      height: 'calc(100vh - 120px)',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <History size={20} color="var(--accent-primary)" />
          <span>Cryptographic Audit & Execution Trail</span>
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Append-only verifiable ledger recording every state mutation, blocker detection, and human approval.
        </p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {events.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
            No audit events recorded yet. Perform actions like detecting blockers or executing resolutions.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {events.map((ev) => (
              <div
                key={ev.event_id}
                style={{
                  padding: '16px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'rgba(99, 102, 241, 0.2)',
                      color: 'var(--accent-primary)',
                      fontFamily: 'monospace',
                    }}>
                      {ev.action}
                    </span>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#fff' }}>
                      Actor: {ev.actor}
                    </span>
                    {ev.target && (
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                        Target: {ev.target}
                      </span>
                    )}
                  </div>

                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                    {new Date(ev.timestamp).toLocaleString()}
                  </span>
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text-primary)', marginBottom: '6px' }}>
                  <strong>Input:</strong> {ev.input_summary}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--accent-cyan)', marginBottom: '8px' }}>
                  <strong>Outcome:</strong> {ev.outcome}
                </div>

                {/* Event details snapshot */}
                <div style={{
                  padding: '10px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'rgba(0, 0, 0, 0.3)',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  color: 'var(--text-secondary)',
                  overflowX: 'auto',
                }}>
                  <pre>{JSON.stringify({
                    event_id: ev.event_id,
                    action: ev.action,
                    target: ev.target,
                    error_details: ev.error_details,
                    previous_revision: ev.previous_revision,
                    resulting_revision: ev.resulting_revision,
                  }, null, 2)}</pre>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
