import React, { useState } from 'react';
import { ApprovalRequest, UserProfile } from '../../types';
import { 
  Inbox, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  ShieldCheck, 
  ShieldAlert, 
  Send,
  Building,
  UserCheck,
  Ban
} from 'lucide-react';

interface ApprovalsInboxViewProps {
  currentUser: UserProfile;
  availableUsers: UserProfile[];
  onSwitchUser: (user: UserProfile) => void;
  requests: ApprovalRequest[];
  onDecide: (requestId: string, decision: 'APPROVED' | 'REJECTED', explanation: string) => Promise<void>;
  isLoading: boolean;
  onRefresh: () => void;
  onNavigateToExecution?: (resolutionId: string) => void;
}

export const ApprovalsInboxView: React.FC<ApprovalsInboxViewProps> = ({
  currentUser,
  availableUsers,
  onSwitchUser,
  requests,
  onDecide,
  isLoading,
  onRefresh,
  onNavigateToExecution,
}) => {
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(
    requests.length > 0 ? requests[0].request_id : null
  );
  const [explanation, setExplanation] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const activeRequest = requests.find((r) => r.request_id === selectedRequestId) || requests[0];

  const handleDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    if (!activeRequest) return;
    try {
      setIsSubmitting(true);
      setActionError(null);
      setActionSuccess(null);
      await onDecide(activeRequest.request_id, decision, explanation);
      setActionSuccess(`Request successfully ${decision.toLowerCase()}!`);
      setExplanation('');
    } catch (err: any) {
      setActionError(err.message || `Failed to submit ${decision.toLowerCase()} decision`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isDesignatedApprover = activeRequest && (
    activeRequest.designated_approver_ids.includes(currentUser.user_id) || 
    currentUser.role === 'ORG_ADMIN'
  );

  const isCrossOrg = activeRequest && activeRequest.org_id !== currentUser.organization_id;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '24px', height: 'calc(100vh - 120px)' }}>
      {/* Sidebar: Role Switcher & Request List */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {/* User Identity Switcher */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          backgroundColor: 'rgba(0, 0, 0, 0.15)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Current Identity
            </span>
            <span style={{
              fontSize: '10px',
              fontWeight: 700,
              padding: '2px 6px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: currentUser.organization_id === 'org-nova' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(244, 63, 94, 0.2)',
              color: currentUser.organization_id === 'org-nova' ? 'var(--accent-primary)' : 'var(--accent-rose)',
            }}>
              {currentUser.organization_id}
            </span>
          </div>

          <select
            value={currentUser.user_id}
            onChange={(e) => {
              const u = availableUsers.find((usr) => usr.user_id === e.target.value);
              if (u) onSwitchUser(u);
            }}
            style={{
              width: '100%',
              padding: '8px 10px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--bg-tertiary)',
              color: '#fff',
              border: '1px solid var(--border-subtle)',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            {availableUsers.map((u) => (
              <option key={u.user_id} value={u.user_id}>
                {u.name} — {u.role.replace(/_/g, ' ')} ({u.organization_id})
              </option>
            ))}
          </select>

          <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
            Permissions: {currentUser.permissions.length > 0 ? currentUser.permissions.join(', ') : 'None'}
          </div>
        </div>

        {/* Requests List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', padding: '0 4px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Pending Approvals ({requests.length})
            </span>
            <button
              onClick={onRefresh}
              disabled={isLoading}
              style={{
                fontSize: '11px',
                color: 'var(--accent-primary)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Refresh
            </button>
          </div>

          {requests.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 10px', color: 'var(--text-muted)', fontSize: '12px' }}>
              <Inbox size={28} style={{ margin: '0 auto 8px', opacity: 0.4 }} />
              No approval requests in this inbox.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {requests.map((req) => {
                const isSelected = (activeRequest?.request_id === req.request_id);
                const isDesignated = req.designated_approver_ids.includes(currentUser.user_id);
                return (
                  <div
                    key={req.request_id}
                    onClick={() => {
                      setSelectedRequestId(req.request_id);
                      setActionError(null);
                      setActionSuccess(null);
                    }}
                    style={{
                      padding: '12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isSelected ? 'var(--bg-tertiary)' : 'rgba(255, 255, 255, 0.02)',
                      border: isSelected ? '1px solid var(--border-active)' : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{
                        fontSize: '9px',
                        fontWeight: 700,
                        padding: '1px 5px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 
                          req.status === 'APPROVED' ? 'rgba(16, 185, 129, 0.2)' :
                          req.status === 'REJECTED' ? 'rgba(244, 63, 94, 0.2)' :
                          req.status === 'NEEDS_ROUTING' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(99, 102, 241, 0.2)',
                        color:
                          req.status === 'APPROVED' ? 'var(--accent-emerald)' :
                          req.status === 'REJECTED' ? 'var(--accent-rose)' :
                          req.status === 'NEEDS_ROUTING' ? 'var(--accent-amber)' : 'var(--accent-primary)',
                      }}>
                        {req.status}
                      </span>

                      {isDesignated && (
                        <span style={{
                          fontSize: '9px',
                          fontWeight: 700,
                          padding: '1px 5px',
                          borderRadius: 'var(--radius-sm)',
                          backgroundColor: 'rgba(6, 182, 212, 0.2)',
                          color: 'var(--accent-cyan)',
                        }}>
                          YOUR APPROVAL NEEDED
                        </span>
                      )}
                    </div>

                    <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>{req.proposed_change}</h4>
                    <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: 1.3 }}>
                      {req.rationale.length > 80 ? req.rationale.slice(0, 79) + '…' : req.rationale}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Main Panel: Request Details & Decision Area */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {activeRequest ? (
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Header */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                  Request ID: {activeRequest.request_id}
                </span>
                <span style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 
                    activeRequest.status === 'APPROVED' ? 'rgba(16, 185, 129, 0.2)' :
                    activeRequest.status === 'REJECTED' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(99, 102, 241, 0.2)',
                  color:
                    activeRequest.status === 'APPROVED' ? 'var(--accent-emerald)' :
                    activeRequest.status === 'REJECTED' ? 'var(--accent-rose)' : 'var(--accent-primary)',
                }}>
                  Status: {activeRequest.status}
                </span>
              </div>
              <h1 style={{ fontSize: '20px', fontWeight: 800, marginTop: '6px' }}>{activeRequest.proposed_change}</h1>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                {activeRequest.rationale}
              </p>
            </div>

            {/* Routing Policy & Reason */}
            <div style={{
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(99, 102, 241, 0.08)',
              border: '1px solid rgba(99, 102, 241, 0.2)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-primary)', fontWeight: 700, fontSize: '13px' }}>
                <Building size={16} />
                <span>Organization Approval Routing Policy</span>
              </div>
              <p style={{ fontSize: '12px', color: '#e2e8f0', marginTop: '6px' }}>
                {activeRequest.routing_reason}
              </p>
              <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', gap: '16px' }}>
                <span>Organization: <strong>{activeRequest.org_id}</strong></span>
                <span>Designated Approvers: <strong>{activeRequest.designated_approver_ids.join(', ') || 'None (Needs Admin Routing)'}</strong></span>
                <span>Project Revision at Creation: <strong>r{activeRequest.project_revision_at_creation}</strong></span>
              </div>
            </div>

            {/* Action Details & Affected Scope */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
              <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Action Type
                </div>
                <div style={{ fontSize: '13px', fontWeight: 600, marginTop: '4px', color: 'var(--accent-cyan)' }}>
                  {activeRequest.action_type}
                </div>
              </div>

              <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Affected Task IDs
                </div>
                <div style={{ fontSize: '13px', fontWeight: 600, marginTop: '4px', color: 'var(--accent-primary)', fontFamily: 'monospace' }}>
                  {activeRequest.affected_task_ids.join(', ') || 'None'}
                </div>
              </div>

              <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Expected Impact
                </div>
                <div style={{ fontSize: '12px', marginTop: '4px', color: '#fff' }}>
                  {activeRequest.expected_impact}
                </div>
              </div>
            </div>

            {/* Risks */}
            {activeRequest.risks && activeRequest.risks.length > 0 && (
              <div>
                <h3 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Evaluated Risks & Consequences
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {activeRequest.risks.map((risk, idx) => (
                    <div key={idx} style={{
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'rgba(245, 158, 11, 0.05)',
                      border: '1px solid rgba(245, 158, 11, 0.2)',
                      fontSize: '12px',
                      color: 'var(--accent-amber)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}>
                      <AlertTriangle size={14} />
                      <span>{risk}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Authorization Feedback Banner */}
            {actionError && (
              <div style={{
                padding: '12px 16px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'rgba(244, 63, 94, 0.1)',
                border: '1px solid rgba(244, 63, 94, 0.3)',
                color: 'var(--accent-rose)',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}>
                <ShieldAlert size={16} />
                <span>{actionError}</span>
              </div>
            )}

            {actionSuccess && (
              <div style={{
                padding: '12px 16px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: 'var(--accent-emerald)',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}>
                <CheckCircle2 size={16} />
                <span>{actionSuccess}</span>
              </div>
            )}

            {/* Decision Controls */}
            {activeRequest.status === 'PENDING' && (
              <div style={{
                marginTop: 'auto',
                padding: '20px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700 }}>
                    Decision Panel for <span style={{ color: 'var(--accent-primary)' }}>{currentUser.name}</span>
                  </div>
                  {isCrossOrg ? (
                    <span style={{ fontSize: '11px', color: 'var(--accent-rose)', fontWeight: 700 }}>
                      ⚠️ Cross-Organization Access (Forbidden)
                    </span>
                  ) : isDesignatedApprover ? (
                    <span style={{ fontSize: '11px', color: 'var(--accent-emerald)', fontWeight: 700 }}>
                      ✓ Authorized to decide
                    </span>
                  ) : (
                    <span style={{ fontSize: '11px', color: 'var(--accent-amber)', fontWeight: 700 }}>
                      ⚠️ Unauthorized (Request assigned to: {activeRequest.designated_approver_ids.join(', ')})
                    </span>
                  )}
                </div>

                <div style={{ marginBottom: '14px' }}>
                  <textarea
                    rows={2}
                    value={explanation}
                    onChange={(e) => setExplanation(e.target.value)}
                    placeholder="Provide audit rationale or rejection justification..."
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--bg-primary)',
                      color: '#fff',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '12px',
                      resize: 'none',
                    }}
                  />
                </div>

                <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                  <button
                    onClick={() => handleDecision('REJECTED')}
                    disabled={isSubmitting}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '9px 18px',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '12px',
                      fontWeight: 700,
                      backgroundColor: 'rgba(244, 63, 94, 0.15)',
                      color: 'var(--accent-rose)',
                      border: '1px solid rgba(244, 63, 94, 0.3)',
                      cursor: 'pointer',
                    }}
                  >
                    <XCircle size={15} />
                    <span>Reject</span>
                  </button>

                  <button
                    onClick={() => handleDecision('APPROVED')}
                    disabled={isSubmitting}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '9px 20px',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '12px',
                      fontWeight: 700,
                      backgroundColor: 'var(--accent-emerald)',
                      color: '#000',
                      border: 'none',
                      cursor: 'pointer',
                      boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)',
                    }}
                  >
                    <CheckCircle2 size={15} />
                    <span>Approve Request</span>
                  </button>
                </div>
              </div>
            )}

            {/* Resolved Decision Record */}
            {activeRequest.status !== 'PENDING' && (
              <div style={{
                marginTop: 'auto',
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: activeRequest.status === 'APPROVED' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
                border: `1px solid ${activeRequest.status === 'APPROVED' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
              }}>
                <div style={{ fontSize: '13px', fontWeight: 700, color: activeRequest.status === 'APPROVED' ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                  Decision Recorded: {activeRequest.status}
                </div>
                <div style={{ fontSize: '12px', color: '#e2e8f0', marginTop: '4px' }}>
                  Decided by user: <strong>{activeRequest.decision_maker_id}</strong> on {activeRequest.decided_at ? new Date(activeRequest.decided_at).toLocaleString() : 'N/A'}.
                </div>
                {activeRequest.explanation && (
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px', fontStyle: 'italic' }}>
                    "{activeRequest.explanation}"
                  </div>
                )}
                {activeRequest.status === 'APPROVED' && onNavigateToExecution && (
                  <button
                    onClick={() => onNavigateToExecution(activeRequest.resolution_id)}
                    style={{
                      marginTop: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 14px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--accent-primary)',
                      color: '#fff',
                      fontSize: '12px',
                      fontWeight: 600,
                      border: 'none',
                      cursor: 'pointer',
                    }}
                  >
                    <span>Proceed to Execution in Resolutions View</span>
                  </button>
                )}
              </div>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
            Select an approval request to review details and submit authorized decisions.
          </div>
        )}
      </div>
    </div>
  );
};
