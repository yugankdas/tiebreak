import React, { useState, useEffect, useCallback } from 'react';
import { api } from './services/api';
import { 
  Project, 
  Blocker, 
  ResolutionProposal, 
  ExecutionResult, 
  VerificationResult, 
  AuditEvent, 
  GraphData,
  IntegrationsStatus,
  GroqStatus,
  UserProfile,
  ApprovalRequest,
} from './types';
import { Navbar } from './components/Navbar';
import { DependencyGraphView } from './features/dependency-graph/DependencyGraphView';
import { BlockersView } from './features/blockers/BlockersView';
import { ResolutionsView } from './features/resolutions/ResolutionsView';
import { AuditTrailView } from './features/audit/AuditTrailView';
import { GovernanceView } from './features/integrations/GovernanceView';
import { ApprovalsInboxView } from './features/approvals/ApprovalsInboxView';
import './styles/index.css';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('graph');
  const [project, setProject] = useState<Project | null>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [blockers, setBlockers] = useState<Blocker[]>([]);
  const [selectedBlocker, setSelectedBlocker] = useState<Blocker | null>(null);
  const [proposals, setProposals] = useState<ResolutionProposal[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [integrationsStatus, setIntegrationsStatus] = useState<IntegrationsStatus | null>(null);
  const [groqStatus, setGroqStatus] = useState<GroqStatus | null>(null);

  // Organization & Approvals state
  const [availableUsers, setAvailableUsers] = useState<UserProfile[]>([]);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [approvalRequests, setApprovalRequests] = useState<ApprovalRequest[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isResetting, setIsResetting] = useState<boolean>(false);
  const [isDetecting, setIsDetecting] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [isTestingGroq, setIsTestingGroq] = useState<boolean>(false);
  const [isLoadingInbox, setIsLoadingInbox] = useState<boolean>(false);

  // Highlighted nodes after a live execution (for visual diffing)
  const [recentlyResolvedNodes, setRecentlyResolvedNodes] = useState<Set<string>>(new Set());

  const [lastExecutionResult, setLastExecutionResult] = useState<ExecutionResult | null>(null);
  const [lastVerificationResult, setLastVerificationResult] = useState<VerificationResult | null>(null);

  // Load organization users once
  const loadUsers = useCallback(async () => {
    try {
      const allUsers = await api.listUsers('');
      setAvailableUsers(allUsers);
      if (!currentUser && allUsers.length > 0) {
        // Default to Alice Chen (PM) so approvals can be viewed
        const alice = allUsers.find((u) => u.user_id === 'mem-01') || allUsers[0];
        setCurrentUser(alice);
      }
    } catch (err) {
      console.error('Failed to load users:', err);
    }
  }, [currentUser]);

  const loadInbox = useCallback(async (user?: UserProfile) => {
    const u = user || currentUser;
    if (!u) return;
    try {
      setIsLoadingInbox(true);
      const inbox = await api.getUserInbox(u.user_id, 'org-nova');
      setApprovalRequests(inbox);
    } catch (err) {
      console.error('Failed to load inbox:', err);
    } finally {
      setIsLoadingInbox(false);
    }
  }, [currentUser]);

  // Initial load
  const loadProjectData = useCallback(async () => {
    try {
      setIsLoading(true);
      const projects = await api.getProjects();
      if (projects.length > 0) {
        const p = projects[0];
        setProject(p);
        
        const [g, blks, props, audit, integ] = await Promise.all([
          api.getGraph(p.project_id),
          api.detectBlockers(p.project_id),
          api.getProposals(p.project_id),
          api.getAuditTrail(p.project_id),
          api.getIntegrationsStatus(),
        ]);

        setGraph(g);
        setBlockers(blks);
        if (blks.length > 0) setSelectedBlocker(blks[0]);
        setProposals(props);
        setAuditEvents(audit);
        setIntegrationsStatus(integ);
        setGroqStatus(integ.groq);
      }
    } catch (err) {
      console.error('Failed to load project data:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProjectData();
    loadUsers();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Reload inbox whenever user switches or approvals tab opens
  useEffect(() => {
    if (currentUser) {
      loadInbox(currentUser);
    }
  }, [currentUser]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSwitchUser = (user: UserProfile) => {
    setCurrentUser(user);
    loadInbox(user);
  };

  // Run real Groq diagnostic
  const handleTestGroq = async () => {
    try {
      setIsTestingGroq(true);
      const status = await api.testGroqConnection();
      setGroqStatus(status);
      if (integrationsStatus) {
        setIntegrationsStatus({ ...integrationsStatus, groq: status });
      }
    } catch (err) {
      console.error('Failed to test Groq:', err);
    } finally {
      setIsTestingGroq(false);
    }
  };

  // Actions
  const handleReset = async () => {
    if (!project) return;
    try {
      setIsResetting(true);
      await api.resetProject(project.project_id);
      setLastExecutionResult(null);
      setLastVerificationResult(null);
      setRecentlyResolvedNodes(new Set());
      await loadProjectData();
    } catch (err) {
      console.error('Reset failed:', err);
    } finally {
      setIsResetting(false);
    }
  };

  const handleDetectBlockers = async () => {
    if (!project) return;
    try {
      setIsDetecting(true);
      const [blks, g, audit] = await Promise.all([
        api.detectBlockers(project.project_id),
        api.getGraph(project.project_id),
        api.getAuditTrail(project.project_id),
      ]);
      setBlockers(blks);
      setGraph(g);
      setAuditEvents(audit);
    } catch (err) {
      console.error('Detection failed:', err);
    } finally {
      setIsDetecting(false);
    }
  };

  const handleGenerateProposals = async (blockerId: string) => {
    if (!project) return;
    try {
      setIsGenerating(true);
      const props = await api.generateProposals(project.project_id, blockerId);
      setProposals(props);
      const audit = await api.getAuditTrail(project.project_id);
      setAuditEvents(audit);
      // Refresh inbox after generation (routes may have been created)
      if (currentUser) await loadInbox(currentUser);
    } catch (err) {
      console.error('Failed to generate proposals:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApproveProposal = async (resolutionId: string, approver: string) => {
    if (!project) return;
    try {
      const updated = await api.approveProposal(project.project_id, resolutionId, approver);
      setProposals((prev) => prev.map((p) => 
        (p.resolution_id === resolutionId || p.proposal_id === resolutionId) ? updated : p
      ));
      const audit = await api.getAuditTrail(project.project_id);
      setAuditEvents(audit);
      if (currentUser) await loadInbox(currentUser);
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    }
  };

  const handleRejectProposal = async (resolutionId: string, reason: string) => {
    if (!project) return;
    try {
      const updated = await api.rejectProposal(project.project_id, resolutionId, reason);
      setProposals((prev) => prev.map((p) => 
        (p.resolution_id === resolutionId || p.proposal_id === resolutionId) ? updated : p
      ));
      const audit = await api.getAuditTrail(project.project_id);
      setAuditEvents(audit);
    } catch (err: any) {
      alert(`Rejection error: ${err.message}`);
    }
  };

  // Live-updating execution handler — uses executeAndVerify atomic endpoint
  const handleExecuteProposal = async (resolutionId: string) => {
    if (!project) return;
    try {
      setIsExecuting(true);

      const response = await api.executeAndVerify(project.project_id, resolutionId);

      // Capture resolved nodes for visual diffing in the graph
      const nowReady = new Set<string>(response.verification.tasks_now_ready || []);
      setRecentlyResolvedNodes(nowReady);

      // Atomically update all state from the single authoritative response
      setLastExecutionResult(response.execution);
      setLastVerificationResult(response.verification);
      setProject(response.project);
      setGraph(response.graph);
      setBlockers(response.blockers);

      // Refresh proposals and audit from server
      const [updatedProposals, audit] = await Promise.all([
        api.getProposals(project.project_id),
        api.getAuditTrail(project.project_id),
      ]);
      setProposals(updatedProposals);
      setAuditEvents(audit);

      // Refresh inbox
      if (currentUser) await loadInbox(currentUser);

      // Clear visual highlight after 5 seconds
      setTimeout(() => setRecentlyResolvedNodes(new Set()), 5000);
    } catch (err: any) {
      alert(`Execution failed: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleSelectBlockerForResolution = (blocker: Blocker) => {
    setSelectedBlocker(blocker);
    setActiveTab('resolutions');
    handleGenerateProposals(blocker.blocker_id);
  };

  // Organization approval inbox decision handler
  const handleApprovalDecision = async (
    requestId: string,
    decision: 'APPROVED' | 'REJECTED',
    explanation: string,
  ) => {
    if (!currentUser) throw new Error('No user selected');
    const updated = await api.decideApprovalRequest(requestId, currentUser.user_id, decision, explanation);
    setApprovalRequests((prev) => prev.map((r) => r.request_id === requestId ? updated : r));
    // Sync proposal state if the resolution was approved
    if (decision === 'APPROVED' && project) {
      const updatedProposals = await api.getProposals(project.project_id);
      setProposals(updatedProposals);
    }
  };

  const pendingApprovalsCount = approvalRequests.filter(
    (r) => r.status === 'PENDING' && currentUser && r.designated_approver_ids.includes(currentUser.user_id)
  ).length;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        projectName={project?.name || 'Loading Project...'}
        onReset={handleReset}
        isResetting={isResetting}
        blockerCount={blockers.length}
        pendingApprovalsCount={pendingApprovalsCount}
        groqStatus={groqStatus}
        onTestGroq={handleTestGroq}
        isTestingGroq={isTestingGroq}
        currentUser={currentUser}
        availableUsers={availableUsers}
        onSwitchUser={handleSwitchUser}
      />

      <main style={{ flex: 1, padding: '24px', maxWidth: '1440px', width: '100%', margin: '0 auto' }}>
        {activeTab === 'graph' && (
          <DependencyGraphView
            graph={graph}
            tasks={project?.tasks || []}
            onRefresh={loadProjectData}
            isLoading={isLoading}
            recentlyResolvedNodes={recentlyResolvedNodes}
          />
        )}

        {activeTab === 'blockers' && (
          <BlockersView
            blockers={blockers}
            onDetect={handleDetectBlockers}
            isDetecting={isDetecting}
            onSelectBlockerForResolution={handleSelectBlockerForResolution}
          />
        )}

        {activeTab === 'resolutions' && (
          <ResolutionsView
            proposals={proposals}
            blockers={blockers}
            selectedBlocker={selectedBlocker}
            onSelectBlocker={setSelectedBlocker}
            onGenerateProposals={handleGenerateProposals}
            isGenerating={isGenerating}
            onApprove={handleApproveProposal}
            onReject={handleRejectProposal}
            onExecute={handleExecuteProposal}
            isExecuting={isExecuting}
            lastExecutionResult={lastExecutionResult}
            lastVerificationResult={lastVerificationResult}
            groqStatus={groqStatus}
          />
        )}

        {activeTab === 'approvals' && (
          <ApprovalsInboxView
            currentUser={currentUser || availableUsers[0]}
            availableUsers={availableUsers}
            onSwitchUser={handleSwitchUser}
            requests={approvalRequests}
            onDecide={handleApprovalDecision}
            isLoading={isLoadingInbox}
            onRefresh={() => currentUser && loadInbox(currentUser)}
            onNavigateToExecution={(resolutionId) => {
              setActiveTab('resolutions');
            }}
          />
        )}

        {activeTab === 'audit' && (
          <AuditTrailView events={auditEvents} />
        )}

        {activeTab === 'governance' && (
          <GovernanceView 
            status={integrationsStatus} 
            onTestGroq={handleTestGroq} 
            isTestingGroq={isTestingGroq} 
          />
        )}
      </main>
    </div>
  );
};
