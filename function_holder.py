import os, re
import openai
import boto3
import json
import tiktoken
from botocore.exceptions import NoCredentialsError
import requests
from typing import Tuple

# Set your OpenAI API key
openai.api_key = os.environ['OPENAI_API_KEY']

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

# def generate_content(prompt):
#     response = openai.Completion.create(
#         engine="text-davinci-003",
#         prompt=prompt,
#         max_tokens=150,
#         n=1,
#         stop=None,
#         temperature=0.8,
#     )
#     text = response.choices[0].text.strip()
#     completion_tokens = response.usage.completion_tokens
#     prompt_tokens = response.usage.prompt_tokens
#     total_tokens = response.usage.total_tokens
#     return text, completion_tokens, prompt_tokens, total_tokens

def generate_content(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    max_tokens=150,
    n=1,
    stop=None,
    temperature=0.8,
    )
    text = response['choices'][0]['message']['content'].strip()
    completion_tokens = response['usage']['completion_tokens']
    prompt_tokens = response['usage']['prompt_tokens']
    total_tokens = response['usage']['total_tokens']
    return text, completion_tokens, prompt_tokens, total_tokens

# Add a function to generate images using DALL-E
def generate_image(prompt, n=1, size="256x256"):
    response = openai.Image.create(
        prompt=prompt,
        n=n,
        size=size
    )
    return response['data'][0]['url']

def post_process_dialogue(dialogue):
    # Parse the JSON string
    dialogue_json = json.loads(dialogue)
    
    # Retrieve the dialogue from the JSON object
    dialogue = dialogue_json.get("dialogue", "")
        
    return dialogue.strip()

def extract_character_names(template):
    character_names = set()
    lines = template.split("\n")
    for line in lines:
        if "]: " in line:
            character_name = line.split("]: ")[0].strip()[1:]
            character_names.add(character_name)
    return list(character_names)

s3 = boto3.client('s3', region_name='us-east-1')

def save_image_to_s3(url, user_id, show_title):
    response = requests.get(url)
    key = f"{user_id}/novels/{show_title}/cover.png"
    s3.put_object(
        Bucket='visualnovelimages',
        Key=key,
        Body=response.content,
        ContentType='image/png'
    )
    return key

# def save_image(url, file_path):
#     response = requests.get(url)

#     # Create the directories if they don't exist
#     os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
#     with open(file_path, "wb") as file:
#         file.write(response.content)

def analyze_sentiment_and_update_profile(dialogue, character_profile):
    sentiment_prompt = f"Identify the likes and dislikes expressed in the following dialogue: '{dialogue}'. Please list them in the format 'likes: item1, item2; dislikes: item3, item4'. If there are no likes or dislikes, just mention 'none'."
    
    sentiment_response = generate_content(sentiment_prompt)
    
    if "likes" in sentiment_response.lower():
        liked_items = re.search(r"likes: (.+?);", sentiment_response, re.IGNORECASE)
        if liked_items:
            liked_items = liked_items.group(1).strip().split(', ')
            if not any(re.match(r"none.*", item, re.IGNORECASE) for item in liked_items):
                character_profile["likes"].extend(liked_items)
    if "dislikes" in sentiment_response.lower():
        disliked_items = re.search(r"dislikes: (.+?)(;|$)", sentiment_response, re.IGNORECASE)
        if disliked_items:
            disliked_items = disliked_items.group(1).strip().split(', ')
            if not any(re.match(r"none.*", item, re.IGNORECASE) for item in disliked_items):
                character_profile["dislikes"].extend(disliked_items)