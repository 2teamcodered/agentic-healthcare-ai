from .workflow import Evidence, HealthcareOrchestrator, PatientRequest, result_to_dict


def main() -> None:
    knowledge_base = [
        Evidence(
            source_id="demo-guideline-001",
            title="Example patient-safety review checklist",
            excerpt="human review verify history contraindications escalation uncertainty",
            confidence=0.96,
            provenance="synthetic demo source",
        ),
        Evidence(
            source_id="demo-protocol-002",
            title="Example evidence provenance protocol",
            excerpt="source timestamp verification evidence retrieval",
            confidence=0.91,
            provenance="synthetic demo source",
        ),
    ]

    orchestrator = HealthcareOrchestrator(knowledge_base)
    result = orchestrator.run(
        PatientRequest(
            request_id="demo-request-001",
            patient_ref="synthetic-patient-001",
            question="Prepare a review packet for a medication-related question.",
            context={"source": "demo"},
        )
    )
    print(result_to_dict(result))


if __name__ == "__main__":
    main()
