import requests
import re
import json
from function_holder import generate_content, generate_image, num_tokens_from_string, post_process_dialogue, extract_character_names, analyze_sentiment_and_update_profile, save_image_to_s3

# change enable_image_generator to turn it on for characters
def generate_script(num_dialogues=6, uploaded_script_template=None, title_prompt=None,character_profiles=None, enable_image_generator=False, user_id=None):

    print("generate_script is being executed")

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

    show_title = show_title_prompt.title()

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
        #     dialogue_prompt = f"Generate a short dialogue line for {character_name} in a coffeeshop where they share their interests, or ask a question about someones interests or life. Enclose dialog in []"
        # elif i<num_dialogues - 1:
        #     dialogue_prompt = f"Generate a short dialogue line for {character_name} in a coffeeshop where they respond to the previous dialogue: \"{previous_dialogue}\". Enclose dialog in []"
        # else:
        #     dialogue_prompt = f"Generate a short dialogue line for {character_name} in a coffeeshop where they respond to the previous dialogue: \"{previous_dialogue}\". This is the last line. Enclose dialog in []"
            dialogue_prompt = f"""Context: 1) You are a character: {character_profile['name']}, in a short show titled: {show_title} 
            
                Rules:
                1) Do not explicitly mention the title of the show in the dialogue.

                Instruction:
                1) Generate an opening dialogue line where you talk about your interests, life, or ask a question to another character (relevant to the show title) in json format.
                2) Format: {{"Index": "{i}", "name": "{character_profile['name']}", "dialogue": "[Dialogue line here]"}}
                3) Review your dialogue to ensure it fits within the rules and if not, edit it to follow them.
                """
        elif i < num_dialogues - 1:
            dialogue_prompt = f"""Context: 1) You are a character: {character_profile['name']}, in a short show titled: {show_title} 
                2) Previous dialogue: {previous_dialogue}
                3) Previous speaker: {previous_character_name}
                4) Next speaker: {next_character_profile['name']} 

                Rules: 
                1) If the previous speaker asked you a question, respond to them but do not respond with a follow-up question if they are not the next speaker.
                2) To continue the conversation, ask another query or change the topic in a natural and conversational way (relevant to the show title). 
                3) If the dialogue contains another query, make sure to direct it to the "Next Speaker" and explicitly mention their name.
                4) Do not explicitly mention the title of the show in the dialogue.

                Instruction: 
                1) Analyze the previous dialogue. 
                2) Generate a responsive dialogue in json format.
                3) Format: {{"Index": "{i}", "name": "{character_profile['name']}", "dialogue": "[Dialogue line here]"}}
                4) Review your dialogue to ensure it fits within the rules and if not, edit it to follow them.
                """
        else:
            dialogue_prompt = f"""Context: 
                1) You are a character: {character_profile['name']}, in a short show titled: {show_title} 
                2) Previous Dialogue: {previous_dialogue}
                3) Previous Speaker: {previous_character_name}
                
                Rules: 
                1) If the previous speaker asked you a question, you can answer it or provide a closing statement or remark to wrap up the conversation (relevant to the show title).
                2) Do not explicitly mention the title of the show in the dialogue.

                Instruction: 
                1) Analyze the previous dialogue. 
                2) Generate a responsive last dialogue line in json format. 
                3) Format: {{"Index": "{i}", "name": "{character_profile['name']}", "dialogue": "[Dialogue line here]"}}
                4) Review your dialogue to ensure it fits within the rules and if not, edit it to follow them.
                """

        # Add the following lines before generating the dialogue
        prompt_tokens = num_tokens_from_string(dialogue_prompt, "cl100k_base")

        # Generate the dialogue
        generated_dialogue_str, ct, pt, tt = generate_content(dialogue_prompt)
        generated_dialogue = json.loads(generated_dialogue_str)
        # dialogue_tokens = num_tokens_from_string(generated_dialogue, "cl100k_base")

        actual_total_tokens += pt + ct

        print({character_profile['name']})
        print(f"Dialogue: {generated_dialogue}")
        print(f"Only dialogue: {generated_dialogue['dialogue']}")
        print(f"ct: {ct}")
        print(f"pt: {pt}")
        print(f"tt: {tt}")

        generated_dialogues.append(generated_dialogue)
        # analyze_sentiment_and_update_profile(generated_dialogue, character_profile)
        previous_dialogue = f"{character_profile['name']}: {generated_dialogue}"
        previous_character_name = character_profiles[character_name]['name']  # Add this line to store the previous character's name
        character_index = (character_index + 1) % len(character_order)

    # Replace dialogues in the script template
    for i, dialogue in enumerate(generated_dialogues):
        script_template = script_template.replace(f"[Dialogue {i+1}]", dialogue['dialogue'])


    title_url = generate_image(f"theme is {show_title}, cinematic background, Kyoto animation, digital art, hi def, no people")  # Call the generate_image() function
    s3_key = save_image_to_s3(title_url, user_id, show_title)
    # return show_title, generated_dialogues, s3_key
    print(f"Generated Dialogues:\n{generated_dialogues}")
    
    print(f"Script template:\n{script_template}")
    print(f"Actual Total Tokens:\n{actual_total_tokens}")
    return show_title, generated_dialogues, s3_key

# generate_script()

