from fastapi import FastAPI, HTTPException, Request
import stripe
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
