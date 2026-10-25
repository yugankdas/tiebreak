import { 
  Project, 
  Blocker, 
  ResolutionProposal, 
  ExecutionResult, 
  VerificationResult, 
  ExecutionResponse,
  AuditEvent, 
  GraphData,
  IntegrationsStatus,
  GroqStatus,
  FailproofStatus,
  UserProfile,
  ApprovalRequest
} from '../types';

const API_BASE = '/api';

export const api = {
  // Projects
  async getProjects(): Promise<Project[]> {
    const res = await fetch(`${API_BASE}/projects`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  async getProject(projectId: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects/${projectId}`);
    if (!res.ok) throw new Error(`Failed to fetch project ${projectId}`);
    return res.json();
  },

  async resetProject(projectId: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/reset`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reset project');
    return res.json();
  },

  // Graph
  async getGraph(projectId: string): Promise<GraphData> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/graph`);
    if (!res.ok) throw new Error('Failed to fetch graph data');
    return res.json();
  },

  // Blockers
  async detectBlockers(projectId: string): Promise<Blocker[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/detect-blockers`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to detect blockers');
    return res.json();
  },

  async getBlockers(projectId: string): Promise<Blocker[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/blockers`);
    if (!res.ok) throw new Error('Failed to fetch blockers');
    return res.json();
  },

  // Resolutions
  async generateProposals(projectId: string, blockerId: string): Promise<ResolutionProposal[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/blockers/${blockerId}/resolutions`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to generate resolution proposals');
    return res.json();
  },

  async getProposals(projectId: string): Promise<ResolutionProposal[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/resolutions`);
    if (!res.ok) throw new Error('Failed to fetch proposals');
    return res.json();
  },

  async approveProposal(projectId: string, resolutionId: string, approver: string): Promise<ResolutionProposal> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/resolutions/${resolutionId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approver, actor: approver }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to approve' }));
      throw new Error(err.detail || 'Failed to approve proposal');
    }
    return res.json();
  },

  async rejectProposal(projectId: string, resolutionId: string, reason: string): Promise<ResolutionProposal> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/resolutions/${resolutionId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) throw new Error('Failed to reject proposal');
    return res.json();
  },

  // Organization & Approval Routing
  async listUsers(orgId = 'org-nova'): Promise<UserProfile[]> {
    const res = await fetch(`${API_BASE}/organization/users?org_id=${encodeURIComponent(orgId)}`);
    if (!res.ok) throw new Error('Failed to fetch organization users');
    return res.json();
  },

  async getUserInbox(userId: string, orgId = 'org-nova'): Promise<ApprovalRequest[]> {
    const res = await fetch(`${API_BASE}/organization/inbox?user_id=${encodeURIComponent(userId)}&org_id=${encodeURIComponent(orgId)}`);
    if (!res.ok) throw new Error('Failed to fetch approval inbox');
    return res.json();
  },

  async decideApprovalRequest(requestId: string, userId: string, decision: 'APPROVED' | 'REJECTED', explanation = ''): Promise<ApprovalRequest> {
    const res = await fetch(`${API_BASE}/organization/requests/${requestId}/decide`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, decision, explanation }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Decision failed' }));
      throw new Error(err.detail || 'Decision failed');
    }
    return res.json();
  },

  // Execution & Live Verification
  async executeAndVerify(projectId: string, resolutionId: string): Promise<ExecutionResponse> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/resolutions/${resolutionId}/execute-and-verify`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Execution and verification failed' }));
      throw new Error(err.detail || 'Execution and verification failed');
    }
    return res.json();
  },

  async executeProposal(projectId: string, resolutionId: string): Promise<ExecutionResult> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/resolutions/${resolutionId}/execute`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Execution failed' }));
      throw new Error(err.detail || 'Execution failed');
    }
    return res.json();
  },

  async verifyResolution(projectId: string, resolutionId: string, blockerId?: string): Promise<VerificationResult> {
    const query = blockerId ? `?blocker_id=${encodeURIComponent(blockerId)}` : '';
    const res = await fetch(`${API_BASE}/projects/${projectId}/resolutions/${resolutionId}/verify${query}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Verification failed');
    return res.json();
  },

  // Audit
  async getAuditTrail(projectId: string): Promise<AuditEvent[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/audit`);
    if (!res.ok) throw new Error('Failed to fetch audit trail');
    return res.json();
  },

  // Integrations Diagnostics
  async getIntegrationsStatus(): Promise<IntegrationsStatus> {
    const res = await fetch(`${API_BASE}/integrations/status`);
    if (!res.ok) throw new Error('Failed to fetch integrations status');
    return res.json();
  },

  async testGroqConnection(): Promise<GroqStatus> {
    const res = await fetch(`${API_BASE}/integrations/groq/status`);
    if (!res.ok) throw new Error('Failed to test Groq connection');
    return res.json();
  },

  async getFailproofStatus(): Promise<FailproofStatus> {
    const res = await fetch(`${API_BASE}/integrations/failproof/status`);
    if (!res.ok) throw new Error('Failed to fetch Failproof status');
    return res.json();
  },
};
