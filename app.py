import os
import json
import chromadb
from flask import Flask, request, jsonify
from flask_cors import CORS
from chromadb.utils import embedding_functions
from google.generativeai import configure, GenerativeModel
from dotenv import load_dotenv

# --- Configuration and Initialization ---

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("API key not found. Please set the 'GEMINI_API_KEY' environment variable.")

configure(api_key=API_KEY)

app = Flask(__name__)
CORS(app)

# Initialize ChromaDB and load data
def initialize_chroma_db():
    """Initializes the ChromaDB client and loads data from a JSON file."""
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        collection_name = "website_content"
        
        try:
            db_collection = client.get_collection(name=collection_name, embedding_function=sentence_transformer_ef)
            if db_collection.count() > 0:
                print("Vector database already populated. Skipping data loading.")
                return db_collection
        except:
            print("Getting or creating collection: 'website_content'")
            db_collection = client.get_or_create_collection(
                name=collection_name,
                embedding_function=sentence_transformer_ef
            )

        print("Populating the vector database...")
        with open('website_data.json', 'r') as f:
            data = json.load(f)

        if not data:
            print("Error: website_data.json is empty.")
            return None

        documents = [d['text'] for d in data]
        ids = [d['id'] for d in data]
        metadatas = [d['metadata'] for d in data]

        db_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Successfully added {len(documents)} documents to the database.")
        
        return db_collection

    except FileNotFoundError:
        print("Error: website_data.json not found. Please run the text_processor.py script first.")
        return None
    except KeyError as e:
        print(f"Error: Missing key in website_data.json: {e}. Please regenerate the file with the latest text_processor.py.")
        return None
    except Exception as e:
        print(f"Failed to initialize database. Exiting. Error: {e}")
        return None

db_collection = initialize_chroma_db()

# --- Chatbot Logic ---

def generate_response(user_message, db_collection):
    """
    Generates a chatbot response and relevant suggestions using the Gemini LLM.
    """
    # 1. Search the vector database for relevant context (primary response)
    results = db_collection.query(
        query_texts=[user_message],
        n_results=1
    )

    context = results['documents'][0][0]

    # 2. Use the context to formulate a grounded prompt for the LLM
    prompt = f"""
    You are an expert chatbot designed to answer questions about a specific website.
    Use the following context to answer the user's question. If the information is not present,
    politely state that you do not have enough information and suggest they contact the company directly.
    
    Do not use any special formatting characters like asterisks or bolding in your response.
    
    Context:
    {context}
    
    User question:
    {user_message}
    """
    
    # 3. Call the Gemini API to get a response
    try:
        model = GenerativeModel(model_name='gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # 4. Generate suggestions for related topics (query for more results)
        suggestion_results = db_collection.query(
            query_texts=[user_message],
            n_results=10  # Increased to get more diverse results
        )

        # Extract titles from the metadata for suggestions, excluding the top result's title
        suggestions = []
        # Safely get the title of the top result using .get() to prevent KeyError
        top_result_metadata = suggestion_results['metadatas'][0][0]
        top_result_title = top_result_metadata.get('title')

        # Iterate from the second result onwards (index 1)
        for i in range(1, len(suggestion_results['metadatas'][0])):
            metadata = suggestion_results['metadatas'][0][i]
            # Safely get the title for each suggestion
            title = metadata.get('title')
            # Only add if a title exists and it's not the same as the top result
            if title and title != top_result_title:
                suggestions.append(title)
        
        # Remove any duplicates by converting to a set and back to a list
        suggestions = list(set(suggestions))[:3] # Limit to 3 unique suggestions

        return response.text, suggestions
    
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Sorry, I am unable to generate a response at this time.", []
    """
    Generates a chatbot response and relevant suggestions using the Gemini LLM.
    """
    # 1. Search the vector database for relevant context (primary response)
    results = db_collection.query(
        query_texts=[user_message],
        n_results=1
    )

    context = results['documents'][0][0]

    # 2. Use the context to formulate a grounded prompt for the LLM
    prompt = f"""
    You are an expert chatbot designed to answer questions about a specific website.
    Use the following context to answer the user's question. If the information is not present,
    politely state that you do not have enough information and suggest they contact the company directly.

    Context:
    {context}

    User question:
    {user_message}
    """

    # 3. Call the Gemini API to get a response
    try:
        model = GenerativeModel(model_name='gemini-1.5-flash')
        response = model.generate_content(prompt)

        # 4. Generate suggestions for related topics (query for more results)
        suggestion_results = db_collection.query(
            query_texts=[user_message],
            n_results=10  # Increased to get more diverse results
        )

        # Extract titles from the metadata for suggestions, excluding the top result's title
        suggestions = []
        # Safely get the title of the top result using .get() to prevent KeyError
        top_result_metadata = suggestion_results['metadatas'][0][0]
        top_result_title = top_result_metadata.get('title')

        # Iterate from the second result onwards (index 1)
        for i in range(1, len(suggestion_results['metadatas'][0])):
            metadata = suggestion_results['metadatas'][0][i]
            # Safely get the title for each suggestion
            title = metadata.get('title')
            # Only add if a title exists and it's not the same as the top result
            if title and title != top_result_title:
                suggestions.append(title)
        
        # Remove any duplicates by converting to a set and back to a list
        suggestions = list(set(suggestions))[:3] # Limit to 3 unique suggestions

        return response.text, suggestions

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Sorry, I am unable to generate a response at this time.", []
# --- API Endpoint ---

@app.route('/chat', methods=['POST'])
def chat():
    if db_collection is None:
        return jsonify({"response": "The chatbot service is not available. Please check the backend logs."}), 503

    data = request.get_json(silent=True)

    if not data or 'message' not in data or not isinstance(data['message'], str):
        return jsonify({"error": "Invalid JSON or missing 'message' key"}), 400

    user_message = data['message']
    
    print(f"User message: {user_message}")
    
    # Generate the chatbot response and suggestions
    bot_response, suggestions = generate_response(user_message, db_collection)
    
    print(f"Bot response: {bot_response}")
    print(f"Suggestions: {suggestions}")
    
    return jsonify({"response": bot_response, "suggestions": suggestions})

if __name__ == '__main__':
    app.run(debug=True)