import os
import json
import openai
from datetime import datetime
from functions import *
from functions_info import *

with open('config/config.json') as f:
    configs = json.load(f)
OPENAI_API_KEY = configs['OPENAI_API_KEY']
GPT_MODEL = configs["GPT_MODEL"]
MEMORY_DIR = "memory"
openai.api_key = OPENAI_API_KEY


class Agent:
    """ The agent for planning, executing and memory management """
    
    def __init__(self, name: str, functions_info: list, functions: dict) -> None:
        self.name = name
        self.memory = []
        self.functions_info = functions_info
        self.functions = functions
    
    def generate_response(self, messages: list):
        """
            Get the response from the GPT model
            
        params:
            - messages (list): A list of message for prompting the GPT model
        
        return:
            response (openai chat completion object): An object of response from the GPT model
        """
        
        response_msg = None
        
        while True:
            response = openai.ChatCompletion.create(
                model=GPT_MODEL,
                messages=messages,
                functions=self.functions_info,
            )
            
            response_msg = response["choices"][0]["message"]
            # print(response_msg)
            finish_reason = response["choices"][0]["finish_reason"]
            messages.append(response_msg)
            
            if finish_reason == "stop":
                break
            
            if response_msg.get("function_call"):
                function_name = response_msg["function_call"]["name"]
                function_to_call = self.functions[function_name]
                function_args = json.loads(response_msg["function_call"]["arguments"])
                function_response = function_to_call(**function_args)
        
            # Convert the result of the function response to string Class if it is not a string object
            if not isinstance(function_response, str):
                function_response = str(function_response)
                assert isinstance(function_response, str) is True, "The response of the function must be a string."
            
            # Add all messages to the historical memory
            messages.append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response
                }
            )
            
        return response_msg

    def update_memory(self, response_obj):
        """
            Update the memeory for storing the conversational contents
        
        params:
            - response_obj (str): An object of response from the GPT model
        """
        
        if response_obj is not None:
            response = json.loads(response_obj)
            memory_format = {response["role"]: response["content"]}
            self.memory.append(memory_format)
        else:
            print("The response is None.")
    
    def save_memory(self):
        """
            Save the memory for later reviewing or reusage
        """
        
        if not os.path.exists(MEMORY_DIR):
            os.makedirs(MEMORY_DIR)
        
        memory_file_name = "memory_" + self.name + datetime.now() + ".json"
        memory_file_path = os.path.join(MEMORY_DIR, memory_file_name)
        with open(memory_file_path, "w") as f:
            json.dump(self.memory, f)
    
    def read_memory(self, memory_file_path: str):
        """
            Read a memory json file from a given path
            
        params:
            - memory_file_path (str): The file path for reading the memory file
        """
        
        try:
            with open(memory_file_path, "r") as f:
                self.memory = json.load(f)
        except FileNotFoundError as e:
            print("Memory file not found")
            

if __name__ == "__main__":
    agent = Agent("Haoxuan", functions, {"get_current_weather" : get_current_weather})
    print(
        agent.generate_response([{"role": "user", "content": "what is the whether like in London today?"}])
    )
