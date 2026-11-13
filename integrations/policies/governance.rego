package uag

import rego.v1

# Application-owned policy, deliberately small. No tenant-supplied Rego or
# network built-ins. Missing/invalid inputs yield review, never silent allow.
default decision := {"action": "review", "reason": "classification_required"}

decision := {"action": "block", "reason": "unacceptable_risk"} if {
    input.risk_level == "unacceptable"
}

decision := {"action": "block", "reason": "pii_not_authorized"} if {
    input.risk_level != "unacceptable"
    input.contains_pii == true
    not input.pii_authorized == true
}

decision := {"action": "review", "reason": "high_risk_requires_approval"} if {
    input.risk_level == "high"
    not pii_denied
    not input.approved == true
}

decision := {"action": "allow", "reason": "policy_conditions_met"} if {
    input.risk_level in {"minimal", "limited", "high"}
    input.contains_pii in {true, false}
    not pii_denied
    input.risk_level != "high"
}

decision := {"action": "allow", "reason": "approved_high_risk"} if {
    input.risk_level == "high"
    input.approved == true
    input.contains_pii in {true, false}
    not pii_denied
}

pii_denied if {
    input.contains_pii == true
    not input.pii_authorized == true
}
