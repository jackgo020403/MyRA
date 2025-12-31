"""Approval loop for user sign-off."""
from ra_orchestrator.state import RAState, ApprovalDecision


def get_user_approval() -> ApprovalDecision:
    """
    Prompt user for approval decision via CLI.

    Returns:
        ApprovalDecision with user's choice and optional feedback
    """
    print("\n" + "=" * 80)
    print("APPROVAL REQUIRED")
    print("=" * 80)
    print("\nPlease review the research plan above.")
    print("\nOptions:")
    print("  1. Approve  - Proceed with this plan")
    print("  2. Edit     - Provide feedback for revision (NOT IMPLEMENTED IN M1)")
    print("  3. Reject   - Cancel research")
    print("")

    while True:
        choice = input("Enter your decision (1/2/3 or approve/edit/reject): ").strip().lower()

        if choice in ["1", "approve"]:
            return ApprovalDecision(decision="approve")
        elif choice in ["2", "edit"]:
            feedback = input("Enter your feedback for revision: ").strip()
            return ApprovalDecision(decision="edit", feedback=feedback)
        elif choice in ["3", "reject"]:
            return ApprovalDecision(decision="reject")
        else:
            print("Invalid choice. Please enter 1, 2, 3, approve, edit, or reject.")


def run_approval_loop(state: RAState) -> RAState:
    """
    Run approval loop and update state based on user decision.

    Args:
        state: Current RA state with research_plan

    Returns:
        Updated state with approval_decision
    """
    approval = get_user_approval()

    state["approval_decision"] = approval

    if approval.decision == "approve":
        state["current_phase"] = "plan_approved"
    elif approval.decision == "edit":
        # In Milestone 1, edit is not implemented
        print("\n[WARNING] Edit functionality not yet implemented in Milestone 1.")
        print("Treating as rejection. Please restart with a refined question.\n")
        state["current_phase"] = "plan_rejected"
    else:  # reject
        state["current_phase"] = "plan_rejected"

    return state
