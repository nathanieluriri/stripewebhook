import logging
from fastapi import FastAPI, HTTPException, Request
import stripe
from fastapi.responses import PlainTextResponse

import json
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Your test secret API key
stripe.api_key = os.getenv("STRIPE")

# Replace this endpoint secret with your endpoint's unique secret
endpoint_secret = os.getenv("ENDPOINT")  # Use your actual endpoint secret

class SingleLogFileHandler(logging.FileHandler):
    """Custom file handler to keep only the latest log entry."""
    def __init__(self, filename, mode='w'):
        super().__init__(filename, mode)

    def emit(self, record):
        # Clear the log file before writing a new log entry
        self.stream.close()  # Close the existing stream
        self.stream = self._open()  # Reopen the stream
        self.stream.truncate(0)  # Clear the log file
        super().emit(record)  # Write the new log entry
# Configure logging
log_file_path = "app.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[SingleLogFileHandler(log_file_path)]
)
logger = logging.getLogger(__name__)


@app.get("/logs", response_class=PlainTextResponse)
async def read_logs():
    try:
        with open("app.log", "r") as log_file:
            logs = log_file.read()
        return logs
    except Exception as e:
        logger.error("Error reading log file: %s", e)
        return "Could not read log file."
    


@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    event = None

    try:
        # Verify the webhook signature
        if endpoint_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        else:
            event = json.loads(payload)
    except json.JSONDecodeError as e:
        print('⚠️  Webhook error while parsing basic request: ' + str(e))
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        print('⚠️  Webhook signature verification failed: ' + str(e))
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']  # contains a stripe.PaymentIntent
        print('Payment for {} succeeded'.format(payment_intent['amount']))
        logger.info('Payment for {} succeeded'.format(payment_intent['amount']))
        # Handle the successful payment intent here if needed
    elif event['type'] == 'payment_method.attached':
        payment_method = event['data']['object']  # contains a stripe.PaymentMethod
        # Handle the successful attachment of a PaymentMethod here if needed
    else:
        # Unexpected event type
        print('Unhandled event type {}'.format(event['type']))

    return {"success": True}

# To run the FastAPI application, use:
# uvicorn filename:app --reload
