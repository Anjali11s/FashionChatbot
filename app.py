from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging

# Load API key from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")

# Configure Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

# Initialize Flask app
app = Flask(__name__)

# Setup logging
logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(message)s')


def extract_keywords_from_prompt(prompt):
    try:
        keyword_prompt = (
            f"Extract the main product keywords from this fashion-related query for shopping search. "
            f"Only return 3 to 5 relevant words without extra explanation:\n\n'{prompt}'"
        )
        response = model.generate_content(keyword_prompt)
        keywords = response.text.strip().replace("\n", " ").replace(",", " ").split()
        return "+".join(keywords[:6])  # Limit to top 6 keywords
    except Exception as e:
        logging.error(f"Keyword Extraction Failed: {str(e)}")
        return prompt.replace(" ", "+")  # fallback

def query_gemini(prompt):
    """Helper function to call Gemini API with error handling."""
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip().replace("\n", "<br>") if response.text else "No response available."

        # Generate a relevant Pinterest search link
        if "outfit" in prompt or "suggest an outfit" in prompt:
            search_query = prompt.replace(" ", "+")
            pinterest_url = f"https://www.pinterest.com/search/pins/?q={search_query}"
            pinterest_img_url = "https://i.pinimg.com/236x/76/8e/1a/768e1a5c4cb94e3f3b6e3f2e6a5f1b58.jpg"

            result_text += f"""
            <br><br><strong>🔗 Outfit Idea Preview:</strong><br>
            <a href="{pinterest_url}" target="_blank">
                <img src="{pinterest_img_url}" alt="Outfit Preview" style="width:200px; height:auto; border-radius:10px; margin-top:5px;">
            </a>
            <br>
            <a href="{pinterest_url}" target="_blank" style="display:inline-block; padding:10px 15px; margin-top:5px;
            background-color:#ff4081; color:white; font-weight:bold; text-decoration:none; border-radius:5px;">
            🌟 View More Outfit Suggestions 🌟</a>
            """

        # Add Amazon / Myntra / Flipkart buttons for shopping
        
        # search_term = prompt.replace(" ", "+")
        search_term = extract_keywords_from_prompt(prompt)

        shopping_buttons = f"""
        <!--CUSTOM-BUTTONS-->
        <br><br><strong>🛍️ Explore Matching Products:</strong><br>
        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;">
            <a href="https://www.amazon.in/s?k={search_term}" target="_blank" 
               style="background-color: #ff9900; color: white; padding: 10px 15px; border-radius: 5px; text-decoration: none;">
               🛒 Amazon
            </a>
            <a href="https://www.myntra.com/{search_term}" target="_blank" 
               style="background-color: #e91e63; color: white; padding: 10px 15px; border-radius: 5px; text-decoration: none;">
               👗 Myntra
            </a>
            <a href="https://www.flipkart.com/search?q={search_term}" target="_blank" 
               style="background-color: #2874f0; color: white; padding: 10px 15px; border-radius: 5px; text-decoration: none;">
               📦 Flipkart
            </a>
        </div>
        """

        result_text += shopping_buttons
        return result_text

    except Exception as e:
        logging.error(f"API Call Failed: {str(e)}")
        return "I'm facing some issues retrieving fashion data. Please try again later."

@app.route("/")
def home():
    # return render_template("index.html")
    return "Flask app Render pe successfully chal raha hai!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip().lower()

    if not user_input:
        return jsonify({"response": "Please enter a valid fashion-related query."})
    # Ask Gemini if the query is fashion-related
    validation_prompt = f"Is the following query related to fashion? Answer only 'yes' or 'no': {user_input}"
    validation_response = query_gemini(validation_prompt).lower()

    if "yes" in validation_response:
        prompt = f"Fashion-related query: {user_input}. Provide relevant advice, outfit suggestions, or styling tips ."
        return jsonify({"response": query_gemini(prompt)})

    return jsonify({"response": "I'm a fashion advisor! Ask me something related to clothing, styling, or brands."})


if __name__ == "__main__":
    app.run(debug=True)

