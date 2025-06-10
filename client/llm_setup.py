from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, ModelSettings, RunConfig # type: ignore
from dotenv import load_dotenv
import os

load_dotenv()


gemini_api_key = os.getenv("GEMINI_API_KEY")

# Check if the API key is present; if not, raise an error
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")


external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model1 = OpenAIChatCompletionsModel(
    model="gemini-1.5-flash",
    openai_client=external_client
)

# Export the model settings separately for use in Agent configuration
model_settings = ModelSettings(
    tool_choice="required",  # Force the model to use tools
    # temperature=0.7,  # Add some creativity but keep responses focused
    # max_tokens=1000,  # Allow for detailed responses
    # top_p=0.95,  # Maintain good response diversity
)

# config = RunConfig(
#     model=model,
#     model_provider=external_client,
#     tracing_disabled=True
# )
