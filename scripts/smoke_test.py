"""Smoke test: one model call, traced in langsmi. """

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

model = init_chat_model(f"google_genai:{os.environ['MODEL_NAME']}")
reply = model.invoke("Reply with exactly one word: Ready")
print(reply.content)