export type BlockerType =
  | 'CIRCULAR_DEPENDENCY'
  | 'MISSING_DECISION'
  | 'RESOURCE_CONFLICT'
  | 'DEADLINE_RISK'
  | 'MANDATORY_REVIEW';

export type TaskStatus = 'NOT_STARTED' | 'READY' | 'IN_PROGRESS' | 'COMPLETED' | 'BLOCKED';

export interface Task {
  task_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: number;
  owner_id: string;
  estimated_effort_hours: number;
  dependencies: string[];
  deadline: string;
  required_skills: string[];
  completion_evidence: string | null;
  is_protected: boolean;
  dependencies_mutable: boolean;
  state_revision: number;
  tags: string[];
  blocker_reason: string | null;
}

export interface TeamMember {
  member_id: string;
  name: string;
  role: string;
  available_capacity?: number;
  capacity_hours_per_week?: number;
  skills: string[];
  is_available?: boolean;
}

export interface Constraint {
  constraint_id: string;
  constraint_type: string;
  description: string;
  applies_to: string[] | null;
  value: any;
  is_active: boolean;
}

export interface Project {
  project_id: string;
  name: string;
  description: string;
  team_members?: TeamMember[];
  team?: TeamMember[];
  tasks: Task[];
  constraints: Constraint[];
  revision: number;
  created_at: string;
  updated_at: string;
}

export interface Blocker {
  blocker_id: string;
  blocker_type: BlockerType;
  title: string;
  explanation: string;
  affected_task_ids: string[];
  root_cause: string;
  evidence: string[];
  downstream_impact: string[];
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  detected_at: string;
  status: 'ACTIVE' | 'RESOLVED' | 'DISMISSED';
  cycle_nodes: string[] | null;
}

export interface ProposedAction {
  action_type: string;
  target_task_id?: string | null;
  target_member_id?: string | null;
  parameters: Record<string, any>;
  description: string;
  reversibility?: 'REVERSIBLE' | 'IRREVERSIBLE' | 'CONDITIONAL';
}

export interface ConstraintCheckResult {
  constraint_id: string;
  constraint_type: string;
  rule: string;
  result: 'PASS' | 'FAIL' | 'NEEDS_INFORMATION';
  evidence: string;
  is_hard_constraint: boolean;
}

export interface ResolutionProposal {
  resolution_id: string;
  proposal_id?: string;
  project_id: string;
  blocker_id: string;
  title: string;
  strategy: string;
  description: string;
  summary?: string;
  proposed_actions: ProposedAction[];
  supporting_evidence: string[];
  assumptions: string[];
  expected_benefits: string[];
  risks: string[];
  trade_offs: string[];
  affected_task_ids: string[];
  estimated_effort_hours: number;
  deadline_impact_days: number;
  resource_impact: string;
  constraint_checks: ConstraintCheckResult[];
  score: number | null;
  score_explanation: string | null;
  approval_state: 'PENDING' | 'APPROVED' | 'REJECTED';
  execution_state: 'NOT_EXECUTED' | 'EXECUTING' | 'EXECUTED' | 'FAILED';
  verification_state: 'NOT_VERIFIED' | 'VERIFIED_RESOLVED' | 'PARTIALLY_RESOLVED' | 'NOT_RESOLVED';
  project_revision: number;
  is_feasible: boolean;
  infeasibility_reason: string | null;
  is_fallback: boolean;
  created_at: string;
  approved_at?: string | null;
  executed_at?: string | null;
  approval_request_id?: string | null;
  designated_approver_ids?: string[];
  routing_reason?: string | null;
}

export interface ExecutionResult {
  success: boolean;
  actions_attempted: any[];
  actions_succeeded: any[];
  actions_failed: any[];
  state_changes: string[];
  error?: string | null;
  executed_at: string;
}

export interface VerificationResult {
  verification_state: string;
  original_blocker_resolved: boolean;
  tasks_now_ready: string[];
  tasks_still_blocked: string[];
  new_blockers: string[];
  evidence: string[];
  verified_at: string;
}

export interface ExecutionResponse {
  execution: ExecutionResult;
  verification: VerificationResult;
  project: Project;
  graph: GraphData;
  blockers: Blocker[];
}

export interface UserProfile {
  user_id: string;
  name: string;
  email: string;
  role: 'ORG_ADMIN' | 'PRODUCT_MANAGER' | 'LEAD_ENGINEER' | 'SECURITY_REVIEWER' | 'TEAM_MEMBER';
  organization_id: string;
  permissions: string[];
}

export interface ApprovalRequest {
  request_id: string;
  org_id: string;
  project_id: string;
  resolution_id: string;
  requester_id: string;
  designated_approver_ids: string[];
  action_type: string;
  proposed_change: string;
  rationale: string;
  affected_task_ids: string[];
  expected_impact: string;
  risks: string[];
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'NEEDS_ROUTING' | 'EXPIRED' | 'CANCELLED';
  decision_maker_id?: string | null;
  decided_at?: string | null;
  explanation?: string | null;
  routing_reason: string;
  project_revision_at_creation: number;
  created_at: string;
}

export interface AuditEvent {
  event_id: string;
  timestamp: string;
  actor: string;
  action: string;
  target: string;
  input_summary: string;
  outcome: string;
  validation_results?: any;
  error_details?: string | null;
  previous_revision?: number | null;
  resulting_revision?: number | null;
}

export interface GraphNode {
  id: string;
  label: string;
  status: TaskStatus;
  priority: number;
  owner: string;
  is_protected: boolean;
  in_cycle?: boolean;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  in_cycle?: boolean;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  cycles: string[][];
}

export interface GroqStatus {
  configured: boolean;
  connected: boolean;
  provider: string;
  model: string;
  actual_model?: string;
  status: string;
  message: string;
  latency_ms: number | null;
}

export interface FailproofStatus {
  status: string;
  version: string;
  enforcement_active: boolean;
  enforcement_note: string;
  tracing_available: boolean;
  cloud_connected: boolean;
  cloud_note: string;
  spool_dir: string;
  capabilities: {
    local_enforcement: boolean;
    event_tracing: boolean;
    policy_evaluation: boolean;
    cloud_sessions: boolean;
    evaluator: boolean;
  };
  limitations: string[];
}

export interface IntegrationsStatus {
  groq: GroqStatus;
  failproof: FailproofStatus;
}
