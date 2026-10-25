import React, { useState } from 'react';
import { ResolutionProposal, Blocker, ExecutionResult, VerificationResult, GroqStatus } from '../../types';
import { 
  Sparkles, 
  CheckCircle2, 
  XCircle, 
  Play, 
  ShieldCheck, 
  ShieldAlert, 
  RotateCcw,
  AlertTriangle,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  Cpu,
  Info
} from 'lucide-react';

interface ResolutionsViewProps {
  proposals: ResolutionProposal[];
  blockers: Blocker[];
  selectedBlocker: Blocker | null;
  onSelectBlocker: (blocker: Blocker) => void;
  onGenerateProposals: (blockerId: string) => void;
  isGenerating: boolean;
  onApprove: (resolutionId: string, approver: string) => void;
  onReject: (resolutionId: string, reason: string) => void;
  onExecute: (resolutionId: string) => void;
  isExecuting: boolean;
  lastExecutionResult: ExecutionResult | null;
  lastVerificationResult: VerificationResult | null;
  groqStatus: GroqStatus | null;
}

export const ResolutionsView: React.FC<ResolutionsViewProps> = ({
  proposals,
  blockers,
  selectedBlocker,
  onSelectBlocker,
  onGenerateProposals,
  isGenerating,
  onApprove,
  onReject,
  onExecute,
  isExecuting,
  lastExecutionResult,
  lastVerificationResult,
  groqStatus,
}) => {
  const [selectedProposalId, setSelectedProposalId] = useState<string | null>(
    proposals.length > 0 ? (proposals[0].resolution_id || proposals[0].proposal_id || null) : null
  );
  const [approverName, setApproverName] = useState('Alice Chen (PM)');

  const activeProposal = proposals.find(
    (p) => (p.resolution_id === selectedProposalId || p.proposal_id === selectedProposalId)
  ) || proposals[0];

  const isLLMProposal = activeProposal && !activeProposal.is_fallback;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '24px', height: 'calc(100vh - 120px)' }}>
      {/* Sidebar: Blocker selection & Proposal list */}
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
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ fontSize: '15px', fontWeight: 700 }}>Resolution Engine</h2>
            {groqStatus?.connected ? (
              <span style={{
                fontSize: '10px',
                fontWeight: 700,
                color: 'var(--accent-emerald)',
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                padding: '2px 6px',
                borderRadius: 'var(--radius-full)',
              }}>
                Groq Live
              </span>
            ) : (
              <span style={{
                fontSize: '10px',
                fontWeight: 700,
                color: 'var(--accent-amber)',
                backgroundColor: 'rgba(245, 158, 11, 0.15)',
                padding: '2px 6px',
                borderRadius: 'var(--radius-full)',
              }}>
                Demo Fallback
              </span>
            )}
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Select a deadlock to propose actionable fixes
          </p>

          <div style={{ marginTop: '12px' }}>
            <label style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Target Deadlock:
            </label>
            <select
              value={selectedBlocker?.blocker_id || ''}
              onChange={(e) => {
                const b = blockers.find((x) => x.blocker_id === e.target.value);
                if (b) onSelectBlocker(b);
              }}
              style={{
                width: '100%',
                marginTop: '4px',
                padding: '8px 10px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--bg-tertiary)',
                color: '#fff',
                border: '1px solid var(--border-subtle)',
                fontSize: '12px',
              }}
            >
              <option value="" disabled>-- Select a Deadlock --</option>
              {blockers.map((b) => (
                <option key={b.blocker_id} value={b.blocker_id}>
                  [{b.severity}] {b.blocker_type.replace(/_/g, ' ')} ({b.affected_task_ids.join(', ')})
                </option>
              ))}
            </select>

            {selectedBlocker && (
              <button
                onClick={() => onGenerateProposals(selectedBlocker.blocker_id)}
                disabled={isGenerating}
                style={{
                  width: '100%',
                  marginTop: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '9px 14px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '12px',
                  fontWeight: 700,
                  backgroundColor: 'var(--accent-primary)',
                  color: '#fff',
                }}
              >
                <Sparkles size={14} className={isGenerating ? 'animate-spin' : ''} />
                <span>
                  {isGenerating 
                    ? (groqStatus?.connected ? 'Groq LLM Reasoning...' : 'Synthesizing Fallback...') 
                    : (groqStatus?.connected ? 'Synthesize with Groq' : 'Synthesize Options')}
                </span>
              </button>
            )}
          </div>
        </div>

        {/* Proposals List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', padding: '0 4px' }}>
            Generated Proposals ({proposals.length})
          </div>

          {proposals.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px 10px', color: 'var(--text-muted)', fontSize: '12px' }}>
              No proposals generated yet. Pick a target deadlock above and click "Synthesize".
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {proposals.map((prop) => {
                const pId = prop.resolution_id || prop.proposal_id || '';
                const isSelected = ((activeProposal?.resolution_id || activeProposal?.proposal_id) === pId);
                return (
                  <div
                    key={pId}
                    onClick={() => setSelectedProposalId(pId)}
                    style={{
                      padding: '12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isSelected ? 'var(--bg-tertiary)' : 'rgba(255, 255, 255, 0.02)',
                      border: isSelected ? '1px solid var(--border-active)' : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        {prop.is_fallback ? (
                          <span style={{
                            fontSize: '9px',
                            fontWeight: 700,
                            padding: '1px 5px',
                            borderRadius: 'var(--radius-sm)',
                            backgroundColor: 'rgba(245, 158, 11, 0.2)',
                            color: 'var(--accent-amber)',
                          }}>
                            FALLBACK
                          </span>
                        ) : (
                          <span style={{
                            fontSize: '9px',
                            fontWeight: 700,
                            padding: '1px 5px',
                            borderRadius: 'var(--radius-sm)',
                            backgroundColor: 'rgba(99, 102, 241, 0.2)',
                            color: 'var(--accent-primary)',
                          }}>
                            GROQ LLM
                          </span>
                        )}

                        {prop.is_feasible ? (
                          <span style={{
                            fontSize: '9px',
                            fontWeight: 700,
                            padding: '1px 5px',
                            borderRadius: 'var(--radius-sm)',
                            backgroundColor: 'rgba(16, 185, 129, 0.2)',
                            color: 'var(--accent-emerald)',
                          }}>
                            FEASIBLE
                          </span>
                        ) : (
                          <span style={{
                            fontSize: '9px',
                            fontWeight: 700,
                            padding: '1px 5px',
                            borderRadius: 'var(--radius-sm)',
                            backgroundColor: 'rgba(244, 63, 94, 0.2)',
                            color: 'var(--accent-rose)',
                          }}>
                            INFEASIBLE
                          </span>
                        )}
                      </div>

                      <span style={{
                        fontSize: '10px',
                        fontWeight: 700,
                        padding: '1px 6px',
                        borderRadius: 'var(--radius-full)',
                        backgroundColor: 
                          prop.execution_state === 'EXECUTED' ? 'rgba(16, 185, 129, 0.2)' :
                          prop.approval_state === 'APPROVED' ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                        color:
                          prop.execution_state === 'EXECUTED' ? 'var(--accent-emerald)' :
                          prop.approval_state === 'APPROVED' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                      }}>
                        {prop.execution_state === 'EXECUTED' ? 'EXECUTED' : prop.approval_state}
                      </span>
                    </div>

                    <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>{prop.title}</h4>
                    <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: 1.3 }}>
                      {(prop.description || prop.summary || '').slice(0, 75)}…
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Main Proposal Detail Area */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        padding: '24px',
        overflowY: 'auto',
      }}>
        {activeProposal ? (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Header info */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <span style={{ fontFamily: 'monospace', fontSize: '11px', color: 'var(--accent-primary)' }}>
                  {activeProposal.resolution_id || activeProposal.proposal_id}
                </span>

                {isLLMProposal ? (
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    backgroundColor: 'rgba(99, 102, 241, 0.25)',
                    color: 'var(--accent-primary)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    border: '1px solid rgba(99, 102, 241, 0.4)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}>
                    <Cpu size={12} /> Groq Generated
                  </span>
                ) : (
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    backgroundColor: 'rgba(245, 158, 11, 0.15)',
                    color: 'var(--accent-amber)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                  }}>
                    Deterministic Fallback
                  </span>
                )}

                <span style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  backgroundColor: activeProposal.is_feasible ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                  color: activeProposal.is_feasible ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                }}>
                  {activeProposal.is_feasible ? 'CONSTRAINTS SATISFIED' : 'CONSTRAINT VIOLATION'}
                </span>

                {activeProposal.score !== null && (
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    backgroundColor: 'rgba(6, 182, 212, 0.15)',
                    color: 'var(--accent-cyan)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                  }}>
                    Score: {activeProposal.score}/100
                  </span>
                )}
              </div>

              <h1 style={{ fontSize: '22px', fontWeight: 800 }}>{activeProposal.title}</h1>
              <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: 1.5 }}>
                {activeProposal.description || activeProposal.summary}
              </p>

              {activeProposal.score_explanation && (
                <div style={{
                  marginTop: '8px',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'rgba(6, 182, 212, 0.08)',
                  border: '1px solid rgba(6, 182, 212, 0.2)',
                  fontSize: '12px',
                  color: '#bae6fd',
                }}>
                  <strong>Scoring Rationale:</strong> {activeProposal.score_explanation}
                </div>
              )}

              {!activeProposal.is_feasible && activeProposal.infeasibility_reason && (
                <div style={{
                  marginTop: '8px',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'rgba(244, 63, 94, 0.1)',
                  border: '1px solid rgba(244, 63, 94, 0.3)',
                  fontSize: '12px',
                  color: '#fecdd3',
                }}>
                  <strong>Deterministic Invariant Block:</strong> {activeProposal.infeasibility_reason}
                </div>
              )}
            </div>

            {/* Actions list */}
            <div>
              <h3 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '10px' }}>
                Proposed Mutation Plan ({(activeProposal.proposed_actions || []).length} atomic actions)
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {(activeProposal.proposed_actions || []).map((act, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '12px 16px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--bg-tertiary)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: 'var(--radius-sm)',
                          backgroundColor: 'rgba(6, 182, 212, 0.15)',
                          color: 'var(--accent-cyan)',
                          fontFamily: 'monospace',
                        }}>
                          {act.action_type}
                        </span>
                        {act.target_task_id && (
                          <span style={{ fontSize: '12px', fontFamily: 'monospace', color: 'var(--accent-primary)', fontWeight: 600 }}>
                            Target: {act.target_task_id}
                          </span>
                        )}
                      </div>
                      <p style={{ fontSize: '13px', color: '#fff', marginTop: '4px' }}>
                        {act.description}
                      </p>
                    </div>

                    <span style={{
                      fontSize: '10px',
                      fontWeight: 700,
                      color: 'var(--accent-emerald)',
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                      padding: '3px 8px',
                      borderRadius: 'var(--radius-sm)',
                    }}>
                      ALLOWLISTED
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Tradeoffs Evaluation */}
            {activeProposal.trade_offs && activeProposal.trade_offs.length > 0 && (
              <div>
                <h3 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '10px' }}>
                  Impact & Tradeoffs Analysis
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
                  {activeProposal.trade_offs.map((t, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '12px',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'rgba(255, 255, 255, 0.02)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {typeof t === 'string' ? t : JSON.stringify(t)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Deterministic Invariant Checks */}
            <div>
              <h3 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '10px' }}>
                Deterministic Governance Checks ({(activeProposal.constraint_checks || []).length} Invariants)
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {(activeProposal.constraint_checks || []).map((c, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: c.result === 'PASS' ? 'rgba(16, 185, 129, 0.05)' : 'rgba(244, 63, 94, 0.05)',
                      border: `1px solid ${c.result === 'PASS' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.3)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '12px',
                    }}
                  >
                    <div>
                      <strong style={{ color: c.result === 'PASS' ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                        [{c.result}] {c.rule}:
                      </strong>{' '}
                      <span style={{ color: 'var(--text-secondary)' }}>{c.evidence}</span>
                    </div>
                    {c.is_hard_constraint && (
                      <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--accent-amber)', marginLeft: '10px' }}>
                        HARD
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Execution / Approval Controls */}
            <div style={{
              marginTop: '10px',
              padding: '20px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--bg-tertiary)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 700 }}>Action Execution Stage</div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Approval: <strong style={{ color: '#fff' }}>{activeProposal.approval_state}</strong> | 
                  Execution: <strong style={{ color: '#fff' }}>{activeProposal.execution_state}</strong>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {activeProposal.approval_state === 'PENDING' && (
                  <>
                    <input
                      type="text"
                      value={approverName}
                      onChange={(e) => setApproverName(e.target.value)}
                      placeholder="Approver role/name"
                      style={{
                        padding: '8px 12px',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'var(--bg-primary)',
                        color: '#fff',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '12px',
                      }}
                    />
                    <button
                      onClick={() => onApprove(activeProposal.resolution_id || activeProposal.proposal_id!, approverName)}
                      disabled={!activeProposal.is_feasible}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 16px',
                        borderRadius: 'var(--radius-md)',
                        fontSize: '12px',
                        fontWeight: 700,
                        backgroundColor: activeProposal.is_feasible ? 'var(--accent-cyan)' : 'var(--bg-tertiary)',
                        color: activeProposal.is_feasible ? '#000' : 'var(--text-muted)',
                        cursor: activeProposal.is_feasible ? 'pointer' : 'not-allowed',
                      }}
                    >
                      <CheckCircle2 size={15} />
                      <span>{activeProposal.is_feasible ? 'Approve Proposal' : 'Infeasible (Blocked)'}</span>
                    </button>
                  </>
                )}

                {activeProposal.approval_state === 'APPROVED' && activeProposal.execution_state !== 'EXECUTED' && (
                  <button
                    onClick={() => onExecute(activeProposal.resolution_id || activeProposal.proposal_id!)}
                    disabled={isExecuting}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '10px 20px',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '13px',
                      fontWeight: 700,
                      backgroundColor: 'var(--accent-emerald)',
                      color: '#000',
                      boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
                    }}
                  >
                    <Play size={16} className={isExecuting ? 'animate-spin' : ''} />
                    <span>{isExecuting ? 'Executing & Verifying...' : 'Execute Resolution'}</span>
                  </button>
                )}

                {activeProposal.execution_state === 'EXECUTED' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-emerald)', fontWeight: 700, fontSize: '13px' }}>
                    <CheckCircle2 size={16} />
                    <span>Executed & Verified in State</span>
                  </div>
                )}
              </div>
            </div>

            {/* Execution / Verification banner if exists */}
            {lastExecutionResult && (
              <div style={{
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
              }}>
                <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle2 size={16} />
                  <span>Execution Succeeded & State Verified</span>
                </h4>
                <div style={{ fontSize: '12px', color: '#e2e8f0', marginTop: '6px', lineHeight: 1.4 }}>
                  Applied <strong>{(lastExecutionResult.actions_succeeded || []).length}</strong> atomic state mutations. 
                  Changes: {lastExecutionResult.state_changes?.join('; ')}
                </div>
                {lastVerificationResult && (
                  <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Verification Status: {lastVerificationResult.verification_state} (Resolved: {lastVerificationResult.original_blocker_resolved ? 'YES' : 'NO'}, Remaining: {lastVerificationResult.tasks_still_blocked?.length || 0})
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
            Select a proposal to view actions, tradeoff matrix, and trigger execution.
          </div>
        )}
      </div>
    </div>
  );
};
