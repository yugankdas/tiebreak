# TIEBREAK — Autonomous Deadlock Resolution & Coordination Agent

TIEBREAK is an AI-powered coordination agent designed to autonomously detect, diagnose, propose, and resolve project deadlocks, circular dependencies, resource contention bottlenecks, and missing decisions within engineering and product teams.

---

## Architecture Overview

```
                      ┌──────────────────────────────────────────────┐
                      │            React 19 + TypeScript             │
                      │   - Interactive Dependency Graph (DAG/Cycle) │
                      │   - Deadlock Forensic Inspector              │
                      │   - Multi-Option Resolution Synthesizer      │
                      │   - Cryptographic Audit Trail Timeline       │
                      │   - FailproofAI Policy Dashboard             │
                      └──────────────────────┬───────────────────────┘
                                             │ HTTP / JSON
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │          FastAPI Backend (Python 3.9+)       │
                      │  - Tarjan Cycle & Topological Sort Engine    │
                      │  - Deadlock & Capacity Diagnostic Engine     │
                      │  - Tradeoff & Proposal Synthesizer           │
                      │  - Allowlisted Safe State Mutator            │
                      │  - FailproofAI Governance Hook Adapter       │
                      │  - Independent Outcome Verifier              │
                      └──────────────────────────────────────────────┘
```

---

## Key Features

1. **Deterministic Circular Deadlock Detection**
   - Employs Tarjan's strongly connected components algorithm to find cyclical blocking loops (`task-01 ↔ task-02 ↔ task-04`).
   - Identifies root causes and computes the downstream blast radius.

2. **Multi-Option Resolution Engine**
   - Synthesizes balanced resolution plans (e.g., Provisional Spec Branching, Dependency Reordering, Resource Reallocation).
   - Generates trade-off scores across delivery time, quality risk, and coordination overhead.

3. **Zero-Bypass Governance & Safety (FailproofAI Integration)**
   - Honors immutable constraints: mandatory security reviews (e.g. `task-07`) and protected requirements cannot be bypassed or removed without signed approval.
   - Reversible mutations with full pre/post snapshot diffs.

4. **Cryptographic Audit Trail**
   - Immutable log records every state transition, user approval, and verification result.

---

## Running the Application

### 1. Backend (FastAPI)
The backend is already running on port 8000. To run or restart manually:
```bash
cd backend
PYTHONPATH=. /Users/yugankdas/Library/Python/3.9/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 2. Frontend (React 19 + Vite)
In a separate terminal:
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Verification & Testing
Run backend unit tests:
```bash
cd backend
PYTHONPATH=. pytest tests/
```
