# Agentic Healthcare AI

A dependency-light Python starter for an **agentic AI + healthcare AI** orchestration workflow. It demonstrates how specialized agents can coordinate around a healthcare-related request while preserving human oversight, evidence provenance, safety review, and an append-only audit trail.

> **Safety notice:** This is a research and engineering scaffold. It is not a medical device, diagnostic system, treatment recommender, emergency service, or substitute for qualified clinical judgment. The included knowledge sources are synthetic demo data.

## What it demonstrates

1. **Intake agent** validates a request.
2. **Evidence agent** retrieves high-confidence, provenance-tagged evidence from a small local collection.
3. **Planning agent** creates a reviewer-facing draft rather than a clinical decision.
4. **Safety agent** identifies high-risk language and required checks.
5. **Human approval gate** stops the default workflow until a qualified reviewer approves it.
6. **Execution agent** only simulates preparation of a reviewer packet.
7. **Audit log** records workflow transitions and key metadata without logging clinical details.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m agentic_healthcare_ai.example
pytest
```

Or run the module without installation:

```bash
PYTHONPATH=src python -m agentic_healthcare_ai.example
```

## Architecture

```text
Patient request
      |
      v
  IntakeAgent ---> EvidenceAgent ---> PlanningAgent ---> SafetyAgent
                                                               |
                                                               v
                                                   HumanApprovalGate
                                                        /      \\
                                                     stop      approve
                                                       |          |
                                                       v          v
                                                  needs_review  ExecutionAgent
                                                                    |
                                                                    v
                                                               AuditLog
```

## Design principles

- **Human-in-the-loop by default:** the approval function defaults to rejection, so the workflow stops for review.
- **Least authority:** the execution stage cannot prescribe, diagnose, contact a patient, or change a medical record.
- **Evidence traceability:** drafts carry source IDs, confidence, and provenance references.
- **Conservative escalation:** high-risk terms add an emergency-pathway check instead of attempting a response.
- **Observable orchestration:** each stage emits an audit event for debugging and evaluation.
- **Synthetic data only:** replace the demo retrieval layer with a governed, access-controlled source before any legitimate evaluation.

## Suggested next steps

- Add typed schemas and contract tests for every agent boundary.
- Replace keyword retrieval with a permission-aware retrieval service and source freshness checks.
- Add model cards, red-team scenarios, calibration metrics, and clinician review protocols.
- Persist audit events in tamper-evident storage with access controls and retention policies.
- Add authentication, authorization, consent handling, and de-identification before handling any sensitive data.

## License

MIT
