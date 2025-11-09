import json
import os
from openai import OpenAI

def call_llm(model_client, model_name, message_history, tool_list):
    """Simple wrapper for OpenAI API calls without caching."""
    kwargs = {
        "model": model_name,
        "messages": message_history,
    }
    
    if tool_list:
        kwargs["tools"] = tool_list
    
    response = model_client.chat.completions.create(**kwargs)
    message = response.choices[0].message
    
    result = {"role": "assistant", "content": message.content}
    
    if hasattr(message, 'tool_calls') and message.tool_calls:
        result["tool_calls"] = []
        for tool_call in message.tool_calls:
            result["tool_calls"].append({
                "id": tool_call.id,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                },
                "type": "function"
            })
        result["content"] = None
    return result

API_KEY = os.environ["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"]
MODEL_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "nvidia/nemotron-nano-9b-v2"

client = OpenAI(base_url=MODEL_URL, api_key=API_KEY)

tools = []
memory = {"role": "user", "content": "Who was the first president?"}

llm_response = call_llm(client, MODEL_NAME, memory, tools)
memory.append(llm_response)

print(llm_response)