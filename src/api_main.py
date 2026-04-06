from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
import uuid
import uvicorn
from src.agent.graph import app as agent_app
from langchain_core.messages import HumanMessage, ToolMessage
from src.app import format_ai_response

app = FastAPI(title="Smart Travel Assistant API")

# Enable CORS (Allow all as requested)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    status: str  # "success", "need_input", "error"
    question: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main endpoint for chatting with the agent.
    Handles both normal conversation and human-in-the-loop responses.
    """
    try:
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get the current state to check for interrupts
        current_state = agent_app.get_state(config)
        
        if "human_review" in current_state.next:
            # The agent was waiting for human input. 
            # We treat the 'message' as the answer to the agent's question.
            last_msg = current_state.values["messages"][-1]
            if not isinstance(last_msg, ToolMessage) or "REQUESTED_USER_INPUT" not in last_msg.content:
                 raise HTTPException(status_code=400, detail="Unexpected state: Missing request_user tool call.")
            
            # Update the state with the user's answer
            agent_app.update_state(
                config,
                {"messages": [ToolMessage(tool_call_id=last_msg.tool_call_id, content=request.message)]}
            )
            # Resume execution (passing None to invoke tells it to continue from current state)
            final_output = agent_app.invoke(None, config)
        else:
            # Normal flow: Start a new interaction with the user's message
            input_data = {"messages": [HumanMessage(content=request.message)]}
            final_output = agent_app.invoke(input_data, config)
        
        # After processing, check if we hit another interrupt (AI asking another question)
        snapshot = agent_app.get_state(config)
        if "human_review" in snapshot.next:
            # AI called request_user again
            last_msg = snapshot.values["messages"][-1]
            question = last_msg.content.replace("REQUESTED_USER_INPUT: ", "")
            return ChatResponse(
                response="",
                thread_id=thread_id,
                status="need_input",
                question=question
            )
        
        # Success: Return the final AI message
        messages = snapshot.values.get("messages", [])
        if not messages:
            return ChatResponse(response="I'm sorry, I couldn't generate a response.", thread_id=thread_id, status="error")
            
        # Find the last AI message that isn't a tool call
        last_ai_msg = None
        for msg in reversed(messages):
            if msg.type == "ai" and not msg.tool_calls:
                last_ai_msg = msg
                break
        
        if not last_ai_msg:
             return ChatResponse(response="Processing...", thread_id=thread_id, status="success")

        return ChatResponse(
            response=format_ai_response(last_ai_msg.content),
            thread_id=thread_id,
            status="success"
        )

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
