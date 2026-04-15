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

# Example of how the bot would flag a document
def analyze_agreement(text):
    missing_elements = []
    for category, details in RENTAL_AGREEMENT_SCHEMA.items():
        if not re.search(details['regex'], text, re.IGNORECASE):
            missing_elements.append(category)
    return missing_elements