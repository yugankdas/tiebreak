import React from 'react';
import { ShieldCheck, ShieldAlert, Cpu, Terminal, Key, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { IntegrationsStatus, GroqStatus, FailproofStatus } from '../../types';

interface GovernanceViewProps {
  status: IntegrationsStatus | null;
  onTestGroq: () => void;
  isTestingGroq: boolean;
}

export const GovernanceView: React.FC<GovernanceViewProps> = ({ status, onTestGroq, isTestingGroq }) => {
  const groq = status?.groq;
  const failproof = status?.failproof;

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--border-subtle)',
      padding: '24px',
      height: 'calc(100vh - 120px)',
      display: 'flex',
      flexDirection: 'column',
      gap: '24px',
      overflowY: 'auto',
    }}>
      <div>
        <h2 style={{ fontSize: '20px', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldCheck size={24} color="var(--accent-emerald)" />
          <span>Integrations & Governance Diagnostics</span>
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Verifiable runtime status for Groq LLM Provider and FailproofAI Policy & Observability daemon.
        </p>
      </div>

      {/* Primary Integration Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '16px',
      }}>
        {/* Groq Card */}
        <div style={{
          padding: '18px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--bg-tertiary)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Primary LLM Provider
              </span>
              <span style={{
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: 
                  groq?.connected ? 'rgba(16, 185, 129, 0.2)' :
                  groq?.configured ? 'rgba(244, 63, 94, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                color: 
                  groq?.connected ? 'var(--accent-emerald)' :
                  groq?.configured ? 'var(--accent-rose)' : 'var(--accent-amber)',
              }}>
                {groq?.connected ? 'CONNECTED' : groq?.status || 'NOT CONFIGURED'}
              </span>
            </div>
            <div style={{ fontSize: '16px', fontWeight: 800 }}>Groq API ({groq?.model || 'llama-3.3-70b-versatile'})</div>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: 1.4 }}>
              {groq?.message || 'Groq connection diagnostics not yet run.'}
            </p>
            {groq?.latency_ms !== null && groq?.latency_ms !== undefined && (
              <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--accent-cyan)' }}>
                Round-trip latency: <strong>{groq.latency_ms}ms</strong>
              </div>
            )}
          </div>

          <button
            onClick={onTestGroq}
            disabled={isTestingGroq}
            style={{
              marginTop: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: 'var(--radius-md)',
              fontSize: '12px',
              fontWeight: 700,
              backgroundColor: 'rgba(99, 102, 241, 0.15)',
              color: 'var(--accent-primary)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
            }}
          >
            <RefreshCw size={13} className={isTestingGroq ? 'animate-spin' : ''} />
            <span>{isTestingGroq ? 'Running Diagnostic...' : 'Test Groq Connection Now'}</span>
          </button>
        </div>

        {/* Failproof Card */}
        <div style={{
          padding: '18px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--bg-tertiary)',
          border: '1px solid var(--border-subtle)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              FailproofAI Integration
            </span>
            <span style={{
              fontSize: '11px',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: 'rgba(6, 182, 212, 0.2)',
              color: 'var(--accent-cyan)',
            }}>
              {failproof?.status || 'TRACE_ONLY'}
            </span>
          </div>
          <div style={{ fontSize: '16px', fontWeight: 800 }}>Daemon & Spool Observability</div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: 1.4 }}>
            {failproof?.enforcement_note || 'Failproof daemon active and spooling events.'}
          </p>
          <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--text-muted)' }}>
            Spool Directory: <code style={{ color: 'var(--accent-primary)' }}>{failproof?.spool_dir || '~/.failproofai/custom-agents/events'}</code>
          </div>
        </div>

        {/* Deterministic Guard Card */}
        <div style={{
          padding: '18px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--bg-tertiary)',
          border: '1px solid var(--border-subtle)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Deterministic Guard
            </span>
            <span style={{
              fontSize: '11px',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: 'rgba(16, 185, 129, 0.2)',
              color: 'var(--accent-emerald)',
            }}>
              ACTIVE (ZERO-BYPASS)
            </span>
          </div>
          <div style={{ fontSize: '16px', fontWeight: 800 }}>TIEBREAK Invariant Engine</div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: 1.4 }}>
            Hard rules, protected tasks (task-07 security review), and permission boundaries are enforced deterministically before any mutation executes.
          </p>
        </div>
      </div>

      {/* Rules & Invariants Table */}
      <div>
        <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px' }}>
          Active Safety Invariants & Policies
        </h3>
        <div style={{
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          overflow: 'hidden',
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-tertiary)', textAlign: 'left', borderBottom: '1px solid var(--border-subtle)' }}>
                <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 600 }}>Rule ID</th>
                <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 600 }}>Policy Scope</th>
                <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 600 }}>Constraint Description</th>
                <th style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontWeight: 600 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: 'var(--accent-primary)' }}>FP-01</td>
                <td style={{ padding: '12px 16px', fontWeight: 600 }}>Security Bypass Prevention</td>
                <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                  task-07 (Security Threat Model Review) is protected; cannot be removed or force-completed without documented proof.
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <CheckCircle size={14} /> ACTIVE
                  </span>
                </td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: 'var(--accent-primary)' }}>FP-02</td>
                <td style={{ padding: '12px 16px', fontWeight: 600 }}>Acyclic Verification</td>
                <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                  Post-execution validation must certify that no new circular dependencies are created in the DAG.
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <CheckCircle size={14} /> ACTIVE
                  </span>
                </td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: 'var(--accent-primary)' }}>FP-03</td>
                <td style={{ padding: '12px 16px', fontWeight: 600 }}>Authorized Sign-off</td>
                <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                  Provisional dependency modifications require explicit Product Manager / Lead Engineer sign-off.
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <CheckCircle size={14} /> ACTIVE
                  </span>
                </td>
              </tr>
              <tr>
                <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: 'var(--accent-primary)' }}>FP-04</td>
                <td style={{ padding: '12px 16px', fontWeight: 600 }}>Capacity Threshold</td>
                <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                  Task reassignments must respect individual engineer capacity (e.g. Eve Thornton 15h/week, Ben Okafor 20h/week).
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <CheckCircle size={14} /> ACTIVE
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
