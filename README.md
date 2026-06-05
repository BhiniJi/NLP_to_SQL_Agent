<<<<<<< HEAD
# NLP_to_SQL_Agent
=======
# HR SQL Chatbot (Streamlit + LangChain + SQL Agent)

This project is a Streamlit-based AI chatbot that allows users to:
- Upload PDF documents (auction/HR notices)
- Extract structured data using LLM (GPT-4o-mini)
- Store extracted data in a SQLite database
- Query the database using natural language (SQL Agent)
- Maintain multi-chat memory with conversation history

## Features

### PDF Processing
- Extracts text from uploaded PDFs
- Uses LLM to convert unstructured text into structured JSON
- Automatically stores data into SQLite database

### AI SQL Chatbot
- Uses LangChain SQL Agent
- Converts user questions into SQL queries
- Retrieves accurate answers from database

### Chat System
- Multiple chat support
- Chat history saved in `chat_history.json`
- Auto-generated chat titles using LLM
- Streamed responses for better UX

### Database
- SQLite database (`company.db`)
- Table: `auction_notices`

## Tech Stack

- Streamlit
- LangChain
- OpenAI GPT-4o-mini
- SQLite (SQLAlchemy)
- PyPDF
- Pandas

## Project Structure

project/
│── app.py
│── chat_history.json
│── company.db
│── .env
│── requirements.txt
│── README.md
>>>>>>> e431437 (Initial Commit -NLP to SQL Agent Project)
