from datetime import datetime
from typing import Dict, List, Optional
import logging
import textwrap

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from messenger.app.schemas.models import MeetingReadinessOutput
from messenger.app.src.tools import (
    lookup_places,
    get_place_details
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from messenger.app.schemas.models import ConversationState
from .prompts import (
    get_dating_agent_prompt,
    get_readiness_prompt,
    get_refinement_prompt,
    get_task_prompt
)
from shared.models import MatchProfile, Message
from shared.exceptions import MatchReadyException

from sqlalchemy import select
from messenger.app.db.models import Chat, MessageDB
from messenger.app.db.database import SessionLocal, init_db


logger = logging.getLogger(__name__)


class DatingAgent:
    """
    An AI-powered dating agent that manages conversations and evaluates
    meeting readiness between users.
    """

    def __init__(self, personal_profile: MatchProfile, verbose: bool = False):
        """
        Initialize the dating agent with a personal profile.

        Args:
            personal_profile (MatchProfile): The profile of the user being represented
        """
        self.personal_profile = personal_profile
        self.llm = ChatOpenAI(temperature=0.7)
        self.refinement_llm = ChatOpenAI(temperature=0.7)

        self.conversations: Dict[str, ConversationState] = {}
        self.verbose = verbose
        self._initialize_agent()

    async def __aenter__(self):
        # init DB
        init_db()
        # Load existing conversations from DB into self.conversations
        with SessionLocal() as db:
            stmt = select(Chat)
            chats = db.execute(stmt)
            for chat in chats.scalars():
                self.conversations[chat.match_id] = chat.to_conversation_state()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Save all conversations to DB
        with SessionLocal() as db:
            for match_id, state in self.conversations.items():
                # Create or update chat
                stmt = select(Chat).where(Chat.match_id == match_id)
                chat = db.execute(stmt)
                chat = chat.scalar_one_or_none()

                if not chat:
                    chat = Chat(match_id=match_id)

                # Update chat from state
                chat.profile = state.profile.model_dump()
                chat.ready_to_meet = state.ready_to_meet
                chat.last_interaction = state.last_interaction
                chat.readiness_timestamp = state.readiness_timestamp

                db.add(chat)
                db.commit()

                # Add any new messages
                for msg in state.messages[len(chat.messages):]:
                    db_message = MessageDB(
                        chat_id=chat.id,
                        message=msg.message,
                        is_received=msg.is_received
                    )
                    db.add(db_message)

                db.commit()

    def _initialize_agent(self) -> None:
        """Initialize the agent with tools, prompts, and memory."""

        self.prompt = self._create_base_prompt()
        self.agent = create_tool_calling_agent(
            self.llm,
            self._get_tools(),
            self.prompt
        )

    def _create_base_prompt(self) -> ChatPromptTemplate:
        """Create the base prompt template for the agent."""
        system_content = get_dating_agent_prompt(self.personal_profile)
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_content),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def _get_tools(self) -> List[tool]:
        """Get the list of available tools for the agent."""
        return [
            lookup_places,
            get_place_details,
        ]

    async def _refine_response(self, response: str) -> Dict:
        """Refine the response to make it more natural and engaging."""
        try:
            refined = await self.refinement_llm.ainvoke([
                SystemMessage(content=get_refinement_prompt(self.personal_profile)),
                HumanMessage(content=f"Original message:\n{response}")
            ])
            return {'output': refined.content}
        except Exception as e:
            logger.warning(f"Refinement failed: {str(e)}")
            return response

    async def handle_message(
        self,
        match_id: str,
        profile: MatchProfile,
        message: Optional[Message] = None
    ) -> str:
        """
        Handle incoming or initial messages in a conversation.

        Args:
            match_id: Unique identifier for the match
            profile: Profile of the match
            message: Optional message to handle

        Returns:
            Generated response message

        Raises:
            Exception: If there's an error handling the message
        """
        try:
            state = self._get_or_create_conversation(match_id, profile)

            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self._get_tools(),
                memory=state.memory,
                handle_parsing_errors=True,
                verbose=True,
                return_intermediate_steps=True
            )

            self._update_conversation_state(state, message)

            if len(state.messages) > 1:
                readiness_result = await DatingAgent.check_meeting_readiness(
                    messages="\n".join(str(m) for m in state.messages),
                )
                logger.info(f"Meeting readiness check:\n{readiness_result}")

                if readiness_result.ready_to_meet:
                    state.ready_to_meet = True
                    raise MatchReadyException(
                        state
                    )

            input_text = self._format_input_text(profile, state, message)
            response = await self.agent_executor.ainvoke({
                "input": input_text,
            })
            refined_response = await self._refine_response(response["output"])
            logger.info(f"REFINED Response: {refined_response['output']}")
            self._update_state_with_response(state, refined_response)
            return refined_response["output"]

        except MatchReadyException as e:
            logger.info(str(e))
            raise

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            raise

    def _get_or_create_conversation(
        self,
        match_id: str,
        profile: MatchProfile
    ) -> ConversationState:
        """Get existing conversation state or create new one."""
        if match_id not in self.conversations:
            self.conversations[match_id] = ConversationState(profile=profile)
        state = self.conversations[match_id]

        if state.ready_to_meet:
            raise MatchReadyException(state)

        return state

    def _update_conversation_state(
        self,
        state: ConversationState,
        message: Optional[Message]
    ) -> None:
        """Update conversation state with new message."""
        if message:
            state.messages.append(Message(
                message=message.message,
                is_received=True
            ))
            state.memory.chat_memory.add_user_message(message.message)
        else:
            state.messages.append(Message(
                message="CONVERSATION_START",
                is_received=False
            ))
            state.memory.chat_memory.add_ai_message("CONVERSATION_START")

    def _format_input_text(
        self,
        profile: MatchProfile,
        state: ConversationState,
        message: Optional[Message]
    ) -> str:
        """Format input text for the agent."""
        profile_str = str(profile)
        history_str = "\n".join(str(m) for m in state.messages) if state.messages else "No previous messages."
        task_str = get_task_prompt(message is None)

        return "\n".join([
            "Profile:",
            textwrap.indent(profile_str, "  "),
            "",
            "Chat History:",
            textwrap.indent(history_str, "  "),
            "",
            "Task:",
            textwrap.indent(task_str, "  ")
        ])

    def _update_state_with_response(
        self,
        state: ConversationState,
        response: Dict
    ) -> None:
        """Update conversation state with the generated response."""
        state.messages.append(Message(
            message=response["output"],
            is_received=False
        ))
        state.memory.chat_memory.add_ai_message(response["output"])
        state.last_interaction = datetime.now()

    @staticmethod
    async def check_meeting_readiness(
        messages: str,
    ) -> MeetingReadinessOutput:
        """Evaluate if users are ready to meet based on conversation.

        Args:
            messages: The conversation history to analyze
            match_name: Name of the person we're chatting with

        Returns:
            Dict with ready_to_meet boolean and rationale
        """
        logger.info("Checking meeting readiness")

        base_llm = ChatOpenAI(temperature=0.0, model_name="gpt-4o")
        structured_llm = base_llm.with_structured_output(
            MeetingReadinessOutput,
            method="function_calling"
        )

        system_prompt = get_readiness_prompt()

        response = await structured_llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Conversation:\n{messages}")
        ])
        return response
