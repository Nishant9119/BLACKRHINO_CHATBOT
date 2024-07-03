import openai
import shelve
from dotenv import load_dotenv
import os
import time
import logging

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)

def create_assistant():
    response = openai.Assistant.create(
        name="Sustainability Bot",
        instructions="You are a sustainability bot and you have to answer queries related to sustainability.",
        model="gpt-3.5-turbo-16k",
    )
    return response['id']

def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)

def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id

def run_assistant(thread_id):
    response = openai.Thread.run(thread_id=thread_id)
    while response['status'] != "completed":
        time.sleep(0.5)
        response = openai.Thread.retrieve_run(thread_id=thread_id, run_id=response['id'])
    messages = openai.Thread.list_messages(thread_id=thread_id)
    new_message = messages['data'][0]['content']
    logging.info(f"Generated message: {new_message}")
    return new_message

def generate_response(message_body, wa_id):
    thread_id = check_if_thread_exists(wa_id)
    if thread_id is None:
        logging.info(f"Creating new thread for wa_id {wa_id}")
        thread = openai.Thread.create()
        thread_id = thread['id']
        store_thread(wa_id, thread_id)
    else:
        logging.info(f"Retrieving existing thread for wa_id {wa_id}")
    
    openai.Message.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )
    new_message = run_assistant(thread_id)
    return new_message