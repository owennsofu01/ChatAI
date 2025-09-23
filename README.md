# Hush BPO Chatbot

This project is a simple, yet powerful, chatbot for the Hush BPO Services website. It leverages Retrieval-Augmented Generation (RAG) to provide accurate answers to user queries by using the website's content as its knowledge base. The chatbot's backend is built with Python using Flask, while the frontend is a single HTML file with CSS and JavaScript.

-----

### Key Features

  * **Context-Aware Responses:** The chatbot uses a vector database to find the most relevant information from the website's content, ensuring that its answers are grounded and accurate.
  * **Scalable Knowledge Base:** By using a web crawler, the chatbot's knowledge base can be automatically updated as new content is added to the website, eliminating the need for manual data entry.
  * **Interactive UI:** A user-friendly, responsive chat interface allows users to ask questions and receive answers, with a typing indicator and interactive suggestions for related topics.
  * **Powered by Gemini:** The project uses Google's Gemini LLM to generate natural and helpful responses based on the retrieved context.

-----

### Technologies Used

  * **Python:** The core of the backend logic.
  * **Flask:** A lightweight web framework for the backend API.
  * **ChromaDB:** A vector database used to store and query the website's content as embeddings.
  * **Google Gemini API:** The large language model used for generating chatbot responses.
  * **`requests` & `BeautifulSoup`:** Libraries for web scraping and parsing HTML content.
  * **`dotenv`:** For securely managing API keys.

-----

### Getting Started

Follow these steps to set up and run the chatbot on your local machine.

#### Prerequisites

  * Python 3.8 or higher.
  * A Gemini API Key. You can get one from the [Google AI Studio](https://ai.google.dev/).

#### 1\. Clone the repository

```bash
git clone <repository_url>
cd <repository_name>
```

#### 2\. Install Dependencies

Install all the required Python packages using pip.

```bash
pip install -r requirements.txt
```

A `requirements.txt` file for this project should contain:

```
Flask
Flask-Cors
chromadb
google-generativeai
python-dotenv
requests
beautifulsoup4
```

#### 3\. Set Up Your API Key

Create a `.env` file in the root directory of your project and add your Gemini API key.

```bash
GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

#### 4\. Scrape the Website

Run the `text_processor.py` script to crawl the website and create the `website_data.json` file. This file will be used to populate the vector database.

```bash
python text_processor.py
```

This script will print its progress to the console.

#### 5\. Run the Backend

Start the Flask server. The `initialize_chroma_db()` function in `app.py` will automatically load the data from `website_data.json` and build the vector database the first time you run it.

```bash
python app.py
```

The server will run on `http://127.0.0.1:5000`.

#### 6\. Open the Frontend

Simply open the `index.html` file in your web browser. The frontend is a static page that communicates with the Flask backend.

-----

### Project Structure

```
.
├── app.py                  # Backend Flask application
├── text_processor.py       # Web scraper and data processor
├── index.html              # Frontend user interface
├── website_data.json       # Generated knowledge base file
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (API key)
```

-----

### How It Works

1.  **Data Ingestion:** The `text_processor.py` script acts as a web crawler, visiting the website's pages, extracting text and metadata (including the title), and saving it all to `website_data.json`.
2.  **Vectorization:** The `app.py` script reads the `website_data.json` file and converts the text of each document into numerical embeddings using a sentence transformer model. These embeddings are then stored in a ChromaDB collection.
3.  **User Query:** A user types a message in the `index.html` interface, which sends a POST request to the `/chat` endpoint on the Flask server.
4.  **Retrieval:** The backend takes the user's message, converts it into an embedding, and queries the ChromaDB to find the most semantically similar document. It also retrieves other relevant documents to use as suggestions.
5.  **Generation:** The retrieved document's text is added to a prompt along with the user's query. This complete prompt is sent to the Gemini LLM.
6.  **Response:** Gemini generates a coherent and contextually-aware response, which the Flask server sends back to the frontend. The frontend displays the response and the suggestions.
