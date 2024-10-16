import logging
from fastapi import FastAPI, HTTPException, Request
import stripe
import yagmail
import pymongo

import json
from bson import ObjectId

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Your test secret API key
stripe.api_key = os.getenv("STRIPE")

# Replace 'your_connection_string' with your actual MongoDB connection string
client = MongoClient(os.getenv("MONGO_URI"))
ONESIGNALAPIKEY = os.getenv("ONESIGNAL")


def send_push_notifications(APIKEY):
    import requests
    import json


    # Define the URL and headers
    url = "https://api.onesignal.com/notifications"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {APIKEY}"
    }

    # Define the payload
    payload = {
        "app_id": "c0781cfa-4181-49ff-be9a-6c8ac11e5421",
        "contents": {"en": "Push NOtification was triggered by making triggering a payment intent success event"},
        "headings": {"en": "New Order"},
        "priority": 10,
        "included_segments": ["All"]
    }

    # Make the POST request
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Print the response
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")




def process_successful_payments():

        import requests
        db = client['Deliveries']
        collection = db['users']
        # Fetch the data from the API
        response = requests.get('https://auto-gen-payment-link-stripe.vercel.app/api/v1/successful-payments')

        # Check if the request was successful
        if response.status_code == 200:
            json_data = response.json()  # Parse the JSON response
        else:
            print(f"Error: {response.status_code} - {response.text}")
        
            
        # Access the successfulPayments list
        successful_payments = json_data['successfulPayments']
        

        for payment in successful_payments:
            if payment['status'] == 'succeeded':
                documents = collection.find({'email': payment['buyerEmail']})
                for doc in documents:
                    if (doc['pick_up_details']['mainText'] in payment['itemsBought'][0]['productDescription']) and \
                       (doc['drop_off_details']['mainText'] in payment['itemsBought'][0]['productDescription']) and \
                       (doc['schedule']['pickUpTime'] in payment['itemsBought'][0]['productDescription']) and \
                       (doc['schedule']['pickUpDate'] in payment['itemsBought'][0]['productDescription']) and \
                       (doc['schedule']['dropOffTime'] in payment['itemsBought'][0]['productDescription']) and \
                       (doc['schedule']['dropOffDate'] in payment['itemsBought'][0]['productDescription']):
                        
                        # Create a document to insert
                        document = {
                            '_id': payment['id'],
                            'name': payment['buyerName'],
                            'email': payment['buyerEmail'],
                            'amount': payment['amount'],
                            'phoneNumber': payment['buyerPhone'],
                            'pickupTime': doc['schedule']['pickUpTime'],
                            'pickupDate': doc['schedule']['pickUpDate'],
                            'dropoffTime': doc['schedule']['dropOffTime'],
                            'dropoffDate': doc['schedule']['dropOffDate'],
                            'dropoffLocation': doc['drop_off_details']['mainText'],
                            'pickupLocationSub': doc['pick_up_details']['subText'],
                            'dropoffLocationSub': doc['drop_off_details']['subText'],
                            'pickupLocation': doc['pick_up_details']['mainText'],
                            'origin_place_id': doc['pick_up_details']['placeId'],
                            'destination_place_id': doc['drop_off_details']['placeId'],
                            'status': "pick Up"
                        }
                        
                        deliveries_collection = db['deliveries']
                        try:
                            import requests
                            import json
                            deliveries_collection.insert_one(document=document)
                            print("a new order has been added ")
                            url = "https://api.onesignal.com/notifications"
                            headers = {
                                "Content-Type": "application/json; charset=utf-8",
                                "Authorization": "Basic M2RhNmI5MGUtNTk0Mi00ZmFiLThjN2UtYTI1YWU0ZWQwMmM1"
                            }

                            # Define the payload
                            payload = {
                                "app_id": "c0781cfa-4181-49ff-be9a-6c8ac11e5421",
                                "contents": {"en": f"Pick Up Location: {doc['pick_up_details']['mainText']} Drop Off Location: {doc['drop_off_details']['mainText']}"},
                                "headings": {"en": "A new Order Just came In"},
                                "priority": 10,
                                "included_segments": ["All"]
                            }

                            # Make the POST request
                            response = requests.post(url, headers=headers, data=json.dumps(payload))

                            # Print the response
                            print(f"Status Code: {response.status_code}")
                            print(f"Response: {response.json()}")

                            
                        except pymongo.errors.DuplicateKeyError:
                            print("Document already added before")

# Replace this endpoint secret with your endpoint's unique secret
endpoint_secret = os.getenv("ENDPOINT")  # Use your actual endpoint secret
# SMTP server details
smtp_user = 'admin@247doordelivery.co.uk'
smtp_password = 'Password10!'
smtp_host = 'smtp.hostinger.com'
smtp_port = 465

# Function to send a simple payment complete email
def send_payment_complete_email():
    customer_email = 'uririnathaniel@gmail.com'
    email_subject = 'A Was Payment Completed Successfully! 💰'
    email_body = """
    Hi there,

    We are pleased to inform You that A payment has been completed successfully. 

    Best regards,
    
    """
    
    try:
        with yagmail.SMTP(smtp_user, smtp_password, host=smtp_host, port=smtp_port) as yag:
            yag.send(to=customer_email, subject=email_subject, contents=email_body)
            print(f"Email sent to {customer_email} successfully!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")




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
        send_payment_complete_email()
        process_successful_payments()
        send_push_notifications(ONESIGNALAPIKEY)
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
