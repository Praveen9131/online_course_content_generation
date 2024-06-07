import openai
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Load the environment variables from .env file
load_dotenv()

# Create an empty list to store the API keys
api_keys = []

# Define the prefix for the environment variable names
prefix = "OPENAI_API_KEY_"

# Loop through the environment variables and find all API keys
idx = 1
while True:
    env_var_name = f"{prefix}{idx}"
    api_key = os.getenv(env_var_name)

    # If the environment variable is not found, break the loop
    if api_key is None:
        break

    api_keys.append(api_key)
    idx += 1

# Set current index to get the api key on each request
current_api_idx = 0

model_name = "gpt-3.5-turbo-16k"
temperature = 0.6
default_max_tokens = 15000

def get_next_api_key():
    global current_api_idx
    api_key = api_keys[current_api_idx]
    current_api_idx = (current_api_idx + 1) % len(api_keys)
    return api_key

def parse_word_count(word_count):
    if isinstance(word_count, str) and 'to' in word_count:
        min_count, max_count = map(int, word_count.split('to'))
        return min_count, max_count
    count = int(word_count)
    return count, count

def is_complete_sentence(text):
    return text.endswith(('.', '!', '?'))

def complete_text(text):
    if not is_complete_sentence(text):
        complete_prompt = f"Complete the following text to ensure it ends with a complete sentence: {text}"
        final_response = openai.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "user", "content": complete_prompt}],
            max_tokens=50,
            temperature=temperature,
            api_key=get_next_api_key()
        )
        final_message = final_response["choices"][0]["message"]["content"].strip()
        text += " " + final_message
    return text

def adjust_word_count(text, min_word_count, max_word_count):
    words = text.split()
    current_word_count = len(words)
    
    if min_word_count <= current_word_count <= max_word_count:
        return text

    if current_word_count > max_word_count:
        summarize_prompt = f"Summarize the following text to fit within {max_word_count} words: {text}"
        summarize_response = openai.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "user", "content": summarize_prompt}],
            max_tokens=max_word_count * 5,
            temperature=temperature,
            api_key=get_next_api_key()
        )
        summarized_text = summarize_response["choices"][0]["message"]["content"].strip()
        return summarized_text
    
    if current_word_count < min_word_count:
        additional_words_needed = min_word_count - current_word_count
        expand_prompt = f"Expand the following text by adding approximately {additional_words_needed} words, ensuring it consists of complete sentences: {text}"
        expand_response = openai.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "user", "content": expand_prompt}],
            max_tokens=additional_words_needed * 5,
            temperature=temperature,
            api_key=get_next_api_key()
        )
        expanded_text = expand_response["choices"][0]["message"]["content"].strip()
        return expanded_text
    
    return text

def generate_article(title, word_count, info=None, conversation_history=None, prefixes=None):
    min_word_count, max_word_count = parse_word_count(word_count)
    prompt = f"""you are expert in AI online course assistant,
Write a detailed section titled '{title}' with approximately {max_word_count} words. Ensure the content is well-organized, informative, and consists of complete sentences. Avoid incomplete sentences.

{info if info else ""}

The structure of your response should include the following:

1) **Title of the course**: Provide the course title

2) **Requirements or prerequisites**: Provide any requirements or prerequisites needed to join the course

3) **Description**: Provide a detailed description of the course, including its objectives, target audience, and breakdown of its modules

4) **What you'll learn**: Provide a comprehensive list of what students will learn from the course

5) **Who this course is for**: Provide information about the target audience for the course

**Keywords**:
[List relevant keywords for the course]

Remember, the goal is to create a comprehensive and self-contained learning resource with the level of detail and instructional quality that one would expect from an expert instructor. Your output should be formatted using Markdown for clarity and easy integration into course platforms.
"""

    if prefixes:
        all_prefix = '\n'.join(prefixes)
        prompt = f"{all_prefix}\n\n{prompt}"
    
    response = None
    retries = 3
    generated_text = ""

    while retries > 0:
        if conversation_history:
            messages = conversation_history.copy()
            messages.append({"role": "user", "content": prompt})
        else:
            messages = [{"role": "user", "content": prompt}]

        try:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=messages,
                max_tokens=default_max_tokens,
                temperature=temperature,
                api_key=get_next_api_key()
            )
        except Exception as e:
            retries -= 1
            continue

        message = response["choices"][0]["message"]
        generated_text = message["content"].strip()
        
        words = generated_text.split()
        if len(words) >= min_word_count:
            break

    generated_text = complete_text(generated_text)
    generated_text = adjust_word_count(generated_text, min_word_count, max_word_count)
    
    # Ensure final word count is within the specified range
    while not (min_word_count <= len(generated_text.split()) <= max_word_count):
        generated_text = adjust_word_count(generated_text, min_word_count, max_word_count)
        generated_text = complete_text(generated_text)

    return generated_text

def process_requests(sections, prefixes=None, save_conversation_history=False):
    conversation_history = None
    results = []

    for section in sections:
        title = section.title.strip()
        word_count = section.word_count
        info = section.info if hasattr(section, 'info') else None
        response = generate_article(title, word_count, info, conversation_history, prefixes)
        
        results.append({"title": title, "content": response, "word_count": len(response.split())})

        if save_conversation_history:
            if conversation_history:
                conversation_history.append({"role": "assistant", "content": response})
            else:
                conversation_history = [{"role": "assistant", "content": response}]
            conversation_history[-1]["content"] += "\n"

    return results

class Section(BaseModel):
    title: str
    word_count: str
    info: Optional[str] = None

class SectionInput(BaseModel):
    sections: List[Section]
    prefixes: Optional[List[str]] = None
    save_conversation_history: Optional[bool] = False

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-article")
async def generate_article_endpoint(input: SectionInput):
    try:
        result = process_requests(input.sections, input.prefixes, input.save_conversation_history)
        return JSONResponse(content={"result": result}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
