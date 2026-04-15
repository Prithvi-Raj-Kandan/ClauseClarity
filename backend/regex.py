import re

# Dictionary mapping legal categories to Regex patterns for extraction
RENTAL_AGREEMENT_SCHEMA = {
    "PARTIES": {
        "importance": 1,
        "regex": r"(First Party|Second Party|Lessor|Lessee|Licensor|Licensee|Landlord|Tenant)",
        "critical_check": "Ensure both parties have Aadhaar/PAN details mentioned."
    },
    "CONSIDERATION": {
        "importance": 2,
        "regex": r"(Monthly Rent|Security Deposit|Rent Amount|Refundable|Consideration|INR|Rs\.)",
        "critical_check": "Check if rent escalation (e.g., 5-10% increase) is mentioned."
    },
    "TENURE": {
        "importance": 3,
        "regex": r"(Term|Tenure|Period|Commencement|Expiry|11 months|Lock-in period)",
        "critical_check": "Ensure the start date and end date are explicitly clear."
    },
    "PREMISES": {
        "importance": 4,
        "regex": r"(Premises|Schedule of Property|Flat No|Survey No|Bounded by|Address)",
        "critical_check": "Verify if the full postal address including PIN code is present."
    },
    "USAGE_RESTRICTIONS": {
        "importance": 5,
        "regex": r"(Residential|Sub-letting|Commercial|Alterations|Structure|Purpose)",
        "critical_check": "Flag if 'Sub-letting' is not explicitly prohibited."
    },
    "TERMINATION": {
        "importance": 6,
        "regex": r"(Notice Period|Termination|Eviction|Vacate|Handover|Breach)",
        "critical_check": "Ensure a 'one month notice' or 'two month notice' is defined."
    },
    "MAINTENANCE": {
        "importance": 7,
        "regex": r"(Electricity|Water Charges|Society Maintenance|Repairs|Fittings)",
        "critical_check": "Differentiate between 'Minor' (Tenant) and 'Major' (Landlord) repairs."
    },
    "LEGAL_BOILERPLATE": {
        "importance": 8,
        "regex": r"(Jurisdiction|Arbitration|Force Majeure|Indemnity|Stamp Duty)",
        "critical_check": "Check for the specific city/state of Jurisdiction."
    }
}

HIGH_RISK_PATTERNS = {
    "immediate_eviction": {
        "regex": r"(immediate eviction|terminate\s+this\s+lease\s+immediately\s+without\s+any\s+notice)",
        "reason": "Immediate eviction or termination without notice.",
    },
    "waiver_of_legal_rights": {
        "regex": r"(not\s+to\s+approach\s+any\s+(court|police|legal\s+authority)|surrenders\s+all\s+legal\s+rights|has\s+no\s+right\s+to\s+contest)",
        "reason": "Tenant legal remedies are waived or blocked.",
    },
    "unrestricted_landlord_entry": {
        "regex": r"(enter\s+the\s+premises\s+at\s+any\s+time\s+of\s+day\s+or\s+night\s+without\s+any\s+notice)",
        "reason": "Landlord entry rights are unrestricted and no-notice.",
    },
    "unbounded_penalties": {
        "regex": r"(penalty\s+of\s+INR\s+[\d,]+\s+per\s+day\s+with\s+no\s+limit)",
        "reason": "Penalty terms are unbounded or excessive.",
    },
    "deposit_non_refundable": {
        "regex": r"(no\s+refund\s+is\s+guaranteed|deduct\s+any\s+amount\s+at\s+his\s+sole\s+discretion)",
        "reason": "Security deposit refund terms are unfair or discretionary.",
    },
}

# Example of how the bot would flag a document
def analyze_agreement(text):
    missing_elements = []
    for category, details in RENTAL_AGREEMENT_SCHEMA.items():
        if not re.search(details['regex'], text, re.IGNORECASE):
            missing_elements.append(category)
    return missing_elements


def analyze_agreement_detailed(text):
    """Return per-category matches, missing clauses, and critical guidance."""
    results = {}
    missing_elements = []
    for category, details in RENTAL_AGREEMENT_SCHEMA.items():
        found = bool(re.search(details["regex"], text, re.IGNORECASE))
        results[category] = {
            "found": found,
            "importance": details["importance"],
            "critical_check": details["critical_check"],
        }
        if not found:
            missing_elements.append(category)

    critical_missing = [
        category
        for category in missing_elements
        if RENTAL_AGREEMENT_SCHEMA[category]["importance"] <= 3
    ]

    high_risk_flags = []
    for flag_name, flag in HIGH_RISK_PATTERNS.items():
        if re.search(flag["regex"], text, re.IGNORECASE):
            high_risk_flags.append(
                {
                    "flag": flag_name,
                    "reason": flag["reason"],
                }
            )

    return {
        "missing_categories": missing_elements,
        "critical_missing": critical_missing,
        "categories": results,
        "high_risk_flags": high_risk_flags,
    }