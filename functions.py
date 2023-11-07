import json
import requests


CONFIG_FILE = "config/config.json"
OPENWHETHERREPORT_API_KEY = json.load(open(CONFIG_FILE))["openweathermap_api_key"]


def get_current_weather(location: str):
    """ Get the current weather in a given location using openwhethermap api """
    url = "https://api.openweathermap.org/data/2.5/weather?q=" + location + "&appid=" + OPENWHETHERREPORT_API_KEY + "&units=metric"
    response = requests.get(url)
    return response.content.decode()


def save_to_file(name: str, content: str):
    """ Save content to a file with the given name """
    with open(name, 'w') as file:
        file.write(content)
    return f"Content saved to file '{name}'"