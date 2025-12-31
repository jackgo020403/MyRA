"""
Simple GUI for Research Assistant - No conversation, just run the research.
"""
import sys
import os
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QScrollArea, QFrame, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from dotenv import load_dotenv, set_key
from anthropic import Anthropic

from ra_orchestrator.state import RAState
from ra_orchestrator.agents.clarifier import run_clarifier
from ra_orchestrator.agents.planner import run_planner
from ra_orchestrator.agents.interactive_approval import run_interactive_approval
from ra_orchestrator.agents.schema_designer import run_schema_designer
from ra_orchestrator.agents.researcher_optimized import run_researcher
from ra_orchestrator.agents.synthesizer import run_synthesizer
from ra_orchestrator.agents.memo_generator import run_memo_generator
from ra_orchestrator.excel.writer import write_full_excel
from ra_orchestrator.excel.writer_m3 import write_milestone3_excel


class FeedbackDialog(QDialog):
    """Dialog for getting user feedback on scope/plan."""

    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(700, 400)

        layout = QVBoxLayout()

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("font-size: 11pt; margin-bottom: 10px;")
        layout.addWidget(msg_label)

        # Feedback text area
        self.feedback_input = QTextEdit()
        self.feedback_input.setPlaceholderText("Enter your feedback here, or click 'Approve' to proceed...")
        self.feedback_input.setStyleSheet("font-size: 11pt; padding: 8px;")
        layout.addWidget(self.feedback_input)

        # Buttons
        button_layout = QHBoxLayout()

        approve_btn = QPushButton("✓ Approve")
        approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-size: 11pt;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        approve_btn.clicked.connect(self.accept)

        revise_btn = QPushButton("↻ Revise")
        revise_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                font-size: 11pt;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0b7dda; }
        """)
        revise_btn.clicked.connect(self.reject)

        button_layout.addWidget(revise_btn)
        button_layout.addWidget(approve_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_feedback(self):
        return self.feedback_input.toPlainText().strip()


class ConfigDialog(QDialog):
    """Dialog for configuring API keys."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Configuration")
        self.setModal(True)
        self.resize(500, 200)

        layout = QFormLayout()

        self.anthropic_input = QLineEdit()
        self.anthropic_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Anthropic API Key:", self.anthropic_input)

        self.serper_input = QLineEdit()
        self.serper_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Serper API Key:", self.serper_input)

        # Load existing values
        load_dotenv()
        self.anthropic_input.setText(os.getenv("ANTHROPIC_API_KEY", ""))
        self.serper_input.setText(os.getenv("SERPER_API_KEY", ""))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_keys(self):
        return {
            "ANTHROPIC_API_KEY": self.anthropic_input.text().strip(),
            "SERPER_API_KEY": self.serper_input.text().strip()
        }


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Research Assistant - AI-Powered Research Tool")
        self.resize(900, 700)

        self.output_dir = Path(__file__).parent / "outputs"
        self.output_dir.mkdir(exist_ok=True, parents=True)

        load_dotenv()
        if not self._check_api_keys():
            self._show_config_dialog()

        self._init_ui()

    def _check_api_keys(self):
        """Check if API keys are configured."""
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        serper_key = os.getenv("SERPER_API_KEY")
        return bool(anthropic_key and serper_key)

    def _show_config_dialog(self):
        """Show configuration dialog."""
        dialog = ConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            keys = dialog.get_keys()
            env_path = Path(__file__).parent / ".env"
            for key, value in keys.items():
                if value:
                    set_key(env_path, key, value)
            load_dotenv(override=True)

    def _init_ui(self):
        """Initialize the UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Main content area
        content = QWidget()
        content.setStyleSheet("background-color: #2b2b2b;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Output area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
                font-size: 11pt;
            }
        """)
        content_layout.addWidget(self.output_area)

        # Input area
        input_frame = self._create_input_area()
        content_layout.addWidget(input_frame)

        layout.addWidget(content)

    def _create_header(self):
        """Create header section."""
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #1976D2;")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Title
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setSpacing(0)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Research Assistant")
        title.setStyleSheet("color: white; font-size: 20pt; font-weight: bold; background: transparent;")
        title_layout.addWidget(title)

        subtitle = QLabel("AI-Powered Research & Analysis")
        subtitle.setStyleSheet("color: #E3F2FD; font-size: 11pt; background: transparent;")
        title_layout.addWidget(subtitle)

        layout.addWidget(title_widget)
        layout.addStretch()

        # Settings button
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #0D47A1;
            }
        """)
        settings_btn.clicked.connect(self._show_config_dialog)
        layout.addWidget(settings_btn)

        return header

    def _create_input_area(self):
        """Create input area."""
        input_frame = QWidget()
        layout = QVBoxLayout(input_frame)
        layout.setContentsMargins(0, 10, 0, 0)

        # Label
        label = QLabel("Enter your research question:")
        label.setStyleSheet("color: white; font-size: 11pt;")
        layout.addWidget(label)

        # Input field
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("What would you like to research?")
        self.input_field.setMaximumHeight(100)
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
                font-size: 11pt;
            }
        """)
        layout.addWidget(self.input_field)

        # Button
        self.start_button = QPushButton("Start Research")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        self.start_button.clicked.connect(self._start_research)
        layout.addWidget(self.start_button)

        return input_frame

    def _log(self, message):
        """Add message to output area."""
        self.output_area.append(message)
        QApplication.processEvents()

    def _detect_scope(self, question: str, client: Anthropic) -> str:
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

    def _start_research(self):
        """Start the research process."""
        question = self.input_field.toPlainText().strip()
        if not question:
            QMessageBox.warning(self, "No Question", "Please enter a research question.")
            return

        if not self._check_api_keys():
            QMessageBox.warning(
                self, "API Keys Required",
                "Please configure your API keys in Settings."
            )
            self._show_config_dialog()
            return

        # Disable input
        self.input_field.setEnabled(False)
        self.start_button.setEnabled(False)
        self.output_area.clear()

        try:
            # Initialize Anthropic client
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            serper_key = os.getenv("SERPER_API_KEY")
            client = Anthropic(api_key=anthropic_key)

            # Initialize state
            state: RAState = {
                "research_question": question,
                "research_context": None,
                "research_plan": None,
                "approval_decision": None,
                "ledger_schema": None,
                "ledger_rows": [],
                "memo_block": None,
                "excel_path": None,
                "current_phase": "init",
                "iteration_count": 0,
                "scope_clarified": False,
            }

            # Step 0: Clarification (auto-detect scope without input())
            self._log("💬 Clarifying research scope...")
            QApplication.processEvents()

            # Auto-detect scope using Claude (non-interactive)
            detected_scope = self._detect_scope(question, client)
            state['research_context'] = f"{question}\n\nResearch Scope:\n{detected_scope}"
            state['scope_clarified'] = True

            # Show clarification dialog
            scope_msg = f"Proposed Research Scope:\n\n{state['research_context']}"
            dialog = FeedbackDialog("Scope Clarification", scope_msg, self)

            while dialog.exec() == QDialog.DialogCode.Rejected:
                feedback = dialog.get_feedback()
                if not feedback:
                    QMessageBox.information(self, "No Feedback", "Please provide feedback or click Approve.")
                    continue

                self._log(f"📝 User feedback: {feedback}\n")
                self._log("💬 Refining scope based on feedback...")
                QApplication.processEvents()

                # Re-detect scope with feedback
                refined_question = f"{question}\n\nUser feedback: {feedback}"
                detected_scope = self._detect_scope(refined_question, client)
                state['research_context'] = f"{question}\n\nRefined Research Scope:\n{detected_scope}\n\nUser feedback: {feedback}"

                scope_msg = f"Refined Research Scope:\n\n{detected_scope}"
                dialog = FeedbackDialog("Scope Clarification", scope_msg, self)

            self._log("✓ Scope clarified and approved\n")

            # Step 1: Planning
            self._log("📋 Creating research plan...")
            QApplication.processEvents()
            state = run_planner(state, client)

            # Step 2: Plan Approval
            self._log("📝 Review sub-questions and expected outputs...")
            QApplication.processEvents()

            # Show plan approval dialog
            plan_text = f"Research Title: {state['research_plan'].research_title}\n\n"
            plan_text += f"Sub-Questions ({len(state['research_plan'].sub_questions)}):\n\n"
            for i, sq in enumerate(state['research_plan'].sub_questions, 1):
                plan_text += f"{i}. {sq.question}\n"
                plan_text += f"   Rationale: {sq.rationale}\n"
                plan_text += f"   Expected Output: {sq.expected_output}\n\n"

            plan_dialog = FeedbackDialog("Research Plan Approval", plan_text, self)

            while plan_dialog.exec() == QDialog.DialogCode.Rejected:
                feedback = plan_dialog.get_feedback()
                if not feedback:
                    QMessageBox.information(self, "No Feedback", "Please provide feedback or click Approve.")
                    continue

                self._log(f"📝 User feedback on plan: {feedback}\n")
                self._log("📋 Revising research plan...")
                QApplication.processEvents()

                # Re-run planner with feedback
                state["research_context"] = f"{state['research_context']}\n\nUser feedback on plan: {feedback}"
                state = run_planner(state, client)

                plan_text = f"Revised Research Title: {state['research_plan'].research_title}\n\n"
                plan_text += f"Sub-Questions ({len(state['research_plan'].sub_questions)}):\n\n"
                for i, sq in enumerate(state['research_plan'].sub_questions, 1):
                    plan_text += f"{i}. {sq.question}\n"
                    plan_text += f"   Rationale: {sq.rationale}\n"
                    plan_text += f"   Expected Output: {sq.expected_output}\n\n"

                plan_dialog = FeedbackDialog("Research Plan Approval", plan_text, self)

            self._log("✓ Research plan approved\n")
            state["approval_decision"] = "approved"
            state["current_phase"] = "plan_approved"

            # Step 2: Schema Design
            self._log("📊 Step 2/5: Designing data schema...")
            QApplication.processEvents()
            state = run_schema_designer(state)
            self._log("✓ Schema designed\n")

            # Step 3: Research
            self._log("🔍 Step 3/5: Researching (searching 50 web sources)...")
            self._log("   This will take several minutes...\n")
            QApplication.processEvents()
            state = run_researcher(state, serper_key, client)
            self._log(f"✓ Collected {len(state['ledger_rows'])} evidence rows\n")

            # Save evidence Excel
            evidence_excel_path = write_full_excel(state, self.output_dir)
            self._log(f"✓ Evidence saved to: {evidence_excel_path}\n")

            # Step 4: Synthesis
            self._log("🧠 Step 4/5: Synthesizing findings...")
            QApplication.processEvents()
            state = run_synthesizer(state, client)
            self._log("✓ Synthesis complete\n")

            # Step 5: Memo Generation
            self._log("📝 Step 5/5: Generating executive memo...")
            QApplication.processEvents()
            state = run_memo_generator(state, client)
            self._log("✓ Memo generated\n")

            # Create final Excel
            self._log("📊 Creating final Excel report...")
            QApplication.processEvents()
            final_excel_path = write_milestone3_excel(state, evidence_excel_path, self.output_dir)

            # Success
            self._log("\n" + "="*60)
            self._log("✅ RESEARCH COMPLETE!")
            self._log("="*60)
            self._log(f"\n📊 Final Report: {final_excel_path}")
            self._log("\nThe report contains 3 tabs:")
            self._log("  1. MEMO - Executive summary")
            self._log("  2. SYNTHESIS - Detailed findings for each question")
            self._log("  3. RAW DATA - All evidence with source links")
            self._log("\nYou can start a new research question anytime!")

        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self._log(f"\n❌ ERROR:\n{error_msg}")
            QMessageBox.critical(self, "Research Failed", f"An error occurred:\n\n{str(e)}")

        finally:
            # Re-enable input
            self.input_field.setEnabled(True)
            self.start_button.setEnabled(True)
            self.input_field.clear()
            self.input_field.setFocus()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
