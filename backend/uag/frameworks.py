"""Original support checklists; neither standard text nor legal determinations."""
FRAMEWORKS = {
    "eu_ai_act": {
        "name": "EU AI Act", "source_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
        "description": "Human-reviewed assessment support. Determine applicability using current authoritative law; no legal compliance guarantee.",
        "controls": [
            ("EU-SCOPE", "Document scope, role and intended purpose", "Record provider/deployer role and the evidence used to assess applicability."),
            ("EU-RISK", "Review prohibited and high-risk use cases", "Record a qualified review of Articles 5 and 6 and relevant annexes; this is not automated legal classification."),
            ("EU-DATA", "Review data governance and quality", "Identify dataset provenance, limitations and controls for the assessed use."),
            ("EU-DOC", "Maintain technical documentation", "Attach technical evidence and operational recordkeeping information."),
            ("EU-HUMAN", "Define human oversight and transparency", "Document user information, oversight, escalation and monitoring."),
            ("EU-SECURITY", "Evaluate robustness and cybersecurity", "Record evaluation results, incident processes and corrective actions.")],
    },
    "iso42001": {
        "name": "ISO/IEC 42001 AIMS", "source_url": "https://www.iso.org/standard/81230.html",
        "description": "Original management-system checklist. Obtain the licensed ISO standard for normative requirements; this checklist is not certification.",
        "controls": [
            ("AIMS-CONTEXT", "Maintain organisation context and scope", "Identify interested parties, boundaries and AI management responsibilities."),
            ("AIMS-POLICY", "Approve AI policy and accountability", "Record management approval, accountability and objectives."),
            ("AIMS-RISK", "Maintain AI risk and impact assessments", "Link risks, impacts, owners and treatment decisions."),
            ("AIMS-SOA", "Maintain applicability decisions", "Document inclusion/exclusion rationale and supporting evidence for selected controls."),
            ("AIMS-LEGAL", "Maintain a legal and regulatory register", "Record applicable obligations, review dates and responsible owners in evidence and control notes."),
            ("AIMS-IMPROVE", "Track internal review and corrective action", "Record review findings, corrective actions and effectiveness checks.")],
    },
    "nist_ai_rmf": {
        "name": "NIST AI RMF", "source_url": "https://airc.nist.gov/airmf-resources/airmf/",
        "description": "Workflow support for Govern, Map, Measure and Manage. Original prompts reference the voluntary NIST AI RMF.",
        "controls": [
            ("GOVERN", "Govern — establish accountability", "Record governance policies, roles, responsibilities and review arrangements."),
            ("MAP", "Map — describe context and impacts", "Document intended use, stakeholders, constraints and potential impacts."),
            ("MEASURE", "Measure — evaluate identified risks", "Attach test results and document uncertainty, limitations and metrics."),
            ("MANAGE", "Manage — prioritise and respond", "Link risk treatments, monitoring, incident response and corrective actions.")],
    },
}


def new_controls(framework):
    return [{"id": identifier, "title": title, "description": description, "status": "not_started", "notes": "", "evidence_ids": [], "owner": "", "due_date": None} for identifier, title, description in FRAMEWORKS[framework]["controls"]]
