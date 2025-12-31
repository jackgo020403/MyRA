"""Setup validation script for RA Orchestrator."""
import sys
from pathlib import Path


def check_python_version():
    """Check Python version is 3.8+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected. Python 3.8+ required.")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if all dependencies are installed."""
    required = [
        "anthropic",
        "openpyxl",
        "langgraph",
        "langchain",
        "langchain_anthropic",
        "dotenv",
        "pydantic",
    ]

    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing.append(package)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    return True


def check_env_file():
    """Check if .env file exists and has API key."""
    env_path = Path(__file__).parent / ".env"

    if not env_path.exists():
        print("❌ .env file not found")
        print("Create .env file with: ANTHROPIC_API_KEY=your_key_here")
        return False

    print("✓ .env file exists")

    # Check if API key is present
    content = env_path.read_text()
    if "ANTHROPIC_API_KEY" not in content:
        print("❌ ANTHROPIC_API_KEY not found in .env")
        return False

    if "your_api_key_here" in content or "your_actual_api_key_here" in content:
        print("⚠️  .env file contains placeholder API key")
        print("Replace with your actual Anthropic API key")
        return False

    print("✓ ANTHROPIC_API_KEY present in .env")
    return True


def check_project_structure():
    """Check if all required files exist."""
    base = Path(__file__).parent
    required_files = [
        "ra_orchestrator/__init__.py",
        "ra_orchestrator/main.py",
        "ra_orchestrator/state.py",
        "ra_orchestrator/graph.py",
        "ra_orchestrator/agents/planner.py",
        "ra_orchestrator/agents/approval.py",
        "ra_orchestrator/agents/schema_designer.py",
        "ra_orchestrator/excel/writer.py",
        "ra_orchestrator/excel/styles.py",
        "ra_orchestrator/prompts/planner.md",
        "requirements.txt",
        "README.md",
    ]

    all_exist = True
    for file_path in required_files:
        full_path = base / file_path
        if not full_path.exists():
            print(f"❌ Missing: {file_path}")
            all_exist = False

    if all_exist:
        print(f"✓ All {len(required_files)} required files present")

    return all_exist


def check_outputs_dir():
    """Check/create outputs directory."""
    outputs_dir = Path(__file__).parent / "outputs"

    if not outputs_dir.exists():
        outputs_dir.mkdir(parents=True, exist_ok=True)
        print("✓ Created outputs/ directory")
    else:
        print("✓ outputs/ directory exists")

    return True


def main():
    """Run all validation checks."""
    print("=" * 80)
    print("RA ORCHESTRATOR - Setup Validation")
    print("=" * 80)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Output Directory", check_outputs_dir),
    ]

    results = []

    for name, check_func in checks:
        print(f"\n[{name}]")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error during check: {e}")
            results.append(False)

    print("\n" + "=" * 80)
    if all(results):
        print("✓ ALL CHECKS PASSED")
        print("=" * 80)
        print("\nYou're ready to run the RA Orchestrator!")
        print("\nRun: python -m ra_orchestrator.main")
        print()
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 80)
        print("\nPlease fix the issues above before running.")
        print("See QUICKSTART.md for setup instructions.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
