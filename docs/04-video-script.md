# CaseSentinel — 2-Person Demo Video Script (≤ 4:00)

**Format:** unedited live screen recording with two voices. English. Public on
YouTube/Vimeo. Must show the backend running (ideally the Cloud Run URL).

**Roles**
- **A — Product / Director voice.** Frames the problem, drives the dashboard (clicks).
- **B — Engineering / Architect voice.** Narrates the agents, the recovery, the stack.

> Replace **A** / **B** with your names in the first line only ("I'm ___ and this is ___").

---

## Pre-recording checklist
1. **Deploy first** (for the "backend on Google Cloud" rubric point):
   follow the README → `gcloud run deploy`. Have the **Cloud Run URL** open in a tab
   and the **Firestore console** open in another. (No time to deploy? See *Fallback* below.)
2. Set `GOOGLE_API_KEY` in `apps/api/.env` so drafting runs on **live Gemini 3.5**
   (or keep offline — the scripted fallback reproduces every beat with zero rate-limit risk).
3. Reset demo state so the approval gate starts empty: `rm -rf .data` before launching.
4. Open the dashboard, the architecture diagram (`docs/00-architecture-diagram.md`),
   and a terminal tailing the server logs.
5. Do one dry run of the click path. Keep the whole take under 4:00.

---

## Script

### 0:00–0:18 — Hook  *(A, over the dashboard)*
**A:** "Special-education teachers lose 15 to 20 unpaid hours a week to compliance
paperwork — and one missed IEP deadline is *federal* noncompliance. Districts
usually find out during a state audit. I'm ___ and I'm ___ — this is **CaseSentinel:
district-wide IDEA compliance, watched continuously.**"

### 0:18–0:45 — The gap  *(B)*
**B:** "Two kinds of tools exist today. Systems of record like Frontline *store*
IEPs. AI tools like MagicSchool *draft* text for one teacher. Neither runs the
district's compliance as a live, governed system — and none can *prove* a human
approved the AI's work. Under IDEA, that proof is the whole ballgame."
> [ACTION A: dashboard visible — Willow Creek USD, 40 caseloads, **8 overdue**, 10 due soon.]

### 0:45–1:35 — Live multi-agent sweep  *(A drives, B narrates)*
**A:** "This is a synthetic district — 40 caseloads with real, seeded deadline drift.
Let's run a live compliance sweep."
> [ACTION A: fault selector on **No fault** → click **Run compliance sweep**.]

**B:** "A supervisor delegates to four specialized agents, one at a time. **Timekeeper**
scans every caseload for drift. **Evidence Ingestor** normalizes messy progress
notes. The **Document Drafter** writes a measurable IEP goal on **Gemini 3.5**.
**Compliance Reporter** rolls up district posture. Every step streams live over
Server-Sent Events into an **append-only audit log**."
> [ACTION: trace fills top to bottom; a draft appears **pending** in the Approval gate.]

### 1:35–2:45 — Signature moment: break a worker on camera  *(A drives, B narrates)*
**A:** "Now let's break it — on purpose. I'll make the drafter hallucinate."
> [ACTION A: fault selector → **Hallucination** → click **Run compliance sweep**.]

**B:** "There it is — the drafter wrote a goal for the *wrong student*, Alex Chen
instead of Finn Novak, and it isn't measurable. Watch the supervisor: its judge
**REJECTS** the output, it **KILLS** the drafter, logs an **incident**, and
**REROUTES** to a healthy fallback. The run still resolves — with a *valid* goal —
and the failure is permanently on the record."
> [ACTION: trace shows judge-rejected → kill → reroute → resolved; point at the **Incident log**.]

**A:** "And it's not just hallucinations."
> [ACTION A: run **Tool error (transient)**.]
**B:** "A transient crash — the supervisor **retries the same worker and recovers**
on its own. A runaway loop — it caps the iterations and reroutes. Systematic
failures reroute; transient ones retry; and if the backup also fails, it
**escalates to a human**. Failure-tolerant by design."

### 2:45–3:20 — Governance: human sign-off  *(A approves, B narrates)*
**B:** "Here's the hard constraint: **no agent ever takes a binding action.** Every
draft is a recommendation waiting for a named human."
**A:** "As the SpEd director, I review the goal — and approve it."
> [ACTION A: type approver name if needed → click **Approve**; it moves to *Decided*.]
**B:** "That approval is now written to the audit log — a **due-process trail** that
proves exactly who signed off and how every failure was handled. That's the part no
competitor ships."

### 3:20–3:50 — Architecture + Google Cloud  *(B)*
**B:** "Under the hood: **Google ADK 2.8** orchestrates the agents, **Gemini 3.5**
does the reasoning, and it's deployed on **Cloud Run** with **Firestore** as the
audit store."
> [ACTION B: show the architecture diagram for ~4s, then cut to the **live Cloud Run URL**
> and the terminal logs / Firestore console showing writes landing.]
**B:** "Strict separation of concerns, failure-tolerant routing, reproducible from
the repo — and **synthetic data only**, no real student records."

### 3:50–4:00 — Close  *(both)*
**A:** "CaseSentinel."
**B:** "District-wide IDEA compliance — watched continuously."

---

## Fallback (if you couldn't deploy in time)
Run locally and **say so honestly**: "running locally here; the same container
deploys to Cloud Run with one command — here's the Dockerfile and the deploy step."
Then show the `Dockerfile`, the `STORE_BACKEND=firestore` switch, and the README
deploy section on screen. It's weaker than a live URL for the "production readiness"
rubric, but it's honest and still demonstrates deploy-readiness.

## Timing & delivery notes
- Total spoken content ≈ 450 words — it fits 4:00 *with* the live clicks; don't rush the 1:35–2:45 signature beat, it's 40% of the score.
- Keep it one continuous take (the rubric rewards *unedited* live execution).
- If live Gemini rate-limits mid-take, the offline scripted model produces the same beats — have it as insurance.
- Trim beat 0:18–0:45 (the gap) first if you're over time.
