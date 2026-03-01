import os
import time
import jwt
import datetime
import webbrowser
from dotenv import load_dotenv

# Use vision_agents v0.3.8 syntax
from vision_agents.plugins.gemini import Realtime
from vision_agents.core.agents import Agent

# Load environment variables
load_dotenv()

def generate_and_save_config():
    """
    Creates a 24-hour JWT token for the user 'student_user'
    and writes it to a config.js file for the frontend to consume.
    """
    api_key = os.environ.get("STREAM_API_KEY", "")
    api_secret = os.environ.get("STREAM_API_SECRET", "")
    user_id = "student_user"
    
    # Create 24-hour JWT payload
    exp = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    payload = {
        "user_id": user_id,
        "exp": int(exp.timestamp())
    }
    
    try:
        # HS256 encoding for Stream tokens
        token = jwt.encode(payload, api_secret, algorithm="HS256")
        if isinstance(token, bytes):
            token = token.decode('utf-8')
    except Exception as e:
        print(f"Warning: Failed to generate Stream token. Did you set STREAM_API_SECRET? Error: {e}")
        token = ""

    # Generate config.js exactly as required
    with open("config.js", "w") as f:
        f.write(f"const STREAM_CONFIG = {{ apiKey: '{api_key}', token: '{token}' }};\n")
    print("[Backend] Generated config.js successfully.")

from vision_agents.plugins.getstream import Edge as StreamEdge

async def main():
    # Generate JS config
    generate_and_save_config()
    
    # Initialize the LLM inside the event loop
    llm = Realtime(fps=2, api_key=os.environ["GEMINI_API_KEY"])

    # Register youtube search tool
    @llm.register_function
    def search_youtube_tutorial(query: str) -> str:
        """Opens a YouTube search for coding tutorials using the webbrowser module."""
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Opened YouTube search for tutorial query: {query}"
    
    # Update Gemini key as requested by User
    os.environ["GEMINI_API_KEY"] = "AIzaSyDBmDD7ROr_NTCF-ARonzW4549kWdbXZXQ"
    os.environ["GOOGLE_API_KEY"] = "AIzaSyDBmDD7ROr_NTCF-ARonzW4549kWdbXZXQ"
    
    # Create the Stream Edge
    import getstream
    os.environ["STREAM_API_KEY"] = os.environ.get("STREAM_API_KEY", "")
    os.environ["STREAM_API_SECRET"] = os.environ.get("STREAM_API_SECRET", "")
    # `getstream` library expects STREAM_SECRET
    os.environ["STREAM_SECRET"] = os.environ["STREAM_API_SECRET"]
    
    edge = StreamEdge()
    from getstream.models import User
    
    # Monkey patch User to have name and image attributes as expected by Agent
    setattr(User, "name", "Saarthi")
    setattr(User, "image", "https://getstream.io/random_svg/?id=saarthi&name=Saarthi")
    
    # Create the Saarthi Agent (Fixing User arguments here)
    agent_user = User(id="saarthi")
    # Setting them on the instance to be safe
    agent_user.name = "Saarthi"
    agent_user.image = "https://getstream.io/random_svg/?id=saarthi&name=Saarthi"
    
    agent = Agent(edge=edge, llm=llm, agent_user=agent_user)
    
    # Connect
    print("[Backend] Saarthi connecting to 'ai-tutor-room'...")
    try:
        await agent.create_user() # Required to register agent_user context
        call = await agent.create_call("default", "ai-tutor-room")
        async with agent.join(call):
            await asyncio.Event().wait() # keep process alive indefinitely
    except Exception as e:
        print(f"Agent execution completed or encountered error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())