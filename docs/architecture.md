# Architecture Notes

The starter intentionally keeps each agent as a small Python class with a single `run` method. This makes the workflow easy to test, replace, and instrument.

## Control flow

`HealthcareOrchestrator.run` owns sequencing and the fail-closed boundary. A malformed request produces a failed result; lack of approval produces `needs_review`; only explicit approval reaches the execution simulation.

## Production hardening checklist

- Use a policy engine for authorization and purpose limitation.
- Keep patient identity separate from model context and audit payloads.
- Require citations, source timestamps, and freshness thresholds.
- Add idempotency keys and replay protection around every side effect.
- Route urgent signals to an independently validated emergency pathway.
- Evaluate false negatives, false positives, subgroup performance, and abstention behavior.
- Ensure a qualified clinician owns final decisions and the system's operating procedure.
