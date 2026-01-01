"""
Organization configuration for multi-tenant Research Assistant.
Each organization has its own API keys and email domain validation.
"""

ORGANIZATIONS = {
    "SNU_student": {
        "name": "Seoul National University",
        "email_domains": ["snu.ac.kr"],
        "anthropic_api_key": "ANTHROPIC_KEY_SNU",  # Environment variable name
        "serper_api_key": "SERPER_KEY_SNU",        # Environment variable name
        "daily_limit": 20,  # Free tier searches per day
        "description": "SNU Students"
    },
    "McKinsey": {
        "name": "McKinsey & Company",
        "email_domains": ["mckinsey.com"],
        "anthropic_api_key": "ANTHROPIC_KEY_MCKINSEY",
        "serper_api_key": "SERPER_KEY_MCKINSEY",
        "daily_limit": 50,  # Higher limit for consulting firms
        "description": "McKinsey Employees"
    },
    "BCG": {
        "name": "Boston Consulting Group",
        "email_domains": ["bcg.com"],
        "anthropic_api_key": "ANTHROPIC_KEY_BCG",
        "serper_api_key": "SERPER_KEY_BCG",
        "daily_limit": 50,
        "description": "BCG Employees"
    },
    "Bain": {
        "name": "Bain & Company",
        "email_domains": ["bain.com", "baincompany.com"],
        "anthropic_api_key": "ANTHROPIC_KEY_BAIN",
        "serper_api_key": "SERPER_KEY_BAIN",
        "daily_limit": 50,
        "description": "Bain Employees"
    }
}


def validate_email_domain(email: str, organization: str) -> bool:
    """
    Validate that email domain matches organization's allowed domains.

    Args:
        email: User's email address
        organization: Organization code (e.g., "SNU_student", "McKinsey")

    Returns:
        True if email domain is valid for the organization
    """
    if organization not in ORGANIZATIONS:
        return False

    email_lower = email.lower()
    allowed_domains = ORGANIZATIONS[organization]["email_domains"]

    for domain in allowed_domains:
        if email_lower.endswith(f"@{domain}"):
            return True

    return False


def get_organization_by_email(email: str) -> str | None:
    """
    Auto-detect organization from email domain.

    Args:
        email: User's email address

    Returns:
        Organization code if domain matches, None otherwise
    """
    email_lower = email.lower()

    for org_code, org_config in ORGANIZATIONS.items():
        for domain in org_config["email_domains"]:
            if email_lower.endswith(f"@{domain}"):
                return org_code

    return None


def get_api_keys(organization: str) -> dict:
    """
    Get API keys for an organization (from environment variables).

    Args:
        organization: Organization code

    Returns:
        Dictionary with anthropic_key and serper_key
    """
    import os

    if organization not in ORGANIZATIONS:
        raise ValueError(f"Unknown organization: {organization}")

    org_config = ORGANIZATIONS[organization]

    return {
        "anthropic_key": os.environ.get(org_config["anthropic_api_key"], ""),
        "serper_key": os.environ.get(org_config["serper_api_key"], "")
    }


def get_daily_limit(organization: str) -> int:
    """Get daily search limit for organization."""
    if organization not in ORGANIZATIONS:
        return 10  # Default

    return ORGANIZATIONS[organization]["daily_limit"]
