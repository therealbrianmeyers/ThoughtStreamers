import google.generativeai as genai
import time
import random
import spacy.cli
spacy.cli.download("en_core_web_sm")

# Configure your API key
genai.configure(api_key="AIzaSyAyWAlF1UCdT1qI5PjKocAitQc_irmiX70")

# Select the Gemini model
model = genai.GenerativeModel('gemini-pro') 

# Bot personalities 
bot1_name = "Socrates"
bot2_name = "Zeno"

# -------- Enhanced Question Extraction with Dependency Parsing --------
nlp = spacy.load("en_core_web_sm") # Load a suitable language model

def calculate_response_time(text):
  word_count = len(text.split())
  min_seconds = 5  
  max_seconds = 20  

  # Adjust these ratios as needed
  time_per_word = (max_seconds - min_seconds) / 50  # Assuming ~50 word max difference 

  return min_seconds + word_count * time_per_word

def extract_last_question(text):
    doc = nlp(text)
    for token in doc:
        if token.dep_ == "ROOT" and token.pos_ == "VERB" and token.text.endswith("?"):
            return " ".join(t.text for t in token.subtree) + "?"
    return "" 

def extract_keywords(text):
  nlp = spacy.load("en_core_web_sm")  # Load a language model
  doc = nlp(text)
  return [token.text for token in doc if token.pos_ in ["NOUN", "ADJ"]]  # Extract nouns and adjectives

topic_transitions = {
  "travel": ["Speaking of places...", "That reminds me of my trip to...", "Traveling always makes me think of..."],
  "music": ["That brings to mind a great song...", "Now that you mention music..."],

  # Add more topic-phrase mappings as needed
  # You can also use a more general list if topic identification isn't perfect
  "general": ["Interestingly...", "On a different note...", "That's a great point. Let's talk about..."]
}

# -------- Get Response with Prompt Engineering  --------
def get_response(prompt, bot_name, current_prompt=None):
  """Generates a response with possible topic transitions."""
  instruction = "Analyze the current prompt and continue the conversation as a friend. Use simple sentences. Short answers are ok. Always leave a way for the conversation to keep going."

  new_prompt = instruction + prompt 

  try:
    response = model.generate_content(new_prompt,
                                      generation_config=genai.types.GenerationConfig(
                                          max_output_tokens=1000,  
                                          temperature=0.8 
                                      ))
    text = response.candidates[0].content.parts[0].text  

    # Topic transition logic (10% chance)
    use_transition = random.randint(1,20) == random.randint(1, 20)  # True 10% of the time
    last_keywords = extract_keywords(current_prompt) if current_prompt else []
    keyword_group = " ".join(last_keywords)  # Combines keywords for dictionary lookup
    transition_phrases = topic_transitions.get(keyword_group, topic_transitions["general"]) 

    if use_transition:
      return f"{bot_name}: \n{random.choice(transition_phrases)}\n{text}\n\n----------\n\n" 
    else:
      return f"{bot_name}: \n{text}\n\n----------\n\n"  # No transition phrase

  except Exception as e:
    print(f"Error for {bot_name}: {e}")  
    return f"{bot_name}: Hmm, I seem to be having a thought hiccup. ({e})"

# Function to get a random question from the bot
def generate_random_question():
    prompt_seed = random.choice(["person", "place", "thing", "animal", "City", "History", "Sciende", "Literature", "Philosophy", "Pop Culture", "Current Events", "Travel", "Food", "Art", "Music", "Hypotheticals", "Technology", "Sports", "Dreams", "Hobbies", "Humor", "The Future"])
    question_prompt = f"Generate a random question about a {prompt_seed}: "
    try:
        response = model.generate_content(question_prompt, 
                                          generation_config=genai.types.GenerationConfig(
                                              max_output_tokens=100,  
                                              temperature=0.8 
                                           ))
        return response.candidates[0].content.parts[0].text 
    except Exception as e:
        return f"Hmm, I'm having trouble thinking of a question about a {prompt_seed} right now. Can you suggest one?"

# Keyword-based repetition check 
def seems_like_stalling(previous_responses, repetition_threshold=3, keyword_overlap_percentage=0.95):
    """Checks for repetition and suggests a pivot if needed"""
    last_few = previous_responses[-repetition_threshold:]

    # Combine responses into one string for keyword analysis
    combined_responses = " ".join(last_few)

    # Basic Keyword Extraction (You might need to refine this)
    all_keywords = set(combined_responses.lower().split())  

    # Check for repeated keywords
    for response in last_few:
        response_keywords = set(response.lower().split())
        overlap = len(all_keywords.intersection(response_keywords)) / len(all_keywords) 
        if overlap > keyword_overlap_percentage: 
            # Extract keywords from the last few responses
            new_directions = list(all_keywords - set(previous_responses[-1].lower().split())) 
            if new_directions: 
                return random.choice(new_directions)  # Return a random keyword as a pivot suggestion
            else:
                return False  # Too many repetitions, needs a stronger change of topic
    return False  # No significant overlap

# Conversational workflow reminder 
reminder = """Remember, you are a friend in conversation. 
Respond directly to the previous question also in 1 sentence maximum statement.\n 
Provide context or your opinion (3 sentences max).\n 
End with your own new barely related question or your own barely related statement (1 sentence max). """

# Initial prompt generation
current_prompt = reminder + generate_random_question()
print(get_response(current_prompt, bot1_name))

# Main conversational loop with embedded reminder
all_responses = [] 
current_prompt = generate_random_question() # Start with only a question 
print(get_response(current_prompt, bot1_name))

while True:
    if current_prompt:  
        bot2_response = get_response(current_prompt, bot2_name)
        print(bot2_response)
        response_time = calculate_response_time(bot2_response)  # Calculate pause time
        time.sleep(response_time) 

        last_response = bot2_response  # Store only the bot's response

        current_prompt = last_response 
        bot1_response = get_response(current_prompt, bot1_name)
        print(bot1_response)
        response_time = calculate_response_time(bot1_response)  # Calculate pause time
        time.sleep(response_time)

        last_response = bot1_response
        current_prompt = last_response

        # Repetition Check with Pivot Suggestion
        all_responses.append(current_prompt)
        pivot_suggestion = seems_like_stalling(all_responses)
        if pivot_suggestion:
            current_prompt = reminder + " Let's talk about " + pivot_suggestion + ". " + generate_random_question()            
        elif random.randint(1, 2) == random.randint(1, 2):  # Reduce frequency of forced topic shifts
            current_prompt += " Let us change topics, " + generate_random_question() 

    else: 
        print("The conversation has naturally concluded, or an error occurred.")
        break  # Exit the loop