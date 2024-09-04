#! /usr/bin/env python3.6
"""
Python 3.6 or newer required.
"""
import json
import os
import stripe
from flask import request, jsonify

from app import app

# This is your test secret API key.
stripe.api_key = 'sk_test_51P4gS7Ru8OQcbSBQBB5yE0k1AGqOSwe0AOY03P9cmZjJ9EQVCphq6QJCJ1aZAtI0EmUKV9vWoMc8nAXnhmEQ6Pa300X3qngnqw'


def calculate_order_amount(items):
    # Replace this constant with a calculation of the order's amount
    # Calculate the order total on the server to prevent
    # people from directly manipulating the amount on the client
    return 1400


def charge_customer(customer_id):
    # Lookup the payment methods available for the customer
    payment_methods = stripe.PaymentMethod.list(
        customer=customer_id,
        type='card'
    )
    # Charge the customer and payment method immediately
    try:
        stripe.PaymentIntent.create(
            amount=1099,
            currency='usd',
            customer=customer_id,
            payment_method=payment_methods.data[0].id,
            off_session=True,
            confirm=True
        )
    except stripe.error.CardError as e:
        err = e.error
        # Error code will be authentication_required if authentication is needed
        print('Code is: %s' % err.code)
        payment_intent_id = err.payment_intent['id']
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)


@app.route('/create-payment-intent', methods=['POST'])
def create_payment():
    # Alternatively, set up a webhook to listen for the payment_intent.succeeded event
    # and attach the PaymentMethod to a new Customer
    customer = stripe.Customer.create()

    try:
        data = json.loads(request.data)
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            customer=customer['id'],
            setup_future_usage='off_session',
            amount=calculate_order_amount(data['items']),
            currency='usd',
            # In the latest version of the API, specifying the `automatic_payment_methods` parameter is optional because Stripe enables its functionality by default.
            automatic_payment_methods={
                'enabled': True,
            },
        )
        return jsonify({
            'clientSecret': intent['client_secret']
        })
    except Exception as e:
        return jsonify(error=str(e)), 403
