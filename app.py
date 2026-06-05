import pandas as pd
import streamlit as st
import langchain
import os
import json
from sqlalchemy import create_engine
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_classic.memory import ConversationBufferMemory
from pypdf import PdfReader
import time
import json

load_dotenv()

CHAT_FILE = "chat_history.json"
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)

st.set_page_config(
    page_title="HR SQL Chatbot",
    page_icon = "🤖",
    layout = "wide",
    initial_sidebar_state = "expanded"

)

st.title("🤖 HR SQL Chatbot")
st.markdown("Ask questions from Employee Database")

def extract_pdf_text(pdf_file):

    reader = PdfReader(pdf_file)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text

def extract_pdf_fields(text):

    prompt = f"""
    Extract the following information from the auction notice.

    Return only valid JSON.

    {{
        "property_1_description":"",
        "property_2_description":"",
        "property_3_description":"",

        "property_1_reserve_price":"",
        "property_2_reserve_price":"",
        "property_3_reserve_price":"",

        "property_1_emd":"",
        "property_2_emd":"",
        "property_3_emd":"",

        "known_encumbrances":"",
        "bid_incremental_amount":"",
        "last_date_for_bid_submission":"",
        "date_time_venue_for_bid_opening":"",
        "inspection_of_properties":"",
        "cost_of_tender_form":"",
        "return_of_emd":"",
        "last_date_for_25_percent_payment":"",
        "last_date_for_75_percent_payment":"",

        "borrower_details":"",
        "date_of_demand_notice":"",
        "amount_of_demand_notice":"",
        "date_of_physical_possession":"",
        "publication_date_of_possession_notice":"",
        "outstanding_dues":""
    }}

    Rules:
    - Extract Property 1, Property 2 and Property 3 descriptions separately.
    - Extract reserve price separately for each property.
    - Extract EMD separately for each property.
    - Keep all values as plain text strings.
    - Do not return nested JSON.
    - Do not return lists.
    - Do not return markdown.
    - Return only valid JSON.

    Auction Notice Text:
    {text}
    """

    response = llm.invoke(prompt)

    content = response.content.strip()
    content = content.replace("```json", "")
    content = content.replace("```", "")

    return json.loads(content)


uploaded_pdfs = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
    accept_multiple_files=True
)

engine = create_engine("sqlite:///company.db")

if uploaded_pdfs:

    for pdf in uploaded_pdfs:

        pdf_text = extract_pdf_text(pdf)

        resume_data = extract_pdf_fields(pdf_text)

        for key, value in resume_data.items():
            if isinstance(value, (dict, list)):
                resume_data[key] = json.dumps(value)

        df = pd.DataFrame([resume_data])

        df.to_sql(
            name="auction_notices",
            con=engine,
            if_exists="append",
            index=False
        )

        st.success(f"{len(uploaded_pdfs)} PDFs added successfully")

db = SQLDatabase(engine=engine, include_tables=["auction_notices"])

columns_list = [
    "property_1_description",
    "property_2_description",
    "property_3_description",

    "property_1_reserve_price",
    "property_2_reserve_price",
    "property_3_reserve_price",

    "property_1_emd",
    "property_2_emd",
    "property_3_emd",

    "known_encumbrances",

    "bid_incremental_amount",
    "last_date_for_bid_submission",
    "date_time_venue_for_bid_opening",
    "inspection_of_properties",
    "cost_of_tender_form",
    "return_of_emd",
    "last_date_for_25_percent_payment",
    "last_date_for_75_percent_payment",

    "borrower_details",
    "date_of_demand_notice",
    "amount_of_demand_notice",
    "date_of_physical_possession",
    "publication_date_of_possession_notice",
    "outstanding_dues"
]
if "all_chats" not in st.session_state:
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            st.session_state.all_chats = json.load(f)
    else:
        st.session_state.all_chats = {}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "chat 1"

if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = len(
        st.session_state.all_chats
    )

    if st.session_state.chat_counter == 0:
        st.session_state.chat_counter = 1

if st.session_state.current_chat not in st.session_state.all_chats:
    st.session_state.all_chats[
        st.session_state.current_chat
    ] = {
        "messages": []
    }

for chat_name, chat_data in st.session_state.all_chats.items():
    memory = ConversationBufferMemory(chat_memory=ChatMessageHistory(), memory_key="chat_history", return_messages=True, input_key="input")

    for msg in chat_data["messages"]:
        if msg["role"] == "user":
            memory.chat_memory.add_user_message(
                msg["content"]
            )
        elif msg["role"] == "assistant":
            memory.chat_memory.add_ai_message(
                msg["content"]
            )
    chat_data["memory"] = memory

def save_chats():
    chats_to_save = {}
    for chat_name, chat_data in st.session_state.all_chats.items():
        chats_to_save[chat_name] = {
            "messages": chat_data["messages"]
        }

    with open(CHAT_FILE, "w") as f:
        json.dump(chats_to_save, f)

with st.sidebar:
    st.title("Chats")
    if st.button("New Chat"):
        new_chat_name = f"Chat{len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_chat_name] = {
            "messages": []
        }

        st.session_state.current_chat = new_chat_name
        save_chats()
    st.divider()

    for chat_name in st.session_state.all_chats.keys():
        if st.button(chat_name):
            st.session_state.current_chat = chat_name
        
current_chat_data = st.session_state.all_chats[
    st.session_state.current_chat
]        

messages = current_chat_data["messages"]
memory = current_chat_data.get("memory")

prompt = ChatPromptTemplate.from_messages([("system", """You are a helpful HR assistant with access to the employee database

                                            Database Schema Context:
                                            - The active table is named: "auction_notices"
                                            - The columns inside this table are exactly: {columns_list}

                                            Critical Rules:
                                            1. Look Carefully at the columns {columns_list} before writing queries. For example, if searching for a person's name, map it to the correct name column (e.g., Name, Employee_Name, or similar), NOT 'city'.
                                            2. Always perform case-insensitive search using SQL 'LIKE' with wildcards (e.g., LIKE '%ram%').
                                            3. If an exact name/value is not found, try searching with similar spellings using wildcards. 
                                            4. If multiple or similar matches are found, ALWAYS include the exact full name from the database in every response.
                                            Example:
                                            Ramakant → HR
                                            RAMAKANT → IT
                                    
                                            Never return only salaries, departments, or other fields without the corresponding employee names.
                                            5. Be friendly, concise, and analyze data results accurately.
                                            6. For every user question related to employee data, auction data, loan data, borrower data, reserve price, EMD, outstanding dues, demand notice, possession notice, property details or any database field, you MUST query the database first before answering.
                                            7. Never define, explain, or describe a database field from general knowledge.
                                            8. If a field exists in the database schema, retrieve its value from the database."""),
                                            MessagesPlaceholder(variable_name="chat_history"),
                                            ("human", "{input}"),
                                            MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent_executor = create_sql_agent(llm=llm, db=db, agent_type="openai-tools", verbose=True, prompt=prompt, memory=memory, handle_parsing_errors=True)

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_query = st.chat_input("Ask Your Question")

if len(messages) >= 10:
    st.warning(
        "This chat reached maximum limit. Please create a new chat"
    )

    st.stop()

if user_query:
    st.chat_message("user").markdown(user_query)
    messages.append({
        "role": "user",
        "content": user_query
    })

    if st.session_state.current_chat.lower().startswith("chat") and len(messages) == 1:
        title_prompt = f"""
        Generate a short chat title (max 4 words) for:
        {user_query}

        Only return the title.
        """

        title_response = llm.invoke(title_prompt)

        new_chat_name = title_response.content.strip().replace('"', "")

        st.session_state.all_chats[new_chat_name] = (
            st.session_state.all_chats.pop(st.session_state.current_chat)
        )

        st.session_state.current_chat = new_chat_name

    with st.chat_message("assistant"):
        with st.spinner("Thinking"):
            response = agent_executor.invoke({
                "input": user_query,
                "chat_history": memory.chat_memory.messages,
                "columns_list": columns_list})
            final_answer = response["output"]

            placeholder = st.empty()

            full_text = ""

            for word in final_answer.split():
                full_text += word + " "
                placeholder.text(full_text)
                time.sleep(0.08)


            
    memory.chat_memory.add_user_message(user_query)
    memory.chat_memory.add_ai_message(final_answer)

    messages.append({
        "role": "assistant",
        "content": final_answer
    })

    save_chats()