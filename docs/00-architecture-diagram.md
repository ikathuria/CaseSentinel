# 00 — Architecture Diagram

Rendered image (for slides / Devpost): [`casesentinel-architecture.png`](casesentinel-architecture.png)
(source: [`casesentinel-architecture.svg`](casesentinel-architecture.svg)).

![CaseSentinel architecture](casesentinel-architecture.png)

---

Mermaid version:

```mermaid
flowchart TB
    Director([SpEd Director / Compliance Coordinator])
    subgraph Web["Dashboard — Vite + React + Tailwind"]
        UI[Posture · Caseload · Live trace · Approval gate · Incidents · Break-an-agent]
    end
    Director <--> UI

    subgraph API["FastAPI on Cloud Run"]
        REST["/api/district · /api/run · /api/approvals · /api/incidents · /api/runs/:id/trace"]
        SSE["/api/run/stream (Server-Sent Events)"]
    end
    UI -->|fetch| REST
    UI -->|EventSource| SSE

    subgraph Supervisor["Supervisor / Orchestrator (guarded, sequential)"]
        direction TB
        TK[Timekeeper] --> EI[Evidence Ingestor] --> DD[Document Drafter] --> CR[Compliance Reporter]
        GUARD{{"Guard: loop cap + content judge"}}
        DD -.watched by.-> GUARD
        GUARD -->|fault| RECOVER["retry / reroute / escalate"]
    end
    REST --> Supervisor
    SSE --> Supervisor

    GATE[[Approval Gate — named human sign-off]]
    DD --> GATE
    Director -->|approve / reject| GATE

    subgraph Gemini["Gemini 3.5 via google-genai (ADK 2.8)"]
        FLASH[gemini-3.5-flash]
        LITE[gemini-3.5-flash-lite]
    end
    EI --> LITE
    DD --> FLASH

    subgraph Store["Store interface"]
        LOCAL[(LocalStore — JSONL)]
        FS[(Firestore)]
    end
    AUDIT[[Append-only audit log + incidents]]
    Supervisor --> AUDIT
    GATE --> AUDIT
    AUDIT --> Store

    classDef gcp fill:#e8f0fe,stroke:#4285f4,color:#1a237e;
    class API,Gemini,FS gcp;
```

**Data flow:** the director triggers a sweep → the supervisor runs the four agents
sequentially (RPM-safe) → the Document Drafter runs under a guard (loop cap +
content judge) → on failure the supervisor retries/reroutes/escalates and logs an
incident → the draft becomes a pending approval → a named human approves → every
step is written to the append-only audit log (LocalStore offline, Firestore on
Cloud Run). The dashboard streams the whole thing live over SSE.
