import base64
import sys
import os
import json
import asyncio
import time

from websockets.sync.client import connect

from typing import List, Dict, Any
from boilerplate_direct import DirectAPI

os.system('title w-AI-fu NovelAI LLM Direct')

# Model names mapping
MODEL_MAPPING = {
    "Kayra": "kayra-v1",
    "Clio": "clio-v1",  # Assuming API name based on convention
    "Euterpe": "euterpe-v1"  # Assuming API name based on convention
}

# Default model and settings
model_name: str = "Kayra"
api_model: str = MODEL_MAPPING[model_name]

async def handle(message: str, websocket, api: DirectAPI):
    split_message = message.split(' ');
    prefix = split_message[0]
    split_message.remove(prefix)
    payload = str.join(' ', split_message)
    match (prefix):
        case "GENERATE":
            await prepare_generate(payload, websocket, api)

async def prepare_generate(payload, websocket, api: DirectAPI):
    parsed = json.loads(payload)
    prompt = parsed["prompt"]
    llm_params = parsed["config"]
    response = ''
    try:
        response = "TEXT " + await generate(prompt, llm_params, api)
    except Exception as e:
        if (len(e.args) < 2):
            print(e, file=sys.stderr)
            response = "ERROR UNDEFINED Could not get informations about this error. Sorry."
        match e.args[1]:
            case 401:
                response = "ERROR WRONG_AUTH Missing or incorrect NovelAI mail and/or password."
            case 502:
                response = "ERROR RESPONSE_FAILURE API Responded with 502. Service may be down or temporary inaccessible."
            case _:
                print(e, file=sys.stderr)
                response = "ERROR UNDEFINED " + str(e.args[2])
    websocket.send(response)

async def generate(custom_prompt, parameters, api: DirectAPI)-> str:
    global api_model, model_name
    
    # Check if model has changed and update accordingly
    if parameters["model"] != model_name:
        model_name = parameters["model"]
        if model_name in MODEL_MAPPING:
            api_model = MODEL_MAPPING[model_name]
        else:
            # Default to Kayra if model not recognized
            api_model = "kayra-v1"
            
    # Prepare parameters for direct API call
    generation_params = {
        "max_length": parameters["max_output_length"],
        "temperature": parameters["temperature"],
        "repetition_penalty": parameters["repetition_penalty"],
        "length_penalty": parameters["length_penalty"],
        "stop_sequences": [[85], [198]]  # Default stop sequences from original code
    }
    
    # Call the API directly to generate text
    result = await api.generate_text(
        prompt=custom_prompt, 
        model=api_model,
        **generation_params
    )
    
    # Extract generated text from the response
    if "output" in result:
        return result["output"]
    else:
        raise Exception("TextGeneration", 500, "No output received from API")

async def main():
    with connect("ws://localhost:8765") as websocket:
        try:
            async with DirectAPI() as api:
                while(True):
                    await handle(websocket.recv(), websocket, api)
        except Exception as e:
            if len(e.args) > 1 and e.args[1] == 401:
                while(True):
                    websocket.recv()
                    websocket.send("ERROR WRONG_AUTH Missing or incorrect NovelAI mail and/or password.")
            else:
                websocket.send("ERROR UNDEFINED " + str(e.args))

if __name__ == '__main__':
    asyncio.run(main())