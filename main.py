from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, model_validator
from agent.agent import agent
from scraper.bill_scraper_bot import get_hesco_bill
import uuid
import uvicorn
import os

app = FastAPI(title="BillWala")

# Each thread_id maps to fetched bill data + whether the agent has seen it yet.
sessions: dict[str, dict] = {}
BASE_DIR = Path(__file__).resolve().parent

class FetchBillRequest(BaseModel):
    consumer_id: str = ""
    reference_no: str = ""

    @model_validator(mode="after")
    def exactly_one_id(self):
        has_consumer = bool(self.consumer_id.strip())
        has_reference = bool(self.reference_no.strip())
        if has_consumer == has_reference:
            raise ValueError("Provide either consumer_id or reference_no, not both.")
        return self

class FetchBillResponse(BaseModel):
    status: int
    data: str | None = None
    thread_id: str | None = None

class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None

class ChatResponse(BaseModel):
    reply: str
    thread_id: str

@app.get("/")
async def home():
    """BillWala frontend."""
    return FileResponse(BASE_DIR / "template" / "index.html")


@app.post("/api/fetch-bill", response_model=FetchBillResponse)
async def fetch_bill(body: FetchBillRequest):
    """Fetch bill from HESCO portal and start a new chat session."""
    if body.consumer_id.strip():
        params = {"appno": body.consumer_id.strip()}
    else:
        params = {"refno": body.reference_no.strip()}

    result = get_hesco_bill(params=params)
    status = result.get("status", 3)

    if status != 0:
        return FetchBillResponse(status=status, data=None, thread_id=None)

    thread_id = str(uuid.uuid4())
    sessions[thread_id] = {
        "bill": result["data"],
        "agent_started": False,
    }

    return FetchBillResponse(status=0, data=result["data"], thread_id=thread_id)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """Send a user message to the bill assistant."""
    if not body.thread_id or body.thread_id not in sessions:
        return ChatResponse(
            reply="Session expired. Please fetch your bill again.",
            thread_id=body.thread_id or "",
        )

    session = sessions[body.thread_id]
    message = body.message.strip()

    if not session["agent_started"]:
        message = (
            f"The following is the user's HESCO electricity bill (it may contain Urdu labels - ignore them for language detection and respond in English by default unless user ask in other language):\n\n"
            f"{session['bill']}\n\n"
            f"User question: {message}"
        )
        session["agent_started"] = True

    result = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {"thread_id": body.thread_id}},
    )

    reply = result["messages"][-1].content
    return ChatResponse(reply=reply, thread_id=body.thread_id)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
