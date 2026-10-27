import unittest

from agentic_healthcare_ai.workflow import (
    Evidence,
    HealthcareOrchestrator,
    PatientRequest,
    WorkflowStatus,
)


KB = [
    Evidence("s1", "Safety checklist", "human review verify escalation", 0.95, "synthetic"),
]


def request(question: str = "Review a medication question") -> PatientRequest:
    return PatientRequest("r1", "synthetic-patient", question)


class WorkflowTests(unittest.TestCase):
    def test_workflow_stops_at_human_review_by_default(self) -> None:
        result = HealthcareOrchestrator(KB).run(request())
        self.assertIs(result.status, WorkflowStatus.NEEDS_REVIEW)
        self.assertIsNone(result.execution_result)
        self.assertIn("human_approval_required", [event["event"] for event in result.audit_events])

    def test_approved_workflow_only_simulates_execution(self) -> None:
        result = HealthcareOrchestrator(KB, approval_fn=lambda _draft, _review: True).run(request())
        self.assertIs(result.status, WorkflowStatus.COMPLETED)
        self.assertEqual(result.execution_result, "Prepared a reviewer packet; no clinical action was executed.")

    def test_high_risk_term_is_flagged_for_escalation(self) -> None:
        result = HealthcareOrchestrator(KB).run(request("There is chest pain; prepare a review packet"))
        self.assertIsNotNone(result.safety_review)
        self.assertIn("chest pain", result.safety_review.risk_flags)
        self.assertIn(
            "immediate escalation to an appropriate emergency pathway",
            result.safety_review.required_checks,
        )


if __name__ == "__main__":
    unittest.main()
