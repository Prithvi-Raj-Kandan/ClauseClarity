from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from typing import List

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def build_grounded_answer(question: str, retrieved_contexts: List[str], analysis_summary: str) -> str:
	if not GOOGLE_API_KEY:
		raise ValueError("GOOGLE_API_KEY is required for chat generation.")

	llm = ChatGoogleGenerativeAI(
		model="gemini-2.5-flash",
		temperature=0.2,
		google_api_key=GOOGLE_API_KEY,
	)

	context_blob = "\n\n".join(retrieved_contexts) if retrieved_contexts else "No context retrieved."
	prompt = (
		"You are ClauseClarify, a legal assistant for rental agreements. "
		"Answer only using the supplied context. If the answer is not in context, say so clearly.\n\n"
		f"Analysis Summary:\n{analysis_summary}\n\n"
		f"Retrieved Context:\n{context_blob}\n\n"
		f"Question: {question}\n"
		"Return a concise answer and include which source (base or uploaded) supports it."
	)
	response = llm.invoke(prompt)
	return getattr(response, "content", str(response))




