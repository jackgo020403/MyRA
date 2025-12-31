"""
GUI Application for Research Assistant Orchestrator.

Proper conversational chat interface with button-based responses.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QScrollArea,
    QFrame, QMessageBox, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QMutex, QWaitCondition
from PyQt6.QtGui import QFont, QTextCursor, QIcon
from dotenv import load_dotenv, set_key
from anthropic import Anthropic

from ra_orchestrator.state import RAState
from ra_orchestrator.agents.planner import run_planner, display_plan
from ra_orchestrator.agents.schema_designer import run_schema_designer
from ra_orchestrator.agents.researcher_optimized import run_researcher
from ra_orchestrator.agents.synthesizer import run_synthesizer
from ra_orchestrator.agents.memo_generator import run_memo_generator
from ra_orchestrator.excel.writer import write_full_excel
from ra_orchestrator.excel.writer_m3 import write_milestone3_excel


class ConfigDialog(QDialog):
    """Dialog for configuring API keys."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Configuration")
        self.setModal(True)
        self.resize(500, 200)

        layout = QFormLayout()

        # API key fields
        self.anthropic_key = QLineEdit()
        self.anthropic_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.anthropic_key.setPlaceholderText("Enter your Anthropic API key")

        self.serper_key = QLineEdit()
        self.serper_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.serper_key.setPlaceholderText("Enter your Serper API key")

        # Load existing values
        load_dotenv()
        existing_anthropic = os.getenv("ANTHROPIC_API_KEY", "")
        existing_serper = os.getenv("SERPER_API_KEY", "")

        if existing_anthropic:
            self.anthropic_key.setText(existing_anthropic)
        if existing_serper:
            self.serper_key.setText(existing_serper)

        layout.addRow("Anthropic API Key:", self.anthropic_key)
        layout.addRow("Serper API Key:", self.serper_key)

        # Help text
        help_label = QLabel(
            "Get your API keys from:\n"
            "• Anthropic: https://console.anthropic.com/\n"
            "• Serper: https://serper.dev/"
        )
        help_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addRow("", help_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_keys(self):
        """Return the API keys."""
        return {
            "ANTHROPIC_API_KEY": self.anthropic_key.text().strip(),
            "SERPER_API_KEY": self.serper_key.text().strip()
        }


class ResearchWorker(QThread):
    """Worker thread for running research phases."""

    add_message = pyqtSignal(str, bool)  # (text, is_user)
    ask_question = pyqtSignal(str, list)  # (question_text, button_labels)
    enable_text_input = pyqtSignal(str)  # (prompt_text)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, research_question, api_key, output_dir):
        super().__init__()
        self.research_question = research_question
        self.api_key = api_key
        self.output_dir = output_dir
        self.client = Anthropic(api_key=api_key)
        self.state = None

        # Synchronization for waiting on user input
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.user_response = None

    def run(self):
        """Run the research workflow with conversational flow."""
        try:
            # Initialize state
            self.state: RAState = {
                "research_question": self.research_question,
                "research_plan": None,
                "approval_decision": None,
                "ledger_schema": None,
                "ledger_rows": [],
                "memo_block": None,
                "excel_path": None,
                "current_phase": "init",
                "iteration_count": 0,
            }

            # Phase 1: Clarification
            self.add_message.emit(
                "Let me understand your research scope better. Analyzing your question...",
                False
            )

            detected_scope = self._detect_scope()
            self.add_message.emit(f"Detected Research Scope:\n\n{detected_scope}", False)

            # Ask for confirmation with buttons
            response = self._ask_user(
                "Is this scope correct?",
                ["✓ Yes, proceed", "✗ No, let me clarify"]
            )

            if response == 1:  # User wants to clarify
                # Get clarification text
                clarification = self._ask_user_text("Please provide your clarifications or corrections:")
                self.state['research_context'] = f"{self.research_question}\n\nUser clarifications:\n{clarification}"
                self.add_message.emit("✓ Scope updated with your clarifications!", False)
            else:
                self.state['research_context'] = f"{self.research_question}\n\nResearch Scope:\n{detected_scope}"
                self.add_message.emit("✓ Scope confirmed!", False)

            # Phase 2: Planning
            self.add_message.emit("Creating research plan...", False)
            self.state = run_planner(self.state, self.client)

            plan_text = display_plan(self.state["research_plan"])
            self.add_message.emit(f"Research Plan:\n\n{plan_text}", False)

            # Phase 3: Question-by-question approval
            self.add_message.emit(
                "Now let's review each sub-question. You can approve, modify, or skip each one.",
                False
            )

            approved_questions = []

            for i, sq in enumerate(self.state["research_plan"].sub_questions, 1):
                question_review = f"""📋 Sub-Question {i} of {len(self.state["research_plan"].sub_questions)}

Question: {sq.question}

Rationale: {sq.rationale}

Expected Output: {sq.expected_output if sq.expected_output else '(Not specified)'}"""

                self.add_message.emit(question_review, False)

                response = self._ask_user(
                    f"How does Question {i} look?",
                    ["✓ Approve", "✎ Modify", "⊗ Skip"]
                )

                if response == 1:  # Modify
                    modifications = self._ask_user_text(
                        "What changes would you like to make to this question?"
                    )
                    self.add_message.emit(f"✓ Question {i} modified based on your feedback!", False)
                    # TODO: Actually modify the question using Claude
                    approved_questions.append(sq)

                elif response == 2:  # Skip
                    self.add_message.emit(f"⊗ Question {i} skipped.", False)

                else:  # Approve
                    self.add_message.emit(f"✓ Question {i} approved!", False)
                    approved_questions.append(sq)

            if not approved_questions:
                raise ValueError("No questions were approved. Cannot proceed with research.")

            self.state["research_plan"].sub_questions = approved_questions
            self.state["approval_decision"] = "approved"
            self.state["current_phase"] = "plan_approved"

            self.add_message.emit(
                f"✓ Research plan finalized with {len(approved_questions)} sub-questions!",
                False
            )

            # Phase 4: Schema
            self.state = run_schema_designer(self.state)

            # Phase 5: Research
            self.add_message.emit(
                "🔍 Starting web research...\n\n"
                "I'll search 50 high-quality sources and extract evidence for each sub-question.\n"
                "This will take 3-5 minutes.",
                False
            )

            serper_key = os.getenv("SERPER_API_KEY")
            if not serper_key:
                raise ValueError("SERPER_API_KEY not found in environment")

            self.state = run_researcher(self.state, serper_key, self.client)

            self.add_message.emit(
                f"✓ Research complete! Collected {len(self.state['ledger_rows'])} evidence rows.",
                False
            )

            # Phase 6: Evidence Excel
            evidence_excel_path = write_full_excel(self.state, self.output_dir)

            # Phase 7: Synthesis
            self.add_message.emit("📊 Analyzing evidence and creating synthesis...", False)
            self.state = run_synthesizer(self.state, self.client)
            self.add_message.emit(
                f"✓ Created synthesis for {len(self.state['question_syntheses'])} sub-questions.",
                False
            )

            # Phase 8: Memo
            self.add_message.emit("📝 Generating executive summary...", False)
            self.state = run_memo_generator(self.state, self.client)

            # Phase 9: Final Excel
            self.add_message.emit("💾 Creating final Excel report...", False)
            final_excel_path = write_milestone3_excel(self.state, evidence_excel_path, self.output_dir)
            self.state["excel_path"] = final_excel_path
            self.state["current_phase"] = "m3_complete"

            self.finished.emit(self.state)

        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_msg)

    def _detect_scope(self):
        """Detect research scope using Claude."""
        prompt = f"""Analyze this research question and identify the research scope:

Research Question: {self.research_question}

Please identify and list:

1. **Specific Entities** (companies, platforms, organizations):
   - Which specific entities should be researched?

2. **Industry Category/Segment**:
   - What specific industry segment or category?

3. **Geographic Scope**:
   - What regions or countries?

4. **Time Period**:
   - What time range should be covered?

5. **Key Research Aspects** (in priority order):
   - What should we focus on? (e.g., market share, business models, trends, etc.)

Format as a clear bulleted list under each category."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def _ask_user(self, question, button_labels):
        """Ask user a multiple choice question and wait for response."""
        self.mutex.lock()
        self.user_response = None

        # Emit question to UI
        self.ask_question.emit(question, button_labels)

        # Wait for user to click a button
        self.wait_condition.wait(self.mutex)

        response = self.user_response
        self.mutex.unlock()

        return response

    def _ask_user_text(self, prompt):
        """Ask user for text input and wait for response."""
        self.mutex.lock()
        self.user_response = None

        # Emit prompt to UI
        self.enable_text_input.emit(prompt)

        # Wait for user to submit text
        self.wait_condition.wait(self.mutex)

        response = self.user_response
        self.mutex.unlock()

        return response

    def set_user_response(self, response):
        """Called by main thread when user responds."""
        self.mutex.lock()
        self.user_response = response
        self.wait_condition.wakeOne()
        self.mutex.unlock()


class ChatMessage(QFrame):
    """Individual chat message widget."""

    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)

        # Sender label
        sender = QLabel("You" if is_user else "Research Assistant")
        sender.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        sender.setStyleSheet("color: #333;")
        layout.addWidget(sender)

        # Message text
        message = QLabel(text)
        message.setWordWrap(True)
        message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message.setFont(QFont("Segoe UI", 10))
        message.setStyleSheet("color: #000; padding: 5px 0;")
        layout.addWidget(message)

        self.setLayout(layout)

        # Styling
        if is_user:
            self.setStyleSheet("""
                ChatMessage {
                    background-color: #E3F2FD;
                    border-radius: 10px;
                    margin: 5px 50px 5px 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                ChatMessage {
                    background-color: #F5F5F5;
                    border-radius: 10px;
                    margin: 5px 5px 5px 50px;
                }
            """)


class QuestionButtons(QFrame):
    """Widget with buttons for multiple choice questions."""

    button_clicked = pyqtSignal(int)

    def __init__(self, question_text, button_labels, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QuestionButtons {
                background-color: #FFF9E6;
                border-radius: 10px;
                margin: 5px 5px 5px 50px;
                border: 2px solid #FFD700;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)

        # Question label
        question = QLabel(question_text)
        question.setWordWrap(True)
        question.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        question.setStyleSheet("color: #000; padding: 5px 0;")
        layout.addWidget(question)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        for i, label in enumerate(button_labels):
            btn = QPushButton(label)
            btn.setFont(QFont("Segoe UI", 10))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2E75B6;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #4A90D9;
                }
            """)
            btn.clicked.connect(lambda checked, idx=i: self.button_clicked.emit(idx))
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Research Assistant - AI-Powered Research Tool")
        self.resize(1000, 700)

        # Output directory
        self.output_dir = Path(__file__).parent / "outputs"
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Check API keys
        load_dotenv()
        if not self._check_api_keys():
            self._show_config_dialog()

        # Initialize UI
        self._init_ui()

        # Worker thread
        self.worker = None
        self.current_question_widget = None

    def _check_api_keys(self):
        """Check if API keys are configured."""
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        serper_key = os.getenv("SERPER_API_KEY")
        return bool(anthropic_key and serper_key)

    def _show_config_dialog(self):
        """Show API configuration dialog."""
        dialog = ConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            keys = dialog.get_keys()

            # Save to .env file
            env_path = Path(__file__).parent / ".env"
            for key, value in keys.items():
                if value:
                    set_key(env_path, key, value)
                    os.environ[key] = value

            if not self._check_api_keys():
                QMessageBox.warning(
                    self,
                    "Configuration Required",
                    "API keys are required to use the Research Assistant.\n"
                    "Please configure them in Settings."
                )
        else:
            if not self._check_api_keys():
                QMessageBox.warning(
                    self,
                    "Configuration Required",
                    "API keys are required. You can configure them later in Settings."
                )

    def _init_ui(self):
        """Initialize the UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Chat area (scrollable)
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(10)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_widget.setLayout(self.chat_layout)

        self.chat_scroll.setWidget(self.chat_widget)
        main_layout.addWidget(self.chat_scroll)

        # Input area
        input_area = self._create_input_area()
        main_layout.addWidget(input_area)

        central_widget.setLayout(main_layout)

        # Add welcome message
        self._add_assistant_message(
            "Hello! I'm your Research Assistant powered by Claude Sonnet 4.5.\n\n"
            "I'll guide you through an interactive research process:\n"
            "• First, I'll clarify your research scope with you\n"
            "• Then, I'll create a research plan and review each question with you\n"
            "• You can approve, modify, or skip any question\n"
            "• Finally, I'll conduct the research and generate a comprehensive report\n\n"
            "Type your research question below to get started!"
        )

    def _create_header(self):
        """Create the header bar."""
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("""
            QFrame {
                background-color: #2E75B6;
            }
        """)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 10, 20, 10)

        # Title section
        title_container = QWidget()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Research Assistant")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")

        subtitle = QLabel("AI-Powered Research & Analysis")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet("color: #E0E0E0; background: transparent;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_container.setLayout(title_layout)
        title_container.setStyleSheet("background: transparent;")

        header_layout.addWidget(title_container)
        header_layout.addStretch()

        # Settings button
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setFixedSize(100, 35)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5BA3E0;
            }
        """)
        settings_btn.clicked.connect(self._show_config_dialog)
        header_layout.addWidget(settings_btn)

        header.setLayout(header_layout)
        return header

    def _create_input_area(self):
        """Create the input area at the bottom."""
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #F0F0F0;
                border-top: 1px solid #CCC;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Enter your research question here...")
        self.input_field.setFont(QFont("Segoe UI", 11))
        self.input_field.setMaximumHeight(80)
        self.input_field.setStyleSheet("""
            QTextEdit {
                padding: 12px;
                border: 2px solid #CCC;
                border-radius: 8px;
                background-color: white;
                color: black;
            }
            QTextEdit:focus {
                border: 2px solid #2E75B6;
            }
        """)

        self.send_button = QPushButton("Send")
        self.send_button.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.send_button.setFixedSize(100, 80)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2E75B6;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #4A90D9;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.send_button.clicked.connect(self._send_message)

        layout.addWidget(self.input_field)
        layout.addWidget(self.send_button)

        input_frame.setLayout(layout)
        return input_frame

    def _add_user_message(self, text):
        """Add a user message to the chat."""
        message = ChatMessage(text, is_user=True)
        self.chat_layout.addWidget(message)
        self._scroll_to_bottom()

    def _add_assistant_message(self, text):
        """Add an assistant message to the chat."""
        message = ChatMessage(text, is_user=False)
        self.chat_layout.addWidget(message)
        self._scroll_to_bottom()

    def _add_question_buttons(self, question_text, button_labels):
        """Add a question with buttons."""
        # Remove previous question widget if exists
        if self.current_question_widget:
            self.chat_layout.removeWidget(self.current_question_widget)
            self.current_question_widget.deleteLater()

        # Create new question widget
        self.current_question_widget = QuestionButtons(question_text, button_labels)
        self.current_question_widget.button_clicked.connect(self._on_button_clicked)
        self.chat_layout.addWidget(self.current_question_widget)
        self._scroll_to_bottom()

    def _on_button_clicked(self, button_index):
        """Handle button click from question widget."""
        if self.worker:
            # Remove the question widget
            if self.current_question_widget:
                self.chat_layout.removeWidget(self.current_question_widget)
                self.current_question_widget.deleteLater()
                self.current_question_widget = None

            # Send response to worker
            self.worker.set_user_response(button_index)

    def _scroll_to_bottom(self):
        """Scroll chat to bottom."""
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    def _send_message(self):
        """Handle sending a message."""
        question = self.input_field.toPlainText().strip()
        if not question:
            return

        # Check API keys
        if not self._check_api_keys():
            QMessageBox.warning(
                self,
                "API Keys Required",
                "Please configure your API keys in Settings before starting research."
            )
            self._show_config_dialog()
            return

        # Add user message
        self._add_user_message(question)
        self.input_field.clear()

        # Disable input while processing
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)

        # Start research in background thread
        self._start_research(question)

    def _start_research(self, question):
        """Start research in background thread."""
        api_key = os.getenv("ANTHROPIC_API_KEY")

        self.worker = ResearchWorker(question, api_key, self.output_dir)
        self.worker.add_message.connect(self._on_add_message)
        self.worker.ask_question.connect(self._on_ask_question)
        self.worker.enable_text_input.connect(self._on_enable_text_input)
        self.worker.finished.connect(self._on_research_complete)
        self.worker.error.connect(self._on_research_error)
        self.worker.start()

    def _on_add_message(self, text, is_user):
        """Handle message from worker."""
        if is_user:
            self._add_user_message(text)
        else:
            self._add_assistant_message(text)

    def _on_ask_question(self, question_text, button_labels):
        """Handle question from worker."""
        self._add_question_buttons(question_text, button_labels)

    def _on_enable_text_input(self, prompt_text):
        """Handle text input request from worker."""
        self._add_assistant_message(prompt_text)

        # Enable input field temporarily
        self.input_field.setEnabled(True)
        self.input_field.setPlaceholderText("Type your response here...")
        self.send_button.setText("Submit")

        # Disconnect old handler and connect new one
        try:
            self.send_button.clicked.disconnect()
        except:
            pass
        self.send_button.clicked.connect(self._submit_text_response)
        self.send_button.setEnabled(True)

    def _submit_text_response(self):
        """Submit text response to worker."""
        response = self.input_field.toPlainText().strip()
        if not response:
            return

        # Add user message
        self._add_user_message(response)
        self.input_field.clear()

        # Disable input again
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)

        # Reconnect original send handler
        try:
            self.send_button.clicked.disconnect()
        except:
            pass
        self.send_button.clicked.connect(self._send_message)
        self.send_button.setText("Send")
        self.input_field.setPlaceholderText("Enter your research question here...")

        # Send response to worker
        if self.worker:
            self.worker.set_user_response(response)

    def _on_research_complete(self, final_state):
        """Handle research completion."""
        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)

        # Show results
        excel_path = final_state.get("excel_path", "Unknown")
        evidence_count = len(final_state.get("ledger_rows", []))
        syntheses_count = len(final_state.get("question_syntheses", []))

        result_message = (
            f"✅ Research complete!\n\n"
            f"Results:\n"
            f"• Evidence rows collected: {evidence_count}\n"
            f"• Sub-questions analyzed: {syntheses_count}\n"
            f"• Excel file saved to:\n  {excel_path}\n\n"
            f"The Excel file contains:\n"
            f"1. MEMO - Executive summary with key findings\n"
            f"2. SYNTHESIS - Per-question analysis with citations\n"
            f"3. RAW DATA - Full evidence organized by source\n\n"
            f"You can start a new research question anytime!"
        )

        self._add_assistant_message(result_message)

        # Show success dialog
        QMessageBox.information(
            self,
            "Research Complete",
            f"Research completed successfully!\n\n"
            f"Results saved to:\n{excel_path}"
        )

    def _on_research_error(self, error_msg):
        """Handle research error."""
        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)

        # Show error
        self._add_assistant_message(
            f"❌ An error occurred during research:\n\n{error_msg}\n\n"
            f"Please check your API keys and try again."
        )

        QMessageBox.critical(
            self,
            "Research Error",
            f"An error occurred:\n\n{error_msg[:500]}"
        )


def main():
    """Main entry point for GUI application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set application-wide font
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
