functions = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
            },
            "required": ["location"],
        },
    },
    
    {
        "name": "save_to_file",
        "description": "Save a given content to a file",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the file",
                },
                "content": {
                    "type": "string",
                    "description": "The content to be saved in the file",
                },
            },
            "required": ["name", "content"],
        },
    },
]