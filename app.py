import os
import pandas as pd
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from mistralai import Mistral
from mistralai import UserMessage
from astrapy import DataAPIClient  

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
ASTRA_DB_NAMESPACE = os.getenv("ASTRA_DB_NAMESPACE")
ASTRA_DB_COLLECTION = os.getenv("ASTRA_DB_COLLECTION")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")


app = Flask(__name__)

# Initialize AstraDB Client
client = DataAPIClient() 
my_database = client.get_database(
    api_endpoint=ASTRA_DB_API_ENDPOINT,  
    token=ASTRA_DB_APPLICATION_TOKEN,
)
collection = my_database.get_collection(ASTRA_DB_COLLECTION)  

mistral = Mistral(api_key=MISTRAL_API_KEY)

@app.route("/query", methods=["POST"])
def query_forex():
    """Handles user queries about historical forex data"""
    user_input = request.json.get("question", "").lower()

    # Extract date from the question
    words = user_input.split()
    date_in_question = None
    time_in_question = None

    for word in words:
        # Checks for format YYYY-MM-DD
        if word.count("-") == 2:  
            date_in_question = word
            # Checks for HH:MM:SS format
        if ":" in word and len(word) == 8:  
            time_in_question = word

    print(f"🔍 Searching for Date: {date_in_question}, Time: {time_in_question}")

    if date_in_question:
        try:
            query = {"Date": date_in_question}
            if time_in_question:
                query["Time"] = time_in_question

            date_filtered = collection.find_one(query)
            
            if date_filtered:
                return jsonify({
                    "response": f"On {date_in_question} at {time_in_question if time_in_question else 'various times'}, "
                                f"Open: {date_filtered['open']}, High: {date_filtered['high']}, Low: {date_filtered['low']}, Close: {date_filtered['close']}, "
                                f"Tick Volume: {date_filtered['tick_volume']}"
                })
        except Exception as e:
            print("❌ Error during filtering:", str(e))

    messages = [UserMessage(content=f"Answer based on forex data: {user_input}")]
    response = mistral.chat.complete(
        model="mistral-tiny",
        messages=messages,
    )
    return jsonify({"response": response.choices[0].message.content})

if __name__ == "__main__":
    app.run(debug=True)