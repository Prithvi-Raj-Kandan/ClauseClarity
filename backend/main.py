from fastapi import FastAPI

app = FastAPI()

@app.post("/upload")
async def upload():
    return {"message": "File uploaded successfully!"}


@app.post("/chat")
async def chat():
    return {"message": "Hello, this is the chat endpoint!"}


