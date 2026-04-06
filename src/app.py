from src.agent.graph import app
from langchain_core.messages import HumanMessage, ToolMessage
import uuid

import re

def format_ai_response(content) -> str:
    """
    Converts AI markdown response to clean, readable plain text.
    - Strips bold/italic markers (**text**, *text*, __text__)
    - Converts markdown bullet points to dash bullets
    - Normalises multiple blank lines
    - Decodes escaped newlines \\n → actual newlines
    """
    if isinstance(content, list):
        # Gemini may return a list of content blocks
        texts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        content = " ".join(texts).strip()

    if not isinstance(content, str):
        content = str(content)

    # 1. Replace literal \n escape sequences with real newlines (common in JSON strings)
    content = content.replace("\\n", "\n")

    # 2. Remove bold/italic markdown: **text** → text, __text__ → text, *text* → text
    content = re.sub(r"\*{2}(.+?)\*{2}", r"\1", content, flags=re.DOTALL)
    content = re.sub(r"_{2}(.+?)_{2}", r"\1", content, flags=re.DOTALL)
    content = re.sub(r"\*(.+?)\*", r"\1", content, flags=re.DOTALL)

    # 3. Convert markdown bullet "* " or "•" at line start → "- "
    content = re.sub(r"^[ \t]*[\*•][ \t]+", "- ", content, flags=re.MULTILINE)

    # 4. Remove markdown headers (# Heading → Heading)
    content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)

    # 5. Collapse 3+ consecutive blank lines → max 2
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content.strip()


def run_chat():
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("--- Smart Travel Assistant (Production Ready) ---")
    print(f"Thread ID: {thread_id}")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        # Start or resume the graph
        current_state = app.get_state(config)
        
        # If we are not at an interrupt node, send user message
        input_data = None
        if not current_state.next:
            input_data = {"messages": [HumanMessage(content=user_input)]}
        
        # Stream events from the graph
        for event in app.stream(input_data, config, stream_mode="values"):
            if "messages" in event:
                last_msg = event["messages"][-1]
                # Only print if it's a final AI response (no tool calls)
                if last_msg.type == "ai" and not last_msg.tool_calls:
                    print(f"Agent: {format_ai_response(last_msg.content)}")

        # Check for interrupts specifically at the human_review node
        snapshot = app.get_state(config)
        while "human_review" in snapshot.next:
            # The last message before human_review should be the request_user tool message
            last_msg = snapshot.values["messages"][-1]
            if isinstance(last_msg, ToolMessage) and "REQUESTED_USER_INPUT" in last_msg.content:
                question = last_msg.content.replace("REQUESTED_USER_INPUT: ", "")
                user_answer = input(f"Agent [Question]: {question}\nYour answer: ")
                
                # Update state: Replace the placeholder tool output with actual user answer
                app.update_state(
                    config,
                    {"messages": [ToolMessage(tool_call_id=last_msg.tool_call_id, content=user_answer)]}
                )
                
                # Resume: Continue to agent node
                for event in app.stream(None, config, stream_mode="values"):
                    if "messages" in event:
                        last_msg = event["messages"][-1]
                        if last_msg.type == "ai" and not last_msg.tool_calls:
                            print(f"Agent: {format_ai_response(last_msg.content)}")
                
                snapshot = app.get_state(config)
            else:
                break

if __name__ == "__main__":
    run_chat()
