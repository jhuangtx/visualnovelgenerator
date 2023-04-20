import openai
import os
import requests
import re
import config
from function_holder import generate_content, generate_image, num_tokens_from_string, post_process_dialogue, extract_character_names, analyze_sentiment_and_update_profile, save_image

# change enable_image_generator to turn it on for characters
def generate_script(num_dialogues=6, uploaded_script_template=None, title_prompt=None,character_profiles=None, enable_image_generator=False):
    # Read the script template from the uploaded file or use the default file
    if uploaded_script_template:
        script_template = uploaded_script_template.read().decode("utf-8")
        
    # Read the script template from a separate file
    else:
        with open("script_template.txt", "r") as file:
            script_template = file.read()

    if character_profiles is None:
         character_profiles = {
    "Character 1": {"name": "Alice", "gender": "female", "age": 28, "personality": "outgoing", "build": "slim", "hair_style": "long", "hair_color": "brown", "eye_color": "green", "likes": [], "dislikes": []},
    "Character 2": {"name": "Bob", "gender": "male", "age": 32, "personality": "reserved", "build": "athletic", "hair_style": "short", "hair_color": "blonde", "eye_color": "blue", "likes": [], "dislikes": []},
    "Character 3": {"name": "Carol", "gender": "female", "age": 25, "personality": "quirky", "build": "curvy", "hair_style": "bob", "hair_color": "red", "eye_color": "brown", "likes": [], "dislikes": []},
    "Character 4": {"name": "Dave", "gender": "male", "age": 29, "personality": "confident", "build": "muscular", "hair_style": "shaved", "hair_color": "black", "eye_color": "hazel", "likes": [], "dislikes": []},
}
    else:
        for key, profile in character_profiles.items():
            character_profiles[key] = {**profile, "likes": [], "dislikes": []}

    if enable_image_generator:
        for character_name in character_profiles:
            try:
                image_prompt = f"{character_profiles[character_name]['gender']}, {character_profiles[character_name]['hair_style']} {character_profiles[character_name]['hair_color']} hair, {character_profiles[character_name]['eye_color']} eyes, {character_profiles[character_name]['build']} build and {character_profiles[character_name]['personality']} personality"
            except KeyError as e:
                print(f"KeyError: {e} not found for {character_name}")
                continue
            character_url = generate_image(image_prompt)
            character_urls[character_name] = character_url
    else:
        title_url = None
        character_urls = {character_name: None for character_name in character_profiles}

    # Extract character order from the script_template
    character_order = re.findall(r'\[(Character \d)\]', script_template)

    # Replace character placeholders with actual names in the script template
    for placeholder in set(character_order):
        script_template = script_template.replace(f"[{placeholder}]", character_profiles[placeholder]['name'])

    # Generate content for specific placeholders
    if title_prompt:
        show_title_prompt = title_prompt
    else:
        show_title_prompt = "Sun, Sand, and Friends"

    show_title = show_title_prompt

    # Replace placeholders with the generated content
    script_template = script_template.replace("[Show Title]", show_title)
    # script_template = script_template.replace("[Episode Title]", episode_title)

    # Generate content for dialogue and action scenes
    generated_dialogues = []
    previous_dialogue = None
    character_index = 0
    estimated_total_tokens=0
    actual_total_tokens=0
    for i in range(num_dialogues):
        character_name = character_order[character_index]
        character_profile = character_profiles[character_name]

        # Calculate the next character's index and profile
        next_character_index = (character_index + 1) % len(character_order)
        next_character_name = character_order[next_character_index]
        next_character_profile = character_profiles[next_character_name] # Add this line to get the next character's profile

        if i == 0:
            dialogue_prompt = f"Generate a short dialogue line for {character_name} in a coffeeshop where they share their interests, or ask a question about someones interests or life. Enclose dialog in []"
        elif i<num_dialogues - 1:
            print(f"Previous dialogue: {previous_dialogue}")

            dialogue_prompt = f"Generate a short dialogue line for {character_name} in a coffeeshop where they respond to the previous dialogue: \"{previous_dialogue}\". Enclose dialog in []"
        else:
            print(f"Previous dialogue: {previous_dialogue}")

            dialogue_prompt = f"Generate a short dialogue line for {character_name} in a coffeeshop where they respond to the previous dialogue: \"{previous_dialogue}\". This is the last line. Enclose dialog in []"
   
        # Add the following lines before generating the dialogue
        prompt_tokens = num_tokens_from_string(dialogue_prompt, "cl100k_base")
        print(f"Estimated Tokens used for prompt: {prompt_tokens}")

        # Generate the dialogue
        generate_dialogue, ct, pt, tt = generate_content(dialogue_prompt)
        dialogue_tokens = num_tokens_from_string(generate_dialogue, "cl100k_base")
        print(f"Estimated tokens from generated dialog: {dialogue_tokens}")

        generated_dialogue = post_process_dialogue(generate_dialogue)
        estimated_total_tokens += prompt_tokens + dialogue_tokens
        actual_total_tokens += pt + ct
        print(f"Tokens from json: {pt}, {ct}, {tt}")

        generated_dialogues.append((character_profile['name'], generated_dialogue))
        # analyze_sentiment_and_update_profile(generated_dialogue, character_profile)
        previous_dialogue = f"{character_profile['name']}: {generated_dialogue}"
        previous_character_name = character_profiles[character_name]['name']  # Add this line to store the previous character's name
        character_index = (character_index + 1) % len(character_order)

    # Replace dialogues in the script template
    for i, (character_name, dialogue) in enumerate(generated_dialogues, start=1):
        script_template = script_template.replace(f"[Dialogue {i}]", dialogue)

    print(script_template)
    print(character_profiles)
    print(character_urls)
    title_url = generate_image(show_title)  # Call the generate_image() function
    save_image(title_url, f"images/{show_title}/cover.png")
    print(f"Estimated total tokens used: {estimated_total_tokens}")
    print(f"Actual total tokens used: {actual_total_tokens}")
    return show_title, generated_dialogues

#generate_script()