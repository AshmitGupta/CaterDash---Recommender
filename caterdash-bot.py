from flask import Flask, request, jsonify
import pandas as pd
import random
from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv
import openai

app = Flask(__name__)

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-4o"

# Function to recommend a meal based on components for Indian cuisine
def recommend_indian_meal(cuisine_data, per_person_budget):
    meal = []
    total_cost = 0

    # Select one veg and one non-veg curry
    veg_curry = cuisine_data[(cuisine_data['Product Sub-category'].str.contains("Curry-Platter", case=False)) & (cuisine_data['Vegan'] == True)]
    non_veg_curry = cuisine_data[(cuisine_data['Product Sub-category'].str.contains("Curry-Platter", case=False)) & (cuisine_data['Vegan'] == False)]
    if not veg_curry.empty:
        chosen_veg = veg_curry.sample()
        meal.append(chosen_veg.iloc[0]['Product Name'])
        total_cost += (chosen_veg.iloc[0]['Product Price per person']) / 2
        veg_curry = veg_curry.drop(chosen_veg.index)  # Remove chosen item to avoid repetition
    if not non_veg_curry.empty:
        chosen_non_veg = non_veg_curry.sample()
        meal.append(chosen_non_veg.iloc[0]['Product Name'])
        total_cost += (chosen_non_veg.iloc[0]['Product Price per person']) / 2
        non_veg_curry = non_veg_curry.drop(chosen_non_veg.index)  # Remove chosen item to avoid repetition

    # Randomly choose between a rice or breads platter
    rice_or_bread = random.choice(['Rice-Platter', 'Breads-Platter'])
    chosen_side = cuisine_data[cuisine_data['Product Sub-category'].str.contains(rice_or_bread, case=False)]
    if not chosen_side.empty:
        chosen = chosen_side.sample()
        meal.append(chosen.iloc[0]['Product Name'])
        total_cost += chosen.iloc[0]['Product Price per person']
        chosen_side = chosen_side.drop(chosen.index)  # Remove chosen item to avoid repetition

    # Always include a dessert
    dessert = cuisine_data[cuisine_data['Product Sub-category'].str.contains("Dessert-Platter", case=False)]
    if not dessert.empty:
        chosen_dessert = dessert.sample()
        meal.append(chosen_dessert.iloc[0]['Product Name'])
        total_cost += chosen_dessert.iloc[0]['Product Price per person']
        dessert = dessert.drop(chosen_dessert.index)  # Remove chosen item to avoid repetition

    # Add as many appetizers as possible
    appetizers = cuisine_data[cuisine_data['Product Sub-category'].str.contains("Appetizer-Platter", case=False)]
    while not appetizers.empty:
        chosen_app = appetizers.sample()
        if total_cost + chosen_app.iloc[0]['Product Price per person'] <= per_person_budget:
            meal.append(chosen_app.iloc[0]['Product Name'])
            total_cost += chosen_app.iloc[0]['Product Price per person']
            appetizers = appetizers.drop(chosen_app.index)  # Remove chosen item to avoid repetition
        else:
            break  # Stop if adding another appetizer exceeds the budget

    return meal, total_cost

# Function to recommend a meal based on components for Chinese cuisine
def recommend_chinese_meal(cuisine_data, per_person_budget):
    meal = []
    total_cost = 0

    # Select one veg and one non-veg main
    veg_main = cuisine_data[(cuisine_data['Product Sub-category'].str.contains("Main-Platter", case=False)) & (cuisine_data['Vegan'] == True)]
    non_veg_main = cuisine_data[(cuisine_data['Product Sub-category'].str.contains("Main-Platter", case=False)) & (cuisine_data['Vegan'] == False)]
    if not veg_main.empty:
        chosen_veg = veg_main.sample()
        meal.append(chosen_veg.iloc[0]['Product Name'])
        total_cost += (chosen_veg.iloc[0]['Product Price per person']) / 2
        veg_main = veg_main.drop(chosen_veg.index)  # Remove chosen item to avoid repetition
    if not non_veg_main.empty:
        chosen_non_veg = non_veg_main.sample()
        meal.append(chosen_non_veg.iloc[0]['Product Name'])
        total_cost += (chosen_non_veg.iloc[0]['Product Price per person']) / 2
        non_veg_main = non_veg_main.drop(chosen_non_veg.index)  # Remove chosen item to avoid repetition

    # Randomly choose between a rice or noodle platter
    rice_or_noodle = random.choice(['Rice-&-Noodles-Platter'])
    chosen_side = cuisine_data[cuisine_data['Product Sub-category'].str.contains(rice_or_noodle, case=False)]
    if not chosen_side.empty:
        chosen = chosen_side.sample()
        meal.append(chosen.iloc[0]['Product Name'])
        total_cost += chosen.iloc[0]['Product Price per person']
        chosen_side = chosen_side.drop(chosen.index)  # Remove chosen item to avoid repetition

    # Add as many appetizers as possible
    appetizers = cuisine_data[cuisine_data['Product Sub-category'].str.contains("Appetizer-Platter", case=False)]
    while not appetizers.empty:
        chosen_app = appetizers.sample()
        if total_cost + chosen_app.iloc[0]['Product Price per person'] <= per_person_budget:
            meal.append(chosen_app.iloc[0]['Product Name'])
            total_cost += chosen_app.iloc[0]['Product Price per person']
            appetizers = appetizers.drop(chosen_app.index)  # Remove chosen item to avoid repetition
        else:
            break  # Stop if adding another appetizer exceeds the budget

    return meal, total_cost

# Function to filter dishes by exact category and meal style
def filter_dishes(data, category, style):
    category_data = data[data['Product Categories'].str.contains(category, case=False, na=False)]
    style_data = category_data[category_data['Kind'].str.contains(style, case=False, na=False)]
    return style_data

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')

    messages = [
        {"role": "system", "content": "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."},
        {"role": "user", "content": user_message}
    ]
    
    chat_response = chat_completion_request(
        messages,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "caterdash_call",
                    "description": "Get the Meal Recommendation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "budget": {
                                "type": "integer",
                                "description": "The total budget of the event",
                            },
                            "number_of_people": {
                                "type": "integer",
                                "description": "The total number of people attending the event",
                            },
                            "meal_preference": {
                                "type": "string",
                                "description": "The preferred meal type (Indian/Chinese)",
                            },
                        },
                        "required": ["budget", "number_of_people", "meal_preference"],
                    },
                }
            }
        ]
    )
    
    if chat_response.choices[0].finish_reason == "tool_calls":
        tool_data = chat_response.choices[0].message.tool_calls[0].function.arguments
        budget = tool_data['budget']
        number_of_people = tool_data['number_of_people']
        meal_preference = tool_data['meal_preference']
        result = caterdash_call(budget, number_of_people, meal_preference)
        return jsonify({"response": result})
    else:
        assistant_message = chat_response.choices[0].message.content
        return jsonify({"response": assistant_message})

@app.route('/')
def index():
    return app.send_static_file('index.html')

def caterdash_call(budget, number_of_people, meal_preference):
    # Load the dataset
    file_path = 'cater-menu-v7.csv'
    menu_data = pd.read_csv(file_path)

    # Calculate per person budget
    per_person_budget = budget / number_of_people

    if meal_preference.lower() == 'indian':
        # Filter for Indian cuisine and meal style
        indian_data = filter_dishes(menu_data, "Indian", "Platter")
        # Recommend a meal
        meal, cost = recommend_indian_meal(indian_data, per_person_budget)
    elif meal_preference.lower() == 'chinese':
        # Filter for Chinese cuisine and meal style
        chinese_data = filter_dishes(menu_data, "Chinese", "Platter")
        # Recommend a meal
        meal, cost = recommend_chinese_meal(chinese_data, per_person_budget)
    else:
        return "Invalid meal preference. Please choose 'Indian' or 'Chinese'."

    if meal and cost <= per_person_budget:
        return f"Recommended {meal_preference.capitalize()} meal: {meal}\nTotal cost per person: {cost}"
    else:
        return f"No {meal_preference.capitalize()} meal combination found within the budget."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)