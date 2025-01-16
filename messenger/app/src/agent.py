from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_community.tools import tool
from langchain_openai import ChatOpenAI
from typing import Dict, List
from datetime import datetime
import logging
from shared.models import MatchProfile, Message
import textwrap
from pydantic import BaseModel, Field
from typing import Optional


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationState(BaseModel):
    """Tracks the state of the conversation"""
    profile: MatchProfile
    messages: List[Message] = []
    meeting_readiness_score: float = 0.0
    engagement_score: float = 0.0
    last_interaction: datetime = datetime.now()


class MeetingReadinessOutput(BaseModel):
    score: float = Field(
        ..., ge=0, le=1, description="Readiness between 0.0 and 1.0"
    )
    rationale: Optional[str] = Field(
        None, description="Reasoning behind readiness score"
    )


class DatingAgent:
    def __init__(self, personal_profile: MatchProfile):
        self.personal_profile = personal_profile
        self.llm = ChatOpenAI(temperature=0.7)

        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
        )

        # Define tools
        self.tools = [
            self.lookup_places,
            self.check_meeting_readiness,
            self.send_notification
        ]

        base_system_message = SystemMessage(
            content=f"""
        You are acting as a person on a dating app with the following profile:

        Your Profile:
        {self.personal_profile.model_dump()}


        First, analyze the profile considering:
        1. Key personality traits from their bio and interests
        2. Potential conversation hooks and shared interests
        3. Their preferences and lifestyle choices
        4. Location and logistics for potential meetups
        5. The type of relationship they're looking for

        Then, based on this analysis:
        - For opening messages: Create a personalized, engaging opener that refers to specific details from their profile
        - For replies: Maintain conversation flow while building rapport and showing genuine interest

        Guidelines:
        - Keep messages concise, natural and as human-like as possible
        - Include a question or hook to encourage response
        - Match their communication style
        - If they mention meeting up, use the lookup_places tool to suggest specific venues
        - If conversation progresses well, use check_meeting_readiness to evaluate timing
        - If meeting readiness is high, send a notification using send_notification
        - Use emoji's to express emotions and add personality
        """
        )

        self.prompt = ChatPromptTemplate.from_messages([
            base_system_message,
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            input_key="input",
            return_messages=True
        )

        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

        self.conversations: Dict[str, ConversationState] = {}

    @tool
    def lookup_places(location1: str, location2: str, venue_type: str) -> List[Dict]:
        """Look up places between two locations based on venue type (bar, restaurant, etc)"""
        # Integration with location service API would go here
        pass

    @tool
    async def check_meeting_readiness(messages: str) -> Dict:
        """
        Evaluate if users are ready to meet based on conversation,
        returning a JSON dictionary with 'score' and 'rationale'.
        """
        # 1) Wrap your LLM with structured output using function calling
        base_llm = ChatOpenAI(
            model="gpt-4o-mini-2024-07-18",
            temperature=0.0
        )
        structured_llm = base_llm.with_structured_output(
            MeetingReadinessOutput,
            method="function_calling"  # Specify function calling method
        )

        # 2) Construct system/user messages
        system_msg = SystemMessage(content="""
        You are a Meeting Readiness AI.
        Analyze the conversation and determine if the users are ready to meet.

        Guidelines for scoring:
        - 0.0-0.2: Very early stages, minimal interaction
        - 0.3-0.4: Basic rapport established
        - 0.5-0.6: Good conversation flow, shared interests identified
        - 0.7-0.8: Strong connection, mutual interest in meeting
        - 0.9-1.0: Clear readiness to meet, logistics being discussed
        """)
        user_msg = HumanMessage(content=f"Conversation:\n{messages}")

        # 3) Invoke the model
        response_obj: MeetingReadinessOutput = await structured_llm.ainvoke([system_msg, user_msg])

        # 4) Return as a dictionary
        return response_obj.model_dump()

    @tool
    def send_notification(
        personal_profile: MatchProfile,
        profile: MatchProfile,
        email: str

    ) -> bool:
        """Send email notification when meeting readiness is detected"""
        message = (
            f"Hey {personal_profile.name}, "
            f"your match:\n {profile} \nis ready to meet up! 🎉"
        )
        logger.warning(
            f"Sending notification to {email} with message:\n {message}"
        )

    async def handle_message(self, match_id: str, profile: MatchProfile, message: Message = None) -> str:
        try:
            # Initialize or get conversation state
            if match_id not in self.conversations:
                self.conversations[match_id] = ConversationState(profile=profile)

            state = self.conversations[match_id]

            # Update conversation state
            if message:
                state.messages.append(Message(
                    message=message.message,
                    is_received=True
                ))
            else:
                state.messages.append(Message(
                    message="START",
                    is_received=False
                ))

            profile_str = f"{profile}"
            if state.messages:
                history_str = "\n".join(str(m) for m in state.messages)
            else:
                history_str = "No previous messages."
            if message:
                task_str = "Please provide a direct reply to the last user message."
            else:
                task_str = "Generate an opening message."

            input_text = "\n".join([
                "Profile:",
                textwrap.indent(profile_str, "  "),
                "",
                "Chat History:",
                textwrap.indent(history_str, "  "),
                "",
                "Task:",
                textwrap.indent(task_str, "  ")
            ])

            # Generate response using agent
            response = await self.agent_executor.ainvoke({
                "input": input_text,
                "agent_scratchpad": ""
            })
            state.messages.append(Message(
                message=response["output"],
                is_received=False
            ))

            state.last_interaction = datetime.now()

            if len(state.messages) > 4:
                readiness_check = await self.check_meeting_readiness.ainvoke(history_str)
                state.meeting_readiness_score = readiness_check["score"]

                if state.meeting_readiness_score > 0.8:
                    await self.send_notification.ainvoke(
                        {
                            "personal_profile": self.personal_profile,
                            "profile": profile,
                            "email": "test@example.com"
                        }
                    )

            return response["output"]

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            raise
