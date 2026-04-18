"""
Chatbot Engine – role-aware AI assistant using Gemini + RAG.
Provides context-filtered responses based on the caller's role.
"""

import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# INITIALIZE GROQ CLIENT
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please add it to your .env file.")

client = Groq(api_key=GROQ_KEY)
DEFAULT_MODEL = "llama-3.3-70b-versatile" 

GREETINGS = ["hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon"]


def ask_ai(question: str, context: str,
           role: str = "Faculty",
           faculty_name: str | None = None,
           rag_context: str = "") -> str:
    """
    Query the AI with role-scoped context.

    Parameters
    ----------
    question      : user's natural-language query
    context       : stringified dataframe relevant to this role
    role          : Faculty | HOD | Principal | Admin
    faculty_name  : display name of logged-in faculty (for Faculty role)
    rag_context   : additional retrieved chunks from ChromaDB
    """
    # Basic Greeting Handler
    clean_q = question.lower().strip().strip("?!.")
    if clean_q in GREETINGS:
        return (f"Hello! I am your Professor Performance AI Agent. I'm here to help you navigate "
                f"performance data and provide role-specific insights for {role}. "
                "How can I assist you today?")

    role_instructions = {
        "Faculty":   (
            f"STRICT SECURITY PROTOCOL: You are assisting {faculty_name or 'a faculty member'}. "
            "Your access is RESTRICTED to ONLY this individual's data. "
            "NEVER mention, compare with, or acknowledge the existence of other faculty members. "
            "If asked about others, politely state that you can only discuss the logged-in user's profile."
        ),
        "HOD": (
            f"STRICT SECURITY PROTOCOL: You are the Head of Department for {faculty_name or 'the specific department'}. "
            "Your access is LIMITED to faculty within your assigned department. "
            "Do NOT provide data for other departments. Focus on local department improvements, "
            "identifying top/weak performers within this department only."
        ),
        "Principal": (
            "EXECUTIVE LEVEL ACCESS: You are helping the Principal review institutional performance. "
            "Provide high-level cross-department analytics, trends, and strategic insights across the entire institution."
        ),
        "Admin": (
            "ADMINISTRATIVE ACCESS: Assist with data management and system auditing."
        ),
    }

    system_prompt = f"""
You are a Professor Performance AI Agent. 
{role_instructions.get(role, '')}

Goal: Provide helpful, data-driven, and concise responses.

Faculty Performance Data for your Context:
{context}

{"Additional Insights from Knowledge Base:" if rag_context else ""}
{rag_context}

Instructions:
- If the question is a greeting, respond warmly and introduce yourself.
- Answer only based on the data provided; do not fabricate numbers.
- Be concise, professional, and constructive.
- Maintain strict data boundaries. If asked for data outside your role's scope, explain your restriction politely.
"""

    full_prompt = system_prompt + f"\n\nUser Question: {question}"

    max_retries = 3
    delay = 5
    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt,
                    }
                ],
                model=DEFAULT_MODEL,
                temperature=0.2,
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            if "rate_limit_exceeded" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                return f"❌ Groq API Error: {e}"