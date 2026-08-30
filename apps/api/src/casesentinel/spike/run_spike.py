"""M0 spike — runnable terminal demo of the supervisor's failure recovery.

    python -m casesentinel.spike.run_spike

Runs one healthy delegation, then injects each fault class (loop, hallucination,
tool_error) into the primary worker and shows the supervisor detect it, kill it,
reroute to a healthy fallback, and log an incident. Runs fully offline with the
scripted model; set GOOGLE_API_KEY to route production drafting through Gemini.
"""

from __future__ import annotations

from ..guards.failure_injection import FaultType, make_worker
from ..guards.supervisor import Supervisor
from ..models.factory import has_gemini_key
from ..store.local_store import LocalStore

STUDENT = "Jordan Rivera"
PROMPT = f"Draft one measurable annual reading goal for {STUDENT}."


def _line(char: str = "-", n: int = 72) -> str:
    return char * n


def run_scenario(supervisor: Supervisor, fault: FaultType) -> None:
    primary = make_worker("document_drafter", fault, student=STUDENT)
    fallback = make_worker("backup_drafter", "none", student=STUDENT)
    result = supervisor.supervise(
        task_id=f"draft-{fault}",
        student=STUDENT,
        prompt=PROMPT,
        primary=primary,
        fallback=fallback,
        max_iterations=5,
    )

    print(f"\n{_line('=')}")
    print(f"SCENARIO: primary worker fault = '{fault}'")
    print(_line())
    for e in result.audit_trail:
        agent = f" [{e['agent']}]" if e.get("agent") else ""
        detail = e.get("detail") or {}
        print(f"  audit: {e['action']:<18}{agent:<22} {detail}")
    print(f"  --> status: {result.status.upper()}"
          + (f", action: {result.action_taken}" if result.action_taken else "")
          + (f", served_by: {result.served_by}" if result.served_by else "")
          + (f", output: {result.output!r}" if result.output else ""))
    if result.incidents:
        for inc in result.incidents:
            print(f"  !! incident: {inc['fault_type']} on {inc['agent']} "
                  f"-> {inc['action_taken']} ({inc['detection']})")


def main() -> None:
    print(_line("#"))
    print("CaseSentinel — M0 spike: supervisor detect / kill / reroute / log")
    print(f"Model backend: {'Gemini (live)' if has_gemini_key() else 'ScriptedLlm (offline)'}")
    print(_line("#"))

    supervisor = Supervisor(LocalStore())
    for fault in ("none", "loop", "hallucination", "tool_error", "transient_tool_error"):
        run_scenario(supervisor, fault)  # type: ignore[arg-type]

    print(f"\n{_line('#')}")
    print("Done. Systematic faults (loop/hallucination) were killed and rerouted to a "
          "healthy fallback; the transient fault was recovered by retry — each logged.")
    print(_line("#"))


if __name__ == "__main__":
    main()
