from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def create_vector_store(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", api_key=GOOGLE_API_KEY)
    vector_store = Chroma.from_texts(chunks, embedding=embeddings)
    return vector_store