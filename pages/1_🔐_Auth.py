"""
Authentication page for MyRA Research Assistant.
Handles signup, login, and email verification.
"""
import streamlit as st
import boto3
import json

# AWS Lambda configuration
AWS_REGION = "ap-northeast-2"
LAMBDA_FUNCTION_NAME = "myra-auth"


def get_org_api_keys(org_code: str) -> dict:
    """Fetch API keys for a given organization from DynamoDB."""
    try:
        dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)

        response = dynamodb.get_item(
            TableName='myra-organizations-prod',
            Key={'org_code': {'S': org_code}}
        )

        if 'Item' not in response:
            return {"error": f"Organization {org_code} not found"}

        item = response['Item']

        return {
            "anthropic_api_key": item['anthropic_api_key']['S'],
            "serper_api_key": item['serper_api_key']['S'],
            "organization_name": item['name']['S'],
            "daily_limit": int(item['daily_limit']['N'])
        }

    except Exception as e:
        return {"error": str(e)}


def call_lambda(action: str, data: dict) -> dict:
    """Call Lambda function using AWS SDK."""
    payload = {
        "action": action,
        **data
    }

    try:
        # Create Lambda client
        lambda_client = boto3.client('lambda', region_name=AWS_REGION)

        # Invoke Lambda
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Parse response
        result = json.loads(response['Payload'].read())

        # Lambda returns {statusCode, body}
        if 'body' in result and isinstance(result['body'], str):
            return json.loads(result['body'])
        elif 'body' in result:
            return result['body']
        return result
    except Exception as e:
        return {"error": str(e)}


def show_signup():
    """Show signup form."""
    st.subheader("📝 Create Account")

    # Get available organizations
    orgs_response = call_lambda("get_organizations", {})
    if "organizations" in orgs_response:
        organizations = orgs_response["organizations"]
    else:
        st.error("Failed to load organizations")
        return

    with st.form("signup_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")

        # Organization selector
        org_options = {
            f"{config['name']} ({', '.join(config['email_domains'])})": code
            for code, config in organizations.items()
        }
        selected_org = st.selectbox(
            "Organization",
            options=list(org_options.keys()),
            help="Select your organization. Your email must match the organization's domain."
        )
        organization = org_options[selected_org]

        password = st.text_input("Password", type="password")
        password_confirm = st.text_input("Confirm Password", type="password")

        submit = st.form_submit_button("Sign Up")

        if submit:
            # Validation
            if not name or not email or not password:
                st.error("Please fill in all fields")
                return

            if password != password_confirm:
                st.error("Passwords do not match")
                return

            if len(password) < 8:
                st.error("Password must be at least 8 characters")
                return

            # Call signup Lambda
            with st.spinner("Creating account..."):
                result = call_lambda("signup", {
                    "email": email,
                    "password": password,
                    "organization": organization,
                    "name": name
                })

            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.success(f"✅ {result['message']}")

                # Store email in session for verification
                st.session_state.pending_verification_email = email
                st.rerun()


def show_verification():
    """Show email verification form."""
    st.subheader("📧 Verify Your Email")

    email = st.session_state.get("pending_verification_email", "")

    if not email:
        st.warning("Please sign up first to get a verification code.")
        if st.button("← Back to Login"):
            if "pending_verification_email" in st.session_state:
                del st.session_state.pending_verification_email
            st.rerun()
        return

    st.success(f"✅ Account created successfully!")
    st.info(f"📧 A 6-digit verification code has been sent to: **{email}**")
    st.info("💡 Please check your email inbox (and spam folder) for the verification code.")

    with st.form("verification_form"):
        code = st.text_input("Verification Code (6 digits)", max_chars=6)
        submit = st.form_submit_button("Verify")

        if submit:
            if not code or len(code) != 6:
                st.error("Please enter the 6-digit code")
                return

            with st.spinner("Verifying..."):
                result = call_lambda("verify_email", {
                    "email": email,
                    "code": code
                })

            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.success("✅ Email verified successfully!")

                # Store auth info in session
                st.session_state.authenticated = True
                st.session_state.user_id = result["user_id"]
                st.session_state.user_email = result["email"]
                st.session_state.user_organization = result["organization"]
                st.session_state.user_token = result["token"]
                st.session_state.daily_limit = result["daily_limit"]
                st.session_state.user_name = result.get("name", "User")

                # Fetch and store organization API keys
                api_keys = get_org_api_keys(result["organization"])
                if "error" not in api_keys:
                    st.session_state.anthropic_api_key = api_keys["anthropic_api_key"]
                    st.session_state.serper_api_key = api_keys["serper_api_key"]
                    st.session_state.organization_name = api_keys["organization_name"]

                # Clear pending verification
                if "pending_verification_email" in st.session_state:
                    del st.session_state.pending_verification_email

                st.balloons()
                st.info("Redirecting to Research Assistant...")

                # Redirect to main page
                st.switch_page("streamlit_app.py")

    # Resend code option
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Resend Code"):
            result = call_lambda("resend_verification", {"email": email})
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("New verification code sent!")

    with col2:
        if st.button("← Back to Login"):
            if "pending_verification_email" in st.session_state:
                del st.session_state.pending_verification_email
            st.rerun()


def show_login():
    """Show login form."""
    st.subheader("🔐 Login")

    with st.form("login_form"):
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if not email or not password:
                st.error("Please enter email and password")
                return

            with st.spinner("Logging in..."):
                result = call_lambda("login", {
                    "email": email,
                    "password": password
                })

            if "error" in result:
                # Check if verification needed
                if result.get("requires_verification"):
                    st.error(f"❌ {result['error']}")
                    st.info("Please verify your email first.")
                    st.session_state.pending_verification_email = email
                    st.rerun()
                else:
                    st.error(f"❌ {result['error']}")
            else:
                st.success(f"✅ Welcome back, {result.get('name', 'User')}!")

                # Store auth info in session
                st.session_state.authenticated = True
                st.session_state.user_id = result["user_id"]
                st.session_state.user_email = result["email"]
                st.session_state.user_organization = result["organization"]
                st.session_state.user_token = result["token"]
                st.session_state.daily_limit = result["daily_limit"]
                st.session_state.user_name = result.get("name", "")

                # Fetch and store organization API keys
                api_keys = get_org_api_keys(result["organization"])
                if "error" not in api_keys:
                    st.session_state.anthropic_api_key = api_keys["anthropic_api_key"]
                    st.session_state.serper_api_key = api_keys["serper_api_key"]
                    st.session_state.organization_name = api_keys["organization_name"]

                st.balloons()
                st.info("Redirecting to Research Assistant...")

                # Redirect to main page
                st.switch_page("streamlit_app.py")


# Page config
st.set_page_config(
    page_title="MyRA - Authentication",
    page_icon="🔐",
    layout="centered"
)

# Main UI
st.title("🔍 MyRA Research Assistant")
st.markdown("### Multi-Organization Authentication")

# Check if already logged in
if st.session_state.get("authenticated"):
    st.success(f"✅ Already logged in as **{st.session_state.get('user_email')}**")
    st.info(f"Organization: **{st.session_state.get('user_organization')}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Go to Research Assistant", use_container_width=True):
            st.switch_page("streamlit_app.py")
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            # Clear session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
else:
    # Check if user needs to verify email
    if st.session_state.get("pending_verification_email"):
        # Show verification page directly
        show_verification()
    else:
        # Show login/signup tabs
        tabs = st.tabs(["🔐 Login", "📝 Sign Up"])

        with tabs[0]:
            show_login()

        with tabs[1]:
            show_signup()

# Footer
st.markdown("---")
st.markdown("""
**Organization-Based Access:**
- SNU Students: `@snu.ac.kr`
- McKinsey: `@mckinsey.com`
- BCG: `@bcg.com`
- Bain: `@bain.com`, `@baincompany.com`

Each organization has its own API keys and usage limits.
""")
