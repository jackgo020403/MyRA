"""
GUI Application for Research Assistant - True Conversational Interface.

Natural back-and-forth conversation like ChatGPT - AI is your thought partner.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from enum import Enum
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QScrollArea,
    QFrame, QMessageBox, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QIcon
from dotenv import load_dotenv, set_key
from anthropic import Anthropic

from ra_orchestrator.state import RAState, SubQuestion
from ra_orchestrator.agents.planner import run_planner
from ra_orchestrator.agents.schema_designer import run_schema_designer
from ra_orchestrator.agents.researcher_optimized import run_researcher
from ra_orchestrator.agents.synthesizer import run_synthesizer
from ra_orchestrator.agents.memo_generator import run_memo_generator
from ra_orchestrator.excel.writer import write_full_excel
from ra_orchestrator.excel.writer_m3 import write_milestone3_excel


class ConversationState(Enum):
    """Current state in the conversation flow."""
    INITIAL = "initial"
    SCOPE_DETECTION = "scope_detection"
    SCOPE_REFINEMENT = "scope_refinement"
    PLAN_CREATION = "plan_creation"
    PLAN_REVIEW = "plan_review"
    QUESTION_REVIEW = "question_review"
    RESEARCH_RUNNING = "research_running"
    COMPLETE = "complete"


class ConfigDialog(QDialog):
    """Dialog for configuring API keys."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Configuration")
        self.setModal(True)
        self.resize(500, 200)

        layout = QFormLayout()

        self.anthropic_key = QLineEdit()
        self.anthropic_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.anthropic_key.setPlaceholderText("Enter your Anthropic API key")

        self.serper_key = QLineEdit()
        self.serper_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.serper_key.setPlaceholderText("Enter your Serper API key")

        load_dotenv()
        existing_anthropic = os.getenv("ANTHROPIC_API_KEY", "")
        existing_serper = os.getenv("SERPER_API_KEY", "")

        if existing_anthropic:
            self.anthropic_key.setText(existing_anthropic)
        if existing_serper:
            self.serper_key.setText(existing_serper)

        layout.addRow("Anthropic API Key:", self.anthropic_key)
        layout.addRow("Serper API Key:", self.serper_key)

        help_label = QLabel(
            "Get your API keys from:\n"
            "• Anthropic: https://console.anthropic.com/\n"
            "• Serper: https://serper.dev/"
        )
        help_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addRow("", help_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_keys(self):
        return {
            "ANTHROPIC_API_KEY": self.anthropic_key.text().strip(),
            "SERPER_API_KEY": self.serper_key.text().strip()
        }


class ConversationManager:
    """Manages the conversational flow - AI's thought partner logic."""

    def __init__(self, client: Anthropic, research_question: str):
        self.client = client
        self.initial_question = research_question
        self.conversation_state = ConversationState.INITIAL

        # Conversation memory
        self.detected_scope = None
        self.refined_scope = None
        self.research_plan = None
        self.approved_questions = []
        self.conversation_history = []

        # Current question being reviewed
        self.current_question_index = 0
        self.questions_to_review = []

    def get_next_message(self, user_message=None):
        """
        Get AI's next message based on conversation state and user's last message.

        Returns: (ai_message, needs_user_input, conversation_continues)
                 ai_message can be "NEED_PLANNING" to signal MainWindow to start planner thread
        """
        if user_message:
            self.conversation_history.append(("user", user_message))

        if self.conversation_state == ConversationState.INITIAL:
            return self._start_scope_detection()

        elif self.conversation_state == ConversationState.SCOPE_DETECTION:
            return self._handle_scope_feedback(user_message)

        elif self.conversation_state == ConversationState.SCOPE_REFINEMENT:
            return self._handle_scope_refinement(user_message)

        elif self.conversation_state == ConversationState.PLAN_CREATION:
            # Signal to GUI that planner needs to run in worker thread
            return "NEED_PLANNING", False, True

        elif self.conversation_state == ConversationState.PLAN_REVIEW:
            return self._handle_plan_review(user_message)

        elif self.conversation_state == ConversationState.QUESTION_REVIEW:
            return self._handle_question_review(user_message)

    def _start_scope_detection(self):
        """AI starts by detecting and proposing scope."""
        self.conversation_state = ConversationState.SCOPE_DETECTION

        prompt = f"""Analyze this research question and propose a research scope:

Research Question: {self.initial_question}

Please identify:
1. Specific entities to research
2. Industry/domain
3. Geographic scope
4. Time period
5. Key aspects to focus on

Format as a conversational proposal, like you're discussing with a colleague."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        self.detected_scope = response.content[0].text
        self.conversation_history.append(("assistant", self.detected_scope))

        ai_message = (
            f"Great question! Let me break down what I think we should research:\n\n"
            f"{self.detected_scope}\n\n"
            f"Does this capture what you're looking for? Feel free to clarify, add, or change anything!"
        )

        return ai_message, True, True  # needs input, continues

    def _handle_scope_feedback(self, user_message):
        """AI processes user's feedback on scope."""
        # Use Claude to understand user's feedback
        prompt = f"""The user gave this feedback on the research scope:

User feedback: {user_message}

Original scope:
{self.detected_scope}

Analyze the user's feedback:
1. Are they happy with the scope? (yes/no/partially)
2. What specific changes or clarifications did they make?
3. What questions should I ask to better understand their needs?

Return a JSON object:
{{
    "satisfied": true/false,
    "needs_more_clarification": true/false,
    "clarification_questions": ["question1", "question2"],
    "updated_scope": "refined scope based on feedback"
}}"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        import re
        text = response.content[0].text
        if "```json" in text:
            json_start = text.find("```json") + 7
            json_end = text.find("```", json_start)
            text = text[json_start:json_end].strip()
        elif "```" in text:
            json_start = text.find("```") + 3
            json_end = text.find("```", json_start)
            text = text[json_start:json_end].strip()

        try:
            analysis = json.loads(text)
        except:
            # Fallback - just proceed
            analysis = {
                "satisfied": True,
                "needs_more_clarification": False,
                "clarification_questions": [],
                "updated_scope": self.detected_scope + f"\n\nUser additions: {user_message}"
            }

        if analysis.get("needs_more_clarification"):
            # Ask follow-up questions
            questions = analysis.get("clarification_questions", [])
            ai_message = "Thanks for that feedback! A few follow-up questions to make sure I understand:\n\n"
            for i, q in enumerate(questions, 1):
                ai_message += f"{i}. {q}\n"

            self.conversation_state = ConversationState.SCOPE_REFINEMENT
            self.conversation_history.append(("assistant", ai_message))
            return ai_message, True, True

        else:
            # Scope is clear, move to planning
            self.refined_scope = analysis.get("updated_scope", self.detected_scope)
            self.conversation_state = ConversationState.PLAN_CREATION

            ai_message = (
                "Perfect! I have a clear understanding now. Let me create a research plan with specific sub-questions.\n\n"
                "This will take a moment..."
            )
            self.conversation_history.append(("assistant", ai_message))

            return ai_message, False, True  # No input needed, continues

    def _handle_scope_refinement(self, user_message):
        """Handle additional scope refinement conversation."""
        # Update scope with new info
        self.refined_scope = f"{self.detected_scope}\n\nAdditional context from conversation:\n{user_message}"
        self.conversation_state = ConversationState.PLAN_CREATION

        ai_message = (
            "Got it! That really helps clarify things. Let me now create a detailed research plan.\n\n"
            "One moment..."
        )
        self.conversation_history.append(("assistant", ai_message))

        return ai_message, False, True

    def get_state_for_planning(self):
        """Get state object for running planner in worker thread."""
        return {
            "research_question": self.initial_question,
            "research_context": self.refined_scope or self.detected_scope,
            "research_plan": None,
            "approval_decision": None,
            "ledger_schema": None,
            "ledger_rows": [],
            "memo_block": None,
            "excel_path": None,
            "current_phase": "init",
            "iteration_count": 0,
        }

    def set_research_plan(self, state):
        """Called after planner completes in worker thread."""
        self.research_plan = state["research_plan"]
        self.questions_to_review = list(self.research_plan.sub_questions)
        self.conversation_state = ConversationState.PLAN_REVIEW

    def format_plan_message(self):
        """Format the plan for display after it's been created."""
        plan_text = f"Research Plan: {self.research_plan.research_title}\n\n"
        plan_text += f"I've broken this down into {len(self.research_plan.sub_questions)} sub-questions:\n\n"

        for i, sq in enumerate(self.research_plan.sub_questions, 1):
            plan_text += f"{i}. {sq.question}\n"

        plan_text += f"\n\nShould we review each question in detail to make sure they're exactly what you need?"

        self.conversation_history.append(("assistant", plan_text))
        return plan_text

    def _handle_plan_review(self, user_message):
        """Handle user's response to the overall plan."""
        user_lower = user_message.lower()

        if any(word in user_lower for word in ["yes", "sure", "ok", "yeah", "proceed", "review"]):
            # User wants to review questions
            self.conversation_state = ConversationState.QUESTION_REVIEW
            self.current_question_index = 0
            return self._present_next_question()

        elif any(word in user_lower for word in ["no", "skip", "looks good", "start", "begin"]):
            # User is happy, start research
            self.conversation_state = ConversationState.RESEARCH_RUNNING
            ai_message = (
                "Great! I'll start the research now. This will take 3-5 minutes.\n\n"
                "I'll search 50 high-quality sources and extract evidence for each question."
            )
            self.conversation_history.append(("assistant", ai_message))
            return ai_message, False, False  # No input, research starts

        else:
            # User has feedback - engage in conversation
            ai_message = (
                f"I understand you have some thoughts. Let me address that:\n\n"
                f"Based on what you said, would you like me to:\n"
                f"1. Review and refine each question with you?\n"
                f"2. Revise the entire plan based on your feedback?\n"
                f"3. Start research with the current plan?\n\n"
                f"What would work best for you?"
            )
            self.conversation_history.append(("assistant", ai_message))
            return ai_message, True, True

    def _present_next_question(self):
        """Present the next question for review."""
        if self.current_question_index >= len(self.questions_to_review):
            # All questions reviewed
            self.conversation_state = ConversationState.RESEARCH_RUNNING
            ai_message = (
                f"Perfect! We've reviewed all {len(self.approved_questions)} sub-questions.\n\n"
                f"I'll now start the research. This will take 3-5 minutes to search and analyze sources."
            )
            self.conversation_history.append(("assistant", ai_message))
            return ai_message, False, False  # Start research

        sq = self.questions_to_review[self.current_question_index]

        ai_message = (
            f"📋 Question {self.current_question_index + 1} of {len(self.questions_to_review)}:\n\n"
            f"**Question:** {sq.question}\n\n"
            f"**Why this question:** {sq.rationale}\n\n"
            f"**What I expect to find:** {sq.expected_output if sq.expected_output else 'Various evidence and insights'}\n\n"
            f"What do you think? You can:\n"
            f"• Say 'good' or 'approve' to keep it\n"
            f"• Suggest changes or improvements\n"
            f"• Say 'skip' to remove it\n"
            f"• Ask me to explain more"
        )

        self.conversation_history.append(("assistant", ai_message))
        return ai_message, True, True

    def _handle_question_review(self, user_message):
        """Handle user's feedback on current question."""
        user_lower = user_message.lower()
        current_q = self.questions_to_review[self.current_question_index]

        if any(word in user_lower for word in ["good", "approve", "ok", "yes", "looks good", "fine"]):
            # Approve current question
            self.approved_questions.append(current_q)
            self.current_question_index += 1

            ai_message = f"✓ Great! Question {self.current_question_index} approved.\n\n"
            self.conversation_history.append(("assistant", ai_message))

            # Present next question immediately
            next_msg, needs_input, continues = self._present_next_question()
            return ai_message + next_msg, needs_input, continues

        elif any(word in user_lower for word in ["skip", "remove", "delete", "no"]):
            # Skip current question
            self.current_question_index += 1

            ai_message = f"✗ Understood, I'll skip question {self.current_question_index}.\n\n"
            self.conversation_history.append(("assistant", ai_message))

            next_msg, needs_input, continues = self._present_next_question()
            return ai_message + next_msg, needs_input, continues

        else:
            # User wants to modify - use Claude to refine
            prompt = f"""The user wants to refine this research question:

Current question: {current_q.question}
Rationale: {current_q.rationale}
Expected output: {current_q.expected_output}

User's feedback: {user_message}

Based on their feedback, propose a refined version of the question. Return JSON:
{{
    "refined_question": "improved question text",
    "explanation": "brief explanation of what you changed and why"
}}"""

            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            text = response.content[0].text
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()
            elif "```" in text:
                json_start = text.find("```") + 3
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()

            try:
                refinement = json.loads(text)

                # Update the question
                current_q.question = refinement["refined_question"]

                ai_message = (
                    f"I've refined the question based on your feedback:\n\n"
                    f"**New question:** {refinement['refined_question']}\n\n"
                    f"**Why:** {refinement['explanation']}\n\n"
                    f"Does this work better for you?"
                )

            except:
                ai_message = (
                    f"I understand you want to refine this question. Could you be more specific about what you'd like to change?\n\n"
                    f"For example:\n"
                    f"• Should it focus on a different aspect?\n"
                    f"• Should it be more specific or more broad?\n"
                    f"• Should it include/exclude certain elements?"
                )

            self.conversation_history.append(("assistant", ai_message))
            return ai_message, True, True  # Stay on same question


class ChatMessage(QFrame):
    """Individual chat message widget."""

    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)

        sender = QLabel("You" if is_user else "Research Assistant")
        sender.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        sender.setStyleSheet("color: #333;")
        layout.addWidget(sender)

        message = QLabel(text)
        message.setWordWrap(True)
        message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message.setFont(QFont("Segoe UI", 10))
        message.setStyleSheet("color: #000; padding: 5px 0;")
        layout.addWidget(message)

        self.setLayout(layout)

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


class MainWindow(QMainWindow):
    """Main application window with conversational interface."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Research Assistant - AI-Powered Research Tool")
        self.resize(1000, 700)

        self.output_dir = Path(__file__).parent / "outputs"
        self.output_dir.mkdir(exist_ok=True, parents=True)

        load_dotenv()
        if not self._check_api_keys():
            self._show_config_dialog()

        self._init_ui()

        self.conversation_manager = None
        self.client = None

    def _check_api_keys(self):
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        serper_key = os.getenv("SERPER_API_KEY")
        return bool(anthropic_key and serper_key)

    def _show_config_dialog(self):
        dialog = ConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            keys = dialog.get_keys()
            env_path = Path(__file__).parent / ".env"
            for key, value in keys.items():
                if value:
                    set_key(env_path, key, value)
                    os.environ[key] = value

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Chat area
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

        # Welcome message
        self._add_assistant_message(
            "Hello! I'm your Research Assistant powered by Claude Sonnet 4.5.\n\n"
            "I'll work with you as a thought partner to:\n"
            "• Understand exactly what you want to research\n"
            "• Create a detailed research plan together\n"
            "• Refine each question until it's perfect\n"
            "• Conduct comprehensive web research\n"
            "• Generate detailed analysis and executive summary\n\n"
            "We'll have a natural conversation - just like chatting with a colleague!\n\n"
            "What would you like to research?"
        )

    def _create_header(self):
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("QFrame { background-color: #2E75B6; }")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 10, 20, 10)

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
        self.input_field.setPlaceholderText("Type your message here...")
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
        message = ChatMessage(text, is_user=True)
        self.chat_layout.addWidget(message)
        self._scroll_to_bottom()

    def _add_assistant_message(self, text):
        message = ChatMessage(text, is_user=False)
        self.chat_layout.addWidget(message)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    def _send_message(self):
        user_message = self.input_field.toPlainText().strip()
        if not user_message:
            return

        if not self._check_api_keys():
            QMessageBox.warning(
                self,
                "API Keys Required",
                "Please configure your API keys in Settings."
            )
            self._show_config_dialog()
            return

        # Add user message
        self._add_user_message(user_message)
        self.input_field.clear()

        # Disable input while AI thinks
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)

        # Initialize conversation manager if this is first message
        if not self.conversation_manager:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            self.client = Anthropic(api_key=api_key)
            self.conversation_manager = ConversationManager(self.client, user_message)

            # Get first AI response
            QTimer.singleShot(100, self._process_conversation)
        else:
            # Continue conversation
            QTimer.singleShot(100, lambda: self._process_conversation(user_message))

    def _process_conversation(self, user_message=None):
        """Process the conversation and get AI's response."""
        try:
            ai_message, needs_input, continues = self.conversation_manager.get_next_message(user_message)

            # Check if planning is needed
            if ai_message == "NEED_PLANNING":
                self._run_planner()
                return

            # Show AI's message
            self._add_assistant_message(ai_message)

            if not continues:
                # Conversation ended - start research
                self._start_research()
            else:
                # Re-enable input for next user message
                self.input_field.setEnabled(True)
                self.send_button.setEnabled(True)
                self.input_field.setFocus()

        except Exception as e:
            import traceback
            error_msg = f"Error: {str(e)}\n\n{traceback.format_exc()}"
            self._add_assistant_message(f"❌ An error occurred:\n\n{error_msg}")
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)

    def _run_planner(self):
        """Run planner synchronously with processEvents to keep UI responsive."""
        # Show loading message
        self._add_assistant_message("⏳ Creating research plan (this may take 10-20 seconds)...")
        QApplication.processEvents()

        try:
            state = self.conversation_manager.get_state_for_planning()

            # Run planner synchronously
            updated_state = run_planner(state, self.client)

            # Update conversation manager with plan
            self.conversation_manager.set_research_plan(updated_state)
            plan_message = self.conversation_manager.format_plan_message()
            self._add_assistant_message(plan_message)

            # Re-enable input
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)
            self.input_field.setFocus()

        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self._add_assistant_message(f"❌ Error creating research plan:\n\n{error_msg}")
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)

    def _start_research(self):
        """Start the actual research process."""
        self._add_assistant_message("🔍 Starting research now...")

        # Build final state from conversation
        state: RAState = {
            "research_question": self.conversation_manager.initial_question,
            "research_context": self.conversation_manager.refined_scope or self.conversation_manager.detected_scope,
            "research_plan": self.conversation_manager.research_plan,
            "approval_decision": "approved",
            "ledger_schema": None,
            "ledger_rows": [],
            "memo_block": None,
            "excel_path": None,
            "current_phase": "plan_approved",
            "iteration_count": 0,
        }

        # Update with approved questions only
        if self.conversation_manager.approved_questions:
            state["research_plan"].sub_questions = self.conversation_manager.approved_questions

        # Run research in thread
        self._run_research_workflow(state)

    def _run_research_workflow(self, state):
        """Run the research workflow synchronously with UI updates."""
        serper_key = os.getenv("SERPER_API_KEY")
        if not serper_key:
            self._add_assistant_message("❌ SERPER_API_KEY not found in environment")
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)
            return

        try:
            # Schema
            state = run_schema_designer(state)
            QApplication.processEvents()

            # Research
            self._add_assistant_message("📊 Searching 50 web sources and extracting evidence...")
            QApplication.processEvents()

            state = run_researcher(state, serper_key, self.client)

            self._add_assistant_message(f"✓ Collected {len(state['ledger_rows'])} evidence rows!")
            QApplication.processEvents()

            # Evidence Excel
            evidence_excel_path = write_full_excel(state, self.output_dir)

            # Synthesis
            self._add_assistant_message("🧠 Synthesizing findings for each question...")
            QApplication.processEvents()

            state = run_synthesizer(state, self.client)
            self._add_assistant_message("✓ Synthesis complete!")
            QApplication.processEvents()

            # Memo
            self._add_assistant_message("📝 Generating executive memo...")
            QApplication.processEvents()

            state = run_memo_generator(state, self.client)
            self._add_assistant_message("✓ Memo generated!")
            QApplication.processEvents()

            # Final Excel
            self._add_assistant_message("📊 Creating final Excel report...")
            QApplication.processEvents()

            final_excel_path = write_milestone3_excel(state, evidence_excel_path, self.output_dir)

            # Success message
            self._add_assistant_message(
                f"✅ Research complete!\n\n"
                f"📊 Excel file: {final_excel_path}\n\n"
                f"The report has 3 tabs:\n"
                f"1. MEMO - Executive summary\n"
                f"2. SYNTHESIS - Detailed analysis\n"
                f"3. RAW DATA - All evidence with sources\n\n"
                f"Feel free to start a new research question anytime!"
            )

            # Re-enable input
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)

            # Reset conversation
            self.conversation_manager = None

        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self._add_assistant_message(f"❌ Research failed:\n\n{error_msg}")
            self.input_field.setEnabled(True)
            self.send_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
