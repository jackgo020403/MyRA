"""
Web-based Research Assistant using Streamlit.
Works on ANY platform - Mac, Windows, Linux, iOS, Android.
"""
import streamlit as st
import os
import json
import base64
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic
import boto3

from ra_orchestrator.state import RAState
from ra_orchestrator.agents.planner import run_planner
from ra_orchestrator.agents.schema_designer import run_schema_designer
from ra_orchestrator.agents.researcher_optimized import run_researcher
from ra_orchestrator.agents.synthesizer import run_synthesizer
from ra_orchestrator.agents.memo_generator import run_memo_generator
from ra_orchestrator.excel.writer import write_full_excel
from ra_orchestrator.excel.writer_m3 import write_milestone3_excel


# Page config
st.set_page_config(
    page_title="MyRA - Research Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check authentication
if not st.session_state.get("authenticated"):
    st.warning("⚠️ Please log in to use the Research Assistant")
    st.info("Click the link below to go to the authentication page")
    if st.button("🔐 Go to Login Page", type="primary"):
        st.switch_page("pages/1_🔐_Auth.py")
    st.stop()

# Get API keys from session (set during login)
anthropic_key = st.session_state.get("anthropic_api_key", "")
serper_key = st.session_state.get("serper_api_key", "")

# If API keys not in session, this means user logged in before this feature was added
if not anthropic_key or not serper_key:
    st.error("⚠️ API keys not configured. Please log out and log in again.")
    if st.button("🚪 Logout and Re-login"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("pages/1_🔐_Auth.py")
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        background-color: #1976D2;
        color: white;
        font-weight: bold;
    }
    .success-box {
        padding: 20px;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        margin: 10px 0;
    }
    .step-box {
        padding: 15px;
        background-color: white;
        border-left: 4px solid #1976D2;
        margin: 10px 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


def _detect_scope(question: str, client: Anthropic) -> str:
    """Auto-detect research scope using Claude."""
    prompt = f"""Analyze this research question and detect the likely research scope.

Research Question: {question}

Provide a clear, structured scope that includes:
1. Key entities/companies/platforms mentioned or implied
2. Industry/category focus
3. Geographic scope (if relevant)
4. Time horizon (if relevant)
5. Key metrics or aspects to prioritize

Be specific but concise. Format as bullet points."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def main():
    # Sidebar
    with st.sidebar:
        # What is MyRA? section
        with st.expander("ℹ️ What is MyRA?", expanded=False):
            st.markdown("""
            **MyRA** is an AI-powered research assistant that helps you conduct comprehensive market research and analysis.

            Simply ask a question, and MyRA will:

            - 🎯 **Plan** a structured research approach with targeted sub-questions
            - 🔍 **Search** 50+ web sources for relevant evidence
            - 📊 **Analyze** and synthesize findings into actionable insights
            - 📝 **Generate** an executive memo with key takeaways
            - 📥 **Deliver** a complete Excel report with raw data and citations

            **Your organization's API keys are automatically configured** - just enter your question and start researching!
            """)

        st.markdown("---")

        st.header("📚 Past Research Logs")

        # Fetch research logs
        user_id = st.session_state.get('user_id', '')
        if user_id:
            try:
                # Use Streamlit secrets for AWS credentials if available (for Cloud deployment)
                if hasattr(st, 'secrets') and 'aws' in st.secrets:
                    lambda_client = boto3.client(
                        'lambda',
                        region_name=st.secrets.aws.get('region_name', 'ap-northeast-2'),
                        aws_access_key_id=st.secrets.aws.get('aws_access_key_id'),
                        aws_secret_access_key=st.secrets.aws.get('aws_secret_access_key')
                    )
                else:
                    # Use default AWS credentials (for local development)
                    lambda_client = boto3.client('lambda', region_name='ap-northeast-2')

                # Call Lambda to get research logs
                response = lambda_client.invoke(
                    FunctionName='myra-auth',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'get_research_logs',
                        'user_id': user_id,
                        'limit': 10
                    })
                )

                result = json.loads(response['Payload'].read())
                if result['statusCode'] == 200:
                    body = json.loads(result['body'])
                    logs = body.get('logs', [])

                    if logs:
                        for log in logs:
                            with st.expander(f"📄 {log['research_title'][:40]}...", expanded=False):
                                st.caption(f"Created: {log['created_at'][:10]}")
                                st.caption(f"Question: {log['research_question'][:80]}...")

                                col1, col2 = st.columns(2)
                                with col1:
                                    # Download button
                                    if st.button("📥 Download", key=f"dl_{log['log_id']}", use_container_width=True):
                                        # Get presigned URL
                                        dl_response = lambda_client.invoke(
                                            FunctionName='myra-auth',
                                            InvocationType='RequestResponse',
                                            Payload=json.dumps({
                                                'action': 'get_research_log_file',
                                                'user_id': user_id,
                                                'log_id': log['log_id']
                                            })
                                        )
                                        dl_result = json.loads(dl_response['Payload'].read())
                                        if dl_result['statusCode'] == 200:
                                            dl_body = json.loads(dl_result['body'])
                                            st.markdown(f"[Download {log['file_name']}]({dl_body['download_url']})")

                                with col2:
                                    # Delete button
                                    if st.button("🗑️ Delete", key=f"del_{log['log_id']}", use_container_width=True):
                                        # Call delete
                                        del_response = lambda_client.invoke(
                                            FunctionName='myra-auth',
                                            InvocationType='RequestResponse',
                                            Payload=json.dumps({
                                                'action': 'delete_research_log',
                                                'user_id': user_id,
                                                'log_id': log['log_id']
                                            })
                                        )
                                        st.success("Deleted! Refresh to update list.")
                                        st.rerun()
                    else:
                        st.info("No research logs yet. Complete a research to see it here!")
                else:
                    st.warning("Could not load research logs")
            except Exception as e:
                st.error(f"Error loading logs: {str(e)}")
        else:
            st.info("No research logs yet")

        st.markdown("---")

        # User info
        st.markdown("### 👤 Account")
        st.markdown(f"**{st.session_state.get('user_name', 'User')}**")
        st.markdown(f"📧 {st.session_state.get('user_email', '')}")
        st.markdown(f"🏢 {st.session_state.get('organization_name', st.session_state.get('user_organization', ''))}")
        st.markdown(f"📊 Daily Limit: {st.session_state.get('daily_limit', 'N/A')} queries")

        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("pages/1_🔐_Auth.py")

    # Header with welcome message
    st.title("🔍 MyRA Research Assistant")
    st.markdown(f"*Welcome, {st.session_state.get('user_name', 'User')}!*")
    st.markdown("---")

    # Initialize session state
    if 'stage' not in st.session_state:
        st.session_state.stage = 'input'
    if 'state' not in st.session_state:
        st.session_state.state = None
    if 'scope' not in st.session_state:
        st.session_state.scope = None
    if 'plan' not in st.session_state:
        st.session_state.plan = None

    # Stage 1: Research Question Input
    if st.session_state.stage == 'input':
        st.header("1️⃣ Enter Your Research Question")
        question = st.text_area(
            "What would you like to research?",
            height=100,
            placeholder="Example: What is the market size of electric vehicles in the US in 2024-2025?"
        )

        if st.button("🚀 Start Research", type="primary"):
            if not question.strip():
                st.error("Please enter a research question.")
            else:
                with st.spinner("🤔 Analyzing your question and detecting scope..."):
                    client = Anthropic(api_key=anthropic_key)
                    scope = _detect_scope(question, client)

                    st.session_state.question = question
                    st.session_state.scope = scope
                    st.session_state.client = client
                    st.session_state.stage = 'scope_review'
                    st.rerun()

    # Stage 2: Scope Review
    elif st.session_state.stage == 'scope_review':
        st.header("2️⃣ Review Research Scope")

        st.markdown("**Your Question:**")
        st.info(st.session_state.question)

        st.markdown("**Detected Research Scope:**")
        # Use a container with proper styling instead of raw HTML
        with st.container():
            st.markdown(st.session_state.scope)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✓ Approve Scope", type="primary", use_container_width=True):
                st.session_state.stage = 'planning'
                st.rerun()

        with col2:
            if st.button("↻ Revise Scope", use_container_width=True):
                st.session_state.stage = 'scope_feedback'
                st.rerun()

    # Stage 2b: Scope Feedback
    elif st.session_state.stage == 'scope_feedback':
        st.header("2️⃣ Refine Research Scope")

        st.markdown("**Your Question:**")
        st.info(st.session_state.question)

        st.markdown("**Current Scope:**")
        with st.container():
            st.markdown(st.session_state.scope)

        st.markdown("---")

        feedback = st.text_area(
            "What would you like to change?",
            height=100,
            placeholder="Example: Focus only on Tesla and Rivian, exclude commercial vehicles"
        )

        if st.button("🔄 Refine Scope", type="primary"):
            if feedback.strip():
                with st.spinner("Refining scope based on your feedback..."):
                    refined_question = f"{st.session_state.question}\n\nUser feedback: {feedback}"
                    new_scope = _detect_scope(refined_question, st.session_state.client)
                    st.session_state.scope = new_scope
                    st.session_state.stage = 'scope_review'
                    st.rerun()

    # Stage 3: Planning
    elif st.session_state.stage == 'planning':
        st.header("3️⃣ Creating Research Plan")

        with st.spinner("📋 Creating research plan with sub-questions..."):
            state: RAState = {
                "research_question": st.session_state.question,
                "research_context": f"{st.session_state.question}\n\nResearch Scope:\n{st.session_state.scope}",
                "research_plan": None,
                "approval_decision": None,
                "ledger_schema": None,
                "ledger_rows": [],
                "memo_block": None,
                "excel_path": None,
                "current_phase": "init",
                "iteration_count": 0,
                "scope_clarified": True,
            }

            state = run_planner(state, st.session_state.client)
            st.session_state.state = state
            st.session_state.plan = state['research_plan']
            st.session_state.stage = 'plan_review'
            st.rerun()

    # Stage 4: Plan Review
    elif st.session_state.stage == 'plan_review':
        st.header("4️⃣ Review Research Plan")

        plan = st.session_state.plan

        st.markdown(f"**Research Title:** {plan.research_title}")
        st.markdown(f"**Number of Sub-Questions:** {len(plan.sub_questions)}")

        st.markdown("---")

        for i, sq in enumerate(plan.sub_questions, 1):
            with st.expander(f"Question {i}: {sq.question}", expanded=True):
                st.markdown(f"**Rationale:** {sq.rationale}")
                st.markdown(f"**Expected Output:** {sq.expected_output}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✓ Approve Plan & Start Research", type="primary", use_container_width=True):
                st.session_state.stage = 'research'
                st.rerun()

        with col2:
            if st.button("↻ Revise Plan", use_container_width=True):
                st.session_state.stage = 'plan_feedback'
                st.rerun()

    # Stage 4b: Plan Feedback
    elif st.session_state.stage == 'plan_feedback':
        st.header("4️⃣ Revise Research Plan")

        # Show current plan
        plan = st.session_state.plan

        st.markdown(f"**Current Research Title:** {plan.research_title}")
        st.markdown(f"**Number of Sub-Questions:** {len(plan.sub_questions)}")

        st.markdown("---")

        for i, sq in enumerate(plan.sub_questions, 1):
            with st.expander(f"Question {i}: {sq.question}", expanded=False):
                st.markdown(f"**Rationale:** {sq.rationale}")
                st.markdown(f"**Expected Output:** {sq.expected_output}")

        st.markdown("---")

        feedback = st.text_area(
            "What would you like to change about the plan?",
            height=150,
            placeholder="Example: Add a question about pricing trends, remove the regulatory question"
        )

        if st.button("🔄 Revise Plan", type="primary"):
            if feedback.strip():
                with st.spinner("Revising research plan..."):
                    st.session_state.state["research_context"] += f"\n\nUser feedback on plan: {feedback}"
                    state = run_planner(st.session_state.state, st.session_state.client)
                    st.session_state.state = state
                    st.session_state.plan = state['research_plan']
                    st.session_state.stage = 'plan_review'
                    st.rerun()

    # Stage 5: Research Execution
    elif st.session_state.stage == 'research':
        st.header("5️⃣ Conducting Research")

        progress_bar = st.progress(0)
        status_text = st.empty()

        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True, parents=True)

        state = st.session_state.state
        state["approval_decision"] = "approved"
        state["current_phase"] = "plan_approved"

        try:
            # Schema Design
            status_text.text("📊 Designing data schema...")
            progress_bar.progress(20)
            state = run_schema_designer(state)

            # Research
            status_text.text("🔍 Searching 50 web sources and extracting evidence...")
            progress_bar.progress(40)
            state = run_researcher(state, serper_key, st.session_state.client)

            status_text.text(f"✓ Collected {len(state['ledger_rows'])} evidence rows")

            # Save evidence Excel
            evidence_excel_path = write_full_excel(state, output_dir)

            # Synthesis
            status_text.text("🧠 Synthesizing findings...")
            progress_bar.progress(60)
            state = run_synthesizer(state, st.session_state.client)

            # Memo
            status_text.text("📝 Generating executive memo...")
            progress_bar.progress(80)
            state = run_memo_generator(state, st.session_state.client)

            # Final Excel
            status_text.text("📊 Creating final Excel report...")
            progress_bar.progress(90)
            final_excel_path = write_milestone3_excel(state, evidence_excel_path, output_dir)

            progress_bar.progress(100)
            status_text.text("✅ Research Complete!")

            # Success message
            st.success("🎉 Research completed successfully!")

            st.markdown(f"""
            <div class='success-box'>
                <h3>📊 Your Research Report is Ready!</h3>
                <p><strong>File:</strong> {final_excel_path}</p>
                <p><strong>Location:</strong> {output_dir.absolute()}</p>

                <h4>Report Contains:</h4>
                <ul>
                    <li><strong>MEMO Tab:</strong> Executive summary</li>
                    <li><strong>SYNTHESIS Tab:</strong> Detailed findings for each question</li>
                    <li><strong>RAW DATA Tab:</strong> All evidence with source links</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            # Download button
            with open(final_excel_path, 'rb') as f:
                file_bytes = f.read()
                st.download_button(
                    label="📥 Download Excel Report",
                    data=file_bytes,
                    file_name=Path(final_excel_path).name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )

                # Save to research logs
                try:
                    # Use Streamlit secrets for AWS credentials if available
                    if hasattr(st, 'secrets') and 'aws' in st.secrets:
                        lambda_client = boto3.client(
                            'lambda',
                            region_name=st.secrets.aws.get('region_name', 'ap-northeast-2'),
                            aws_access_key_id=st.secrets.aws.get('aws_access_key_id'),
                            aws_secret_access_key=st.secrets.aws.get('aws_secret_access_key')
                        )
                    else:
                        # Use default AWS credentials
                        lambda_client = boto3.client('lambda', region_name='ap-northeast-2')

                    # Encode file as base64
                    file_base64 = base64.b64encode(file_bytes).decode('utf-8')

                    # Save to research logs
                    save_response = lambda_client.invoke(
                        FunctionName='myra-auth',
                        InvocationType='RequestResponse',
                        Payload=json.dumps({
                            'action': 'save_research_log',
                            'user_id': st.session_state.get('user_id', ''),
                            'research_title': state['research_plan'].research_title,
                            'research_question': st.session_state.question,
                            'file_data': file_base64,
                            'file_name': Path(final_excel_path).name
                        })
                    )

                    save_result = json.loads(save_response['Payload'].read())
                    if save_result['statusCode'] == 200:
                        st.success("✅ Research saved to your history!")
                    else:
                        st.warning("Could not save to research history")
                except Exception as e:
                    st.warning(f"Could not save to research history: {str(e)}")

            if st.button("🔄 Start New Research"):
                # Reset research-specific state, keep auth and welcome flag
                keys_to_keep = ['authenticated', 'user_id', 'user_email', 'user_name', 'user_organization',
                                'organization_name', 'daily_limit', 'anthropic_api_key', 'serper_api_key', 'show_welcome']
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                # Explicitly reset to input stage
                st.session_state.stage = 'input'
                st.rerun()

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

            if st.button("🔄 Try Again"):
                st.session_state.stage = 'input'
                st.rerun()


if __name__ == "__main__":
    main()
