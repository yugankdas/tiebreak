import React, { useState } from 'react';
import { GraphData, Task } from '../../types';
import { 
  AlertTriangle, 
  Shield, 
  Clock, 
  User, 
  CheckCircle2, 
  CircleDashed,
  RefreshCw,
  Info
} from 'lucide-react';

interface DependencyGraphViewProps {
  graph: GraphData | null;
  tasks: Task[];
  onRefresh: () => void;
  isLoading: boolean;
  recentlyResolvedNodes?: Set<string>;
}

export const DependencyGraphView: React.FC<DependencyGraphViewProps> = ({
  graph,
  tasks,
  onRefresh,
  isLoading,
  recentlyResolvedNodes = new Set(),
}) => {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  if (!graph) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading graph...</div>;
  }

  const selectedTask = tasks.find((t) => t.task_id === selectedTaskId);
  const cycleTaskIds = new Set<string>();
  graph.cycles.forEach((cycle) => cycle.forEach((id) => cycleTaskIds.add(id)));

  // Simple layered layout computation for rendering SVG DAG
  // Assign columns based on longest path or heuristic
  const nodeMap = new Map(graph.nodes.map((n) => [n.id, n]));
  const inDegree = new Map<string, number>();
  const adj = new Map<string, string[]>();

  graph.nodes.forEach((n) => {
    inDegree.set(n.id, 0);
    adj.set(n.id, []);
  });

  graph.edges.forEach((e) => {
    inDegree.set(e.target, (inDegree.get(e.target) || 0) + 1);
    const list = adj.get(e.source) || [];
    list.push(e.target);
    adj.set(e.source, list);
  });

  // Calculate layout coordinates
  // Nodes in cycles get placed together with distinct styling
  const nodePositions: Record<string, { x: number; y: number }> = {};
  const width = 880;
  const height = 480;

  // Circular / Deadlock layout for cyclic nodes, and layered for others
  const cyclicList = Array.from(cycleTaskIds);
  const nonCyclicList = graph.nodes.filter((n) => !cycleTaskIds.has(n.id)).map((n) => n.id);

  // Position cyclic nodes in a ring on the left
  const cycleCenterX = 220;
  const cycleCenterY = 240;
  const cycleRadius = 110;
  cyclicList.forEach((id, idx) => {
    const angle = (idx / (cyclicList.length || 1)) * 2 * Math.PI - Math.PI / 2;
    nodePositions[id] = {
      x: cycleCenterX + cycleRadius * Math.cos(angle),
      y: cycleCenterY + cycleRadius * Math.sin(angle),
    };
  });

  // Position non-cyclic nodes in right grid
  const cols = 3;
  const startX = 460;
  const startY = 80;
  const colSpacing = 140;
  const rowSpacing = 85;

  nonCyclicList.forEach((id, idx) => {
    const col = idx % cols;
    const row = Math.floor(idx / cols);
    nodePositions[id] = {
      x: startX + col * colSpacing,
      y: startY + row * rowSpacing,
    };
  });

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '24px', height: 'calc(100vh - 120px)' }}>
      {/* Graph Area */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        position: 'relative',
      }}>
        {/* Header toolbar */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
        }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 700 }}>Interactive Dependency Graph</h2>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Showing {graph.nodes.length} tasks and {graph.edges.length} dependency edges.
              {graph.cycles.length > 0 ? (
                <span style={{ color: 'var(--accent-rose)', fontWeight: 600, marginLeft: '6px' }}>
                  ⚠️ {graph.cycles.length} Circular Deadlock Cycle Detected!
                </span>
              ) : (
                <span style={{ color: 'var(--accent-emerald)', fontWeight: 600, marginLeft: '6px' }}>
                  ✓ Graph is acyclic (DAG clean)
                </span>
              )}
            </p>
          </div>

          <button
            onClick={onRefresh}
            disabled={isLoading}
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
            <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Legend */}
        <div style={{
          padding: '8px 20px',
          fontSize: '11px',
          display: 'flex',
          gap: '16px',
          borderBottom: '1px solid var(--border-subtle)',
          backgroundColor: 'rgba(255, 255, 255, 0.01)',
          color: 'var(--text-secondary)',
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent-rose)' }} />
            Deadlock Cycle
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent-amber)' }} />
            Blocked Task
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent-cyan)' }} />
            In Progress
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent-emerald)' }} />
            Ready / Completed
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Shield size={12} color="var(--accent-primary)" />
            Protected Constraint
          </span>
        </div>

        {/* SVG Container */}
        <div style={{ flex: 1, position: 'relative', overflow: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width={width} height={height} style={{ filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.3))' }}>
            <defs>
              <marker
                id="arrowhead-normal"
                markerWidth="8"
                markerHeight="6"
                refX="22"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#475569" />
              </marker>
              <marker
                id="arrowhead-cycle"
                markerWidth="10"
                markerHeight="8"
                refX="24"
                refY="4"
                orient="auto"
              >
                <polygon points="0 0, 10 4, 0 8" fill="#f43f5e" />
              </marker>
            </defs>

            {/* Background cycle highlight area if cycles exist */}
            {cyclicList.length > 0 && (
              <circle
                cx={cycleCenterX}
                cy={cycleCenterY}
                r={cycleRadius + 45}
                fill="rgba(244, 63, 94, 0.05)"
                stroke="rgba(244, 63, 94, 0.25)"
                strokeDasharray="4 4"
              />
            )}

            {/* Edges */}
            {graph.edges.map((edge) => {
              const src = nodePositions[edge.source];
              const tgt = nodePositions[edge.target];
              if (!src || !tgt) return null;

              const isCycleEdge = edge.in_cycle || (cycleTaskIds.has(edge.source) && cycleTaskIds.has(edge.target));

              // Quadratic curve if in cycle to make loop obvious
              let pathData = `M ${src.x} ${src.y} L ${tgt.x} ${tgt.y}`;
              if (isCycleEdge) {
                const midX = (src.x + tgt.x) / 2;
                const midY = (src.y + tgt.y) / 2;
                // bend slightly away from center
                const dx = midX - cycleCenterX;
                const dy = midY - cycleCenterY;
                const ctrlX = midX + dx * 0.3;
                const ctrlY = midY + dy * 0.3;
                pathData = `M ${src.x} ${src.y} Q ${ctrlX} ${ctrlY} ${tgt.x} ${tgt.y}`;
              }

              return (
                <path
                  key={edge.id}
                  d={pathData}
                  fill="none"
                  stroke={isCycleEdge ? 'var(--accent-rose)' : '#334155'}
                  strokeWidth={isCycleEdge ? 2.5 : 1.5}
                  strokeDasharray={isCycleEdge ? '5 3' : 'none'}
                  markerEnd={isCycleEdge ? 'url(#arrowhead-cycle)' : 'url(#arrowhead-normal)'}
                  style={{
                    filter: isCycleEdge ? 'drop-shadow(0 0 4px rgba(244, 63, 94, 0.6))' : 'none',
                    transition: 'all 0.3s ease',
                  }}
                />
              );
            })}

            {/* Nodes */}
            {graph.nodes.map((node) => {
              const pos = nodePositions[node.id];
              if (!pos) return null;

              const inCycle = cycleTaskIds.has(node.id);
              const isSelected = selectedTaskId === node.id;
              const justResolved = recentlyResolvedNodes.has(node.id);

              let fillColor = 'var(--bg-tertiary)';
              let strokeColor = 'var(--border-subtle)';

              if (justResolved) {
                strokeColor = 'var(--accent-emerald)';
                fillColor = '#0d2a1a';
              } else if (inCycle) {
                strokeColor = 'var(--accent-rose)';
                fillColor = '#2a121d';
              } else if (node.status === 'BLOCKED') {
                strokeColor = 'var(--accent-amber)';
              } else if (node.status === 'IN_PROGRESS') {
                strokeColor = 'var(--accent-cyan)';
              } else if (node.status === 'COMPLETED' || node.status === 'READY') {
                strokeColor = 'var(--accent-emerald)';
              }

              if (isSelected) {
                strokeColor = '#fff';
              }

              return (
                <g
                  key={node.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSelectedTaskId(node.id)}
                >
                  {/* Outer glow ring for cycles */}
                  {inCycle && !justResolved && (
                    <circle
                      r={24}
                      fill="none"
                      stroke="var(--accent-rose)"
                      strokeWidth={1.5}
                      strokeDasharray="3 3"
                      opacity={0.7}
                    />
                  )}
                  {/* Outer glow ring for just-resolved nodes */}
                  {justResolved && (
                    <circle
                      r={26}
                      fill="none"
                      stroke="var(--accent-emerald)"
                      strokeWidth={2}
                      strokeDasharray="none"
                      opacity={0.8}
                    />
                  )}

                  {/* Node Circle */}
                  <circle
                    r={18}
                    fill={fillColor}
                    stroke={strokeColor}
                    strokeWidth={isSelected ? 3 : inCycle ? 2.5 : 1.5}
                  />

                  {/* ID / Icon Inside */}
                  <text
                    textAnchor="middle"
                    dy="4"
                    fill="#fff"
                    fontSize="10px"
                    fontWeight="700"
                    fontFamily="monospace"
                  >
                    {node.id.replace('task-', 'T')}
                  </text>

                  {/* Task Label Underneath */}
                  <text
                    textAnchor="middle"
                    dy="32"
                    fill={
                      isSelected ? '#fff' :
                      justResolved ? '#6ee7b7' :
                      inCycle ? '#fda4af' : 'var(--text-secondary)'
                    }
                    fontSize="10px"
                    fontWeight={isSelected || inCycle || justResolved ? '600' : '400'}
                  >
                    {node.label.length > 16 ? node.label.slice(0, 15) + '…' : node.label}
                  </text>

                  {/* Protected icon badge */}
                  {node.is_protected && (
                    <circle cx={12} cy={-12} r={6} fill="var(--accent-primary)" />
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      </div>

      {/* Side Inspector Panel */}
      <div style={{
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
      }}>
        <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Info size={16} color="var(--accent-primary)" />
          <span>Task Inspector</span>
        </h3>

        {selectedTask ? (
          <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontFamily: 'monospace', fontSize: '12px', color: 'var(--accent-primary)', fontWeight: 600 }}>
                  {selectedTask.task_id}
                </span>
                <span style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: 
                    cycleTaskIds.has(selectedTask.task_id) ? 'rgba(244, 63, 94, 0.2)' :
                    selectedTask.status === 'BLOCKED' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                  color:
                    cycleTaskIds.has(selectedTask.task_id) ? 'var(--accent-rose)' :
                    selectedTask.status === 'BLOCKED' ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                }}>
                  {cycleTaskIds.has(selectedTask.task_id) ? 'DEADLOCKED' : selectedTask.status}
                </span>
              </div>
              <h4 style={{ fontSize: '15px', fontWeight: 700 }}>{selectedTask.title}</h4>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: 1.4 }}>
                {selectedTask.description}
              </p>
            </div>

            {selectedTask.blocker_reason && (
              <div style={{
                padding: '10px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'rgba(244, 63, 94, 0.1)',
                border: '1px solid rgba(244, 63, 94, 0.3)',
                fontSize: '11px',
                color: '#fecdd3',
              }}>
                <strong style={{ color: 'var(--accent-rose)', display: 'block', marginBottom: '2px' }}>
                  Blocker Reason:
                </strong>
                {selectedTask.blocker_reason}
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <User size={14} color="var(--accent-primary)" />
                <span>Owner: <strong>{selectedTask.owner_id}</strong></span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Clock size={14} color="var(--accent-cyan)" />
                <span>Effort: <strong>{selectedTask.estimated_effort_hours}h</strong></span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={14} color="var(--accent-amber)" />
                <span>Deadline: <strong>{selectedTask.deadline.split('T')[0]}</strong></span>
              </div>
              {selectedTask.is_protected && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-primary)' }}>
                  <Shield size={14} />
                  <strong>Protected Governance Task</strong>
                </div>
              )}
            </div>

            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Prerequisite Dependencies ({selectedTask.dependencies.length})
              </div>
              {selectedTask.dependencies.length === 0 ? (
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>None (Root node)</span>
              ) : (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {selectedTask.dependencies.map((dep) => (
                    <span
                      key={dep}
                      onClick={() => setSelectedTaskId(dep)}
                      style={{
                        padding: '4px 8px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '11px',
                        fontFamily: 'monospace',
                        cursor: 'pointer',
                        backgroundColor: cycleTaskIds.has(dep) ? 'rgba(244, 63, 94, 0.2)' : 'var(--bg-tertiary)',
                        color: cycleTaskIds.has(dep) ? 'var(--accent-rose)' : 'var(--text-primary)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      {dep}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 10px', color: 'var(--text-muted)', fontSize: '13px' }}>
            Click on any graph node to inspect its details, status, and dependencies.
          </div>
        )}
      </div>
    </div>
  );
};
