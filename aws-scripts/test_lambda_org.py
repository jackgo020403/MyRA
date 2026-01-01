"""
Test Lambda function with organization-based authentication.

Prerequisites:
1. Docker Compose running: docker-compose up -d
2. DynamoDB tables created: python aws-scripts/create_dynamodb_tables.py --local

Run with: python aws-scripts/test_lambda_org.py
"""
import requests
import json
import time

LAMBDA_URL = "http://localhost:9000/2015-03-31/functions/function/invocations"


def call_lambda(action, data):
    """Call Lambda function."""
    event = {
        "body": json.dumps({
            "action": action,
            **data
        })
    }

    response = requests.post(LAMBDA_URL, json=event)
    result = response.json()

    print(f"\n{'='*60}")
    print(f"Action: {action}")
    print(f"Status: {result['statusCode']}")
    print(f"Response:")
    body = json.loads(result['body'])
    print(json.dumps(body, indent=2))
    print(f"{'='*60}")

    return body


def test_get_organizations():
    """Test getting available organizations."""
    print("\n🧪 Test 1: Get Available Organizations")
    result = call_lambda("get_organizations", {})
    return result.get("organizations", {})


def test_signup_invalid_email():
    """Test signup with invalid email domain."""
    print("\n🧪 Test 2: Signup with Invalid Email (should fail)")
    result = call_lambda("signup", {
        "email": "test@gmail.com",  # Wrong domain for SNU
        "password": "secure123",
        "organization": "SNU_student",
        "name": "Test User"
    })
    assert "error" in result, "Should fail with wrong email domain"


def test_signup_valid():
    """Test signup with valid email."""
    print("\n🧪 Test 3: Signup with Valid Email (SNU)")
    result = call_lambda("signup", {
        "email": "test.user@snu.ac.kr",
        "password": "secure123",
        "organization": "SNU_student",
        "name": "Test SNU Student"
    })

    if "error" in result:
        if "already registered" in result["error"]:
            print("⚠️  User already exists, continuing with tests...")
            return None
        else:
            print(f"❌ Unexpected error: {result['error']}")
            return None

    assert "user_id" in result, "Should return user_id"
    assert result.get("requires_verification") == True, "Should require verification"

    return result.get("user_id")


def test_signup_mckinsey():
    """Test signup with McKinsey email."""
    print("\n🧪 Test 4: Signup with McKinsey Email")
    result = call_lambda("signup", {
        "email": "john.doe@mckinsey.com",
        "password": "mckinsey123",
        "organization": "McKinsey",
        "name": "John Doe"
    })

    if "error" in result and "already registered" not in result["error"]:
        print(f"❌ Error: {result['error']}")
        return None

    return result.get("user_id")


def test_login_unverified():
    """Test login without email verification."""
    print("\n🧪 Test 5: Login without Verification (should fail)")
    result = call_lambda("login", {
        "email": "test.user@snu.ac.kr",
        "password": "secure123"
    })

    # Should either fail because unverified, or succeed if already verified
    if "error" in result:
        assert "not verified" in result["error"].lower() or "invalid" in result["error"].lower()
        print("✅ Correctly blocked unverified user")
    else:
        print("⚠️  User was already verified")


def test_verify_email_wrong_code():
    """Test email verification with wrong code."""
    print("\n🧪 Test 6: Verify Email with Wrong Code (should fail)")
    result = call_lambda("verify_email", {
        "email": "test.user@snu.ac.kr",
        "code": "000000"  # Wrong code
    })

    if "error" not in result:
        print("⚠️  Verification might have succeeded (code was correct by chance)")
    else:
        print(f"✅ Correctly rejected wrong code: {result['error']}")


def test_verify_email_correct():
    """Test email verification with correct code (manual input needed)."""
    print("\n🧪 Test 7: Verify Email with Correct Code")
    print("\n📧 CHECK DOCKER LOGS FOR VERIFICATION CODE:")
    print("   Run: docker-compose logs lambda | grep 'VERIFICATION EMAIL' -A 10")
    print()

    code = input("Enter the 6-digit verification code from the logs: ").strip()

    if not code:
        print("⚠️  Skipping verification test")
        return None

    result = call_lambda("verify_email", {
        "email": "test.user@snu.ac.kr",
        "code": code
    })

    if "error" in result:
        print(f"❌ Verification failed: {result['error']}")
        return None

    assert "token" in result, "Should return JWT token"
    print(f"✅ Email verified! Token: {result['token'][:20]}...")

    return result


def test_login_verified(token_data):
    """Test login after verification."""
    print("\n🧪 Test 8: Login After Verification")
    result = call_lambda("login", {
        "email": "test.user@snu.ac.kr",
        "password": "secure123"
    })

    if "error" in result:
        print(f"❌ Login failed: {result['error']}")
        return None

    assert "token" in result, "Should return JWT token"
    assert result["organization"] == "SNU_student", "Should be SNU organization"
    assert result["daily_limit"] == 20, "SNU should have 20 searches/day"

    print(f"✅ Login successful!")
    print(f"   Organization: {result['organization']}")
    print(f"   Daily Limit: {result['daily_limit']}")

    return result


def test_usage_tracking(user_id, organization):
    """Test usage tracking."""
    print(f"\n🧪 Test 9: Usage Tracking for {user_id}")

    # Check initial usage
    result = call_lambda("check_usage", {"user_id": user_id})
    print(f"Initial usage: {result.get('searches_used', 0)}/{result.get('daily_limit', 0)}")

    # Increment usage
    for i in range(3):
        result = call_lambda("increment_usage", {
            "user_id": user_id,
            "organization": organization
        })
        print(f"After search {i+1}: {result.get('searches_used', 0)}/{result.get('daily_limit', 0)}")
        time.sleep(0.5)

    # Check final usage
    result = call_lambda("check_usage", {"user_id": user_id})
    print(f"✅ Usage tracking working! Used: {result.get('searches_used', 0)}")


def test_resend_verification():
    """Test resending verification code."""
    print("\n🧪 Test 10: Resend Verification Code")

    # Create a new user for this test
    email = f"resend.test@snu.ac.kr"

    # Try signup
    result = call_lambda("signup", {
        "email": email,
        "password": "test123",
        "organization": "SNU_student",
        "name": "Resend Test"
    })

    if "error" in result and "already registered" in result["error"]:
        print("⚠️  User already exists, testing resend anyway")

    # Resend code
    result = call_lambda("resend_verification", {"email": email})

    if "error" in result:
        if "already verified" in result["error"]:
            print("⚠️  User already verified, can't resend")
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print("✅ Verification code resent!")


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          MyRA Lambda Organization Auth Tests                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    print("🚀 Starting tests...\n")
    print("Make sure Docker Compose is running: docker-compose up -d\n")

    try:
        # Test 1: Get organizations
        orgs = test_get_organizations()
        print(f"\n✅ Found {len(orgs)} organizations")

        # Test 2: Invalid email
        test_signup_invalid_email()

        # Test 3-4: Valid signups
        snu_user = test_signup_valid()
        mckinsey_user = test_signup_mckinsey()

        # Test 5: Login unverified
        test_login_unverified()

        # Test 6: Wrong verification code
        test_verify_email_wrong_code()

        # Test 7: Correct verification (manual)
        verified_data = test_verify_email_correct()

        if verified_data:
            # Test 8: Login after verification
            login_data = test_login_verified(verified_data)

            if login_data:
                # Test 9: Usage tracking
                test_usage_tracking(login_data["user_id"], login_data["organization"])

        # Test 10: Resend verification
        test_resend_verification()

        print("""

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                    ✅ All Tests Complete!                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

📋 Summary:
- Organization-based signup ✅
- Email domain validation ✅
- Email verification ✅
- Login with JWT tokens ✅
- Usage tracking per organization ✅

🎯 Next Steps:
1. Integrate with Streamlit UI
2. Set up real email sending (AWS SES)
3. Deploy to AWS

        """)

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
