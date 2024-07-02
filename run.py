import logging
from flask import Flask
import sys
import os
from dotenv import load_dotenv
import json

from flask import Blueprint, request, jsonify, current_app

from app.decorators.security import signature_required
from app.utils.whatsapp_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)

app = Flask(__name__)

load_dotenv()
app.config["ACCESS_TOKEN"] = os.getenv("ACCESS_TOKEN")
app.config["YOUR_PHONE_NUMBER"] = os.getenv("YOUR_PHONE_NUMBER")
app.config["APP_ID"] = os.getenv("APP_ID")
app.config["APP_SECRET"] = os.getenv("APP_SECRET")
app.config["RECIPIENT_WAID"] = os.getenv("RECIPIENT_WAID")
app.config["VERSION"] = os.getenv("VERSION")
app.config["PHONE_NUMBER_ID"] = os.getenv("PHONE_NUMBER_ID")
app.config["VERIFY_TOKEN"] = os.getenv("VERIFY_TOKEN")

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

def handle_message():
    body = request.get_json()
    logging.info(f"request body: {body}")

    # Check if it's a WhatsApp status update
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return jsonify({"status": "ok"}), 200

    try:
        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
            return jsonify({"status": "ok"}), 200
        else:
            # if the request is not a WhatsApp API event, return an error
            logging.error("Not a whatsapp api event")
            return (
                jsonify({"status": "error", "message": "Not a WhatsApp API event"}),
                404,
            )
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        return jsonify({"status": "error", "message": "Invalid JSON provided"}), 400


# Required webhook verifictaion for WhatsApp
def verify():
    # Parse params from the webhook verification request
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    logging.info(f"Received verification request: mode={mode}, token={token},challenge = {challenge}")

    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
            logging.info("WEBHOOK_VERIFIED")
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return challenge,200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            return jsonify({"status": "error", "message": "Verification failed"}), 403
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

@app.route("/")
def jg():
    return f"hello world"

@app.route("/webhook", methods=["GET"])
def webhook_get():
    return verify()

@app.route("/webhook", methods=["POST"])
@signature_required
def webhook_post():
    return handle_message()

if __name__ == "__main__":
    logging.info("Flask app started")
    app.run(host="0.0.0.0", port=8000)
