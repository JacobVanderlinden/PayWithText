from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import twilio.twiml
from models import Customer, outstanding_requests
from django.http.response import HttpResponse
from django_twilio.decorators import twilio_view
from twilio.rest import TwilioRestClient
import requests
import json
import random
import datetime

apiKey = '2565b3aa12f9a820a70689b5301852e1'
account_sid = "AC5bcfd5c781b6d936a80cb68108a6497d" # Your Account SID from www.twilio.com/console
auth_token  = "6c6096b3bf9590efcc7bd9755956b9fd"  # Your Auth Token from www.twilio.com/console
client = TwilioRestClient(account_sid, auth_token)

# CapitalOne functions

def get_account(customer):
    url = "http://api.reimaginebanking.com/customers/{}/accounts?key=2565b3aa12f9a820a70689b5301852e1".format(customer.capital_one_id)
    response = requests.get(
        url, 
        headers={'content-type':'application/json'},
    )
    response = response.json()
    print(response)
    return response[0]['_id']

def create_account(customer):
    url = 'http://api.reimaginebanking.com/customers/{}/accounts?key=2565b3aa12f9a820a70689b5301852e1'.format(customer.capital_one_id)
    payload = {
      "type": "Checking",
      "nickname": "PayWithCard Account",
      "rewards": 0,
      "balance": float("%.2f" % (random.randint(1,10000) + random.random())),
      "account_number": "000000" + str(customer.phone_number)
    }
    response = requests.post(
        url,
        data = json.dumps(payload),
        headers={'content-type':'application/json'},    
    )
    response = response.json()
    print(response)
    account_number = response[u'objectCreated'][u'account_number']
    return account_number

def create_customer(customer):
    url = 'http://api.reimaginebanking.com/customers?key=2565b3aa12f9a820a70689b5301852e1'
    payload = {
      "first_name": customer.first_name,
      "last_name": customer.last_name,
      "address": {
        "street_number": "700",
        "street_name": "San Jacinto Blvd",
        "city": "Austin",
        "state": "TX",
        "zip": "78701"
      }
    }
    # Create a Savings Account
    response = requests.post( 
        url, 
        data=json.dumps(payload),
        headers={'content-type':'application/json'},
    )
    response = response.json()
    print(response)
    customer_number = response[u'objectCreated'][u'_id']
    customer.capital_one_id = customer_number
    create_account(customer)
    return customer_number

def get_balance(customer):
    url = 'http://api.reimaginebanking.com/customers/{}/accounts?key=2565b3aa12f9a820a70689b5301852e1'.format(customer.capital_one_id)
    response = requests.get(
        url, 
        headers={'content-type':'application/json'},
    )
    response = response.json()
    return response[0]["balance"]

def transfer_balance(c1, c2, amount):
    now = datetime.datetime.now()
    url = 'http://api.reimaginebanking.com/accounts/{}/transfers?key=2565b3aa12f9a820a70689b5301852e1'.format(get_account(c1))
    payload = {
      "medium": "balance",
      "payee_id": get_account(c2),
      "amount": float(amount),
      "transaction_date": "%d-%d-%d" % (now.year, now.month, now.day),
      "description": "PayWithText Transfer"
    }
    response = requests.post(
        url,
        data=json.dumps(payload),
        headers={'content-type':'application/json'},
    )
    response = response.json()
    print(response)
    return response

# Misc functions

def is_float(string1):
    try:
        string1 = float(string1)
        return True
    except:
        try:
            string1 = int(string1)
            return True
        except:
            False

# Views

@twilio_view
def entry(request):
    # Get current message and uppercase value of message (in case of keyword)
    message_body = request.POST.get('Body', '')
    message_upper = message_body.upper()
    # Create a twilio response
    resp = twilio.twiml.Response()
    # Check if user is authenticated
    is_authenticated = request.session.get('is_authenticated', False)
    # Each path supported by application
    keywords = {
        "SIGNUP":"/signup",
        "VIEW":"/view",
        "RESTART":"/restart",
        "CMD":"/cmd",
        "EDIT":"/edit",
        "BALANCE":"/balance",
        "PAY":"/pay",
        "REQUEST":"/request",
        "PAYREQUEST":"/payrequest",
    }
    # States user can be in that require redirect
    states = {
        "signup_started":"/signup",
        "edit_started":"/edit",
        "pending_payment":"/pay",
        "request_started":"/request",
        "request_made":"/payrequest",
    }
    # Check if user is in states established above
    state_added = False
    for state in states:
        if request.session.get(state):
            resp.redirect(states[state])
            state_added = True
    # Check if user sent keyword
    if (((message_upper in keywords) or (message_upper.split(" ")[0] in keywords)) and not state_added):
        resp.redirect(keywords[message_upper.split(" ")[0]])
    # Send default text
    elif not state_added:
        if is_authenticated:
            resp.sms("Welcome to PayWithText! Send CMD for a list of commands.")
        else:
            resp.sms("Welcome to PayWithText! Respond SIGNUP to start using our service.")
    # Return TwiML
    return resp

# Signup view
@twilio_view
def signup(request):
    # Create Twilio response
    resp = twilio.twiml.Response()
    # Get message body
    message_body = request.POST.get('Body', '')
    # Check for signup states
    signup_started = request.session.get('signup_started', False)
    pin_requested = request.session.get('pin_requested', False)
    is_authenticated = request.session.get('is_authenticated', False)
    first_name_given = request.session.get('first_name_given', False)
    # Begin signup tree traversal
    if signup_started:
        if first_name_given:
            if pin_requested:
                if len(message_body) == 4 and message_body.isnumeric():
                    request.session['pin'] = message_body
                    from_number = request.POST.get('From', None)[2:]
                    new_user = Customer.objects.create(phone_number=from_number, first_name=request.session['first_name'], last_name=request.session['last_name'], pin=request.session['pin'])
                    create_customer(new_user)
                    new_user.save()
                    
                    message = "Signup complete! Type CMD for a list of available commands."
                    request.session['is_authenticated'] = True
                    request.session['signup_started'] = False
                    resp.sms(message)
                    resp.redirect("/balance")
                else:
                    message = "Sorry, please send a 4-digit numeric pin."
                    resp.sms(message)
            else:
                request.session['last_name'] = message_body
                message = "Great. Now, please enter a 4-digit numeric pin we'll use to confirm your payments."
                request.session['pin_requested'] = True
                resp.sms(message)
        else:
            request.session['first_name'] = message_body
            request.session['first_name_given'] = True
            message = "Thanks %s! What's your last name?" % message_body
            resp.sms(message)
    else:
        if is_authenticated:
            message = "Whoops, looks like you've already registered!\nYou can send RESTART to reset your account."
            resp.sms(message)
        else:
            message = "Let's get you signed up! Please reply with your first name."
            request.session['signup_started'] = True
            resp.sms(message)
    # Return TwiML
    return str(resp)

# View to see current user information. Remove in production, used for debugging
@twilio_view
def view(request):
    # Create TwiML response
    resp = twilio.twiml.Response()
    try:
        this_customer = Customer.objects.get(phone_number=request.POST.get('From', '')[2:])
    except:
        message = "Please register to use this feature!"
        resp.sms(message)
        return str(resp)
    # String with user information
    user_number = request.POST.get('From', None)[2:]
    try:
        user = Customer.objects.get(phone_number=user_number)
        message = "First name: %s\nLast name: %s\nPhone number: %s\nPin: %s" % (user.first_name, user.last_name, user.phone_number, user.pin)
    except:
        message = "Sorry, you weren't found in our database."
    resp.sms(message)
    # Return TwiML
    return str(resp)

# Resets account associated with phone number
# In production, replace middle section by deleting row in DB associated with phone number
@twilio_view
def restart(request):
    # Create TwiML response
    resp = twilio.twiml.Response()
    # Remove states from signup
    request.session['is_authenticated'] = False
    request.session['signup_started'] = False
    request.session['pin_requested'] = False
    request.session['first_name_given'] = False
    # Remove user information
    request.session['first_name'] = None
    request.session['last_name'] = None
    request.session['pin'] = None
    # Remove states from edit
    request.session['edit_started'] = False
    request.session['pin_confirmed'] = False
    request.session['trait_selected'] = False
    # Remove states from pay and request
    request.session['pending_payment'] = False
    request.session['payment_request'] = False
    request.session['request_started'] = False
    request.session['request_shown'] = False
    request.session['request_selected'] = False
    # Removing row from database
    try:
        Customer.objects.get(phone_number=request.POST.get('From', None)[2:]).delete()
    except:
        pass
    # Confirm removal
    message = "Your account has been reset. Please respond with SIGNUP to re-register."
    resp.sms(message)
    # Return TwiML
    return str(resp)

# See list of available commands 
@twilio_view
def cmd(request):
    #Establish response
    resp = twilio.twiml.Response()
    message = """
    Commands
    EDIT - Edit your profile
    RESTART - Reset all your information
    BALANCE - Check your balance
    PAY - Create a payment
    REQUEST - Request a payment
    PAYREQUEST - Approve/deny a request
    VIEW - View your information
    """
    resp.sms(message)
    # Return TwiML
    return str(resp)

# Edit current information
@twilio_view
def edit(request):
    # Establish response and evaluate message body text
    resp = twilio.twiml.Response()
    try:
        this_customer = Customer.objects.get(phone_number=request.POST.get('From', '')[2:])
    except:
        message = "Please register to use this feature!"
        resp.sms(message)
        return str(resp)
    message_body = request.POST.get('Body', '')
    # Check for Edit states
    edit_started = request.session.get('edit_started', False)
    pin_verified = request.session.get('pin_verified', False)
    trait_selected = request.session.get('trait_selected', False)
    # List of characteristics to edit
    characteristics = {
        #ID:[trait_name, verbose_name],
        "1":["first_name", "first name"],
        "2":["last_name", "last name"],
        "3":["pin", "pin"],
    }
    # Begin edit tree traversal
    if edit_started:
        if pin_verified:
            if trait_selected:
                if trait_selected != "3":
                    request.session[characteristics[trait_selected][0]] = message_body
                    request.session["edit_started"] = False
                    request.session["pin_verified"] = False
                    request.session["trait_selected"] = False
                    message = "Change successful."
                    resp.sms(message)
                else:
                    if len(message_body) == 4 and message_body.isnumeric():
                        request.session['pin'] = message_body
                        request.session["edit_started"] = False
                        request.session["pin_verified"] = False
                        request.session["trait_selected"] = False
                        message = "Change successful."
                        resp.sms(message)
                    else:
                        message = "Sorry, that's not a valid PIN number."
                        resp.sms(message)
                user_to_change = Customer.objects.filter(phone_number=request.POST.get('From', None)[2:])[0]
                user_to_change.first_name = request.session['first_name']
                user_to_change.last_name = request.session['last_name']
                user_to_change.pin = request.session['pin']
                user_to_change.save()
            else:
                
                if message_body in characteristics:
                    trait_selected = message_body
                    request.session['trait_selected'] = message_body
                    message = "What would you like to change your %s to?" % characteristics[trait_selected][1]
                    resp.sms(message)
                elif message_body.upper() == "LEAVE":
                    request.session['edit_started'] = False
                    request.session['pin_verified'] = False
                    request.session['trait_selected'] = False
                    message = "Edit cancelled!"
                    resp.sms(message)
                else:
                    message = "Sorry, please enter a valid option.\n1. First name\n2. Last name\n3. Pin"
                    resp.sms(message)
        else:
            if message_body.upper() == "LEAVE":
                request.session['edit_started'] = False
                request.session['pin_verified'] = False
                request.session['trait_selected'] = False
                message = "Edit cancelled!"
                resp.sms(message)
            elif message_body == request.session['pin']:
                request.session['pin_verified'] = True
                message = "Please reply with the number of the item you'd like to edit:\n1. First name\n2. Last name\n3. Pin"
                resp.sms(message)
            else:
                message = "Sorry, that's not the right pin."
                resp.sms(message)
    else:
        message = "Please enter your pin to make changes. Enter LEAVE at any time to cancel."
        request.session['edit_started'] = True
        resp.sms(message)
    # Return TwiML
    return str(resp)

@twilio_view
def balance(request):
    # Create TwiML response
    resp = twilio.twiml.Response()
    try:
        this_customer = Customer.objects.get(phone_number=request.POST.get('From', '')[2:])
    except:
        message = "Please register to use this feature!"
        request.session['payment_request'] = False
        request.session['pending_payment'] = False
        resp.sms(message)
        return str(resp)
    try:
        # String with user information
        user_number = request.POST.get('From', None)[2:]
        user = Customer.objects.get(phone_number=user_number)
        message = "Your balance is $%.2f." % get_balance(user)
    except:
        message = "Please text SIGNUP to access your balance."
    resp.sms(message)
    # Return TwiML
    return str(resp)

@twilio_view
def pay(request):
    resp = twilio.twiml.Response()
    # Check if user is authorized
    try:
        this_customer = Customer.objects.get(phone_number=request.POST.get('From', '')[2:])
    except:
        message = "Please register to use this feature!"
        request.session['payment_request'] = False
        request.session['pending_payment'] = False
        resp.sms(message)
        return str(resp)
    message_body = request.POST.get('Body', '')
    payment_request = message_body.split(" ")
    pending_payment = request.session.get('pending_payment', False)
    if pending_payment:
        if message_body.upper() == "LEAVE":
                request.session['payment_request'] = False
                request.session['pending_payment'] = False
                message = "Payment cancelled!"
                resp.sms(message)
                return str(resp)
        if message_body == this_customer.pin:
            if get_balance(this_customer) >= float(pending_payment[1]):
                # Check if other user has an account

                if Customer.objects.filter(phone_number=pending_payment[0]).count() == 1:
                    other_customer = Customer.objects.get(phone_number=pending_payment[0])
                    success = transfer_balance(this_customer, other_customer, pending_payment[1])
                    message = "You've successfully transferred $%s to %s.\nAfter processing, your balance will be $%.2f." % (pending_payment[1], other_customer.first_name, float(get_balance(this_customer)) - float(pending_payment[1]))
                    resp.sms(message)

                    message = client.messages.create(body="%s %s (%s) just sent you $%s using PayWithText. After processing, your balance will be $%.2f." % (this_customer.first_name, this_customer.last_name, this_customer.phone_number, pending_payment[1], float(get_balance(other_customer)) + float(pending_payment[1])), to="+1%s" % other_customer.phone_number, from_="+15126663017")
                    print(message.sid)
                    request.session['payment_request'] = False
                    request.session['pending_payment'] = False
                else:
                    message = "%s isn't a member yet. We've sent them an invitation for you!" % pending_payment[0]
                    resp.sms(message)
                    message = client.messages.create(body="Your friend %s %s (%s) wants to send you $%s using PayWithText. Reply SIGNUP to claim it!" % (this_customer.first_name, this_customer.last_name, this_customer.phone_number, pending_payment[1]), to="+1%s" % pending_payment[0], from_="+15126663017")
                    request.session['payment_request'] = False
                    request.session['pending_payment'] = False
            else:
                message = "You have insufficient funds for this payment."
                resp.sms(message)
                request.session['payment_request'] = False
                request.session['pending_payment'] = False
        else:
            message = "Invalid pin - please try again.\nSend LEAVE to exit this prompt at any time."
            resp.sms(message)
    else:
        if len(payment_request) == 3 and len(payment_request[1]) == 10 and payment_request[1].isnumeric() and is_float(payment_request[2]):
            request.session['pending_payment'] = message_body.split(" ")[1:]
            message = "Please enter your pin to transfer money, or send LEAVE to cancel."
            resp.sms(message)
        elif message_body.upper() == "LEAVE":
            request.session['payment_request'] = False
            request.session['pending_payment'] = False
            message = "Edit cancelled!"
            resp.sms(message)
        else: 
            message = "Usage:\nPAY [10-digit phone number, no spaces] [amount, no dollar sign]"
            resp.sms(message)
    return str(resp)

@twilio_view
def req(request):
    resp = twilio.twiml.Response()
    try:
        this_customer = Customer.objects.get(phone_number=request.POST.get('From', '')[2:])
    except:
        message = "Please register to use this feature!"
        request.session['payment_request'] = False
        request.session['pending_payment'] = False
        resp.sms(message)
        return str(resp)
    
    message_body = request.POST.get('Body', '')
    payment_request = message_body.split(" ")

    if len(payment_request) == 3 and len(payment_request[1]) == 10 and payment_request[1].isnumeric() and is_float(payment_request[2]):
        if Customer.objects.filter(phone_number=payment_request[1]).count() == 1:
            other_customer = Customer.objects.filter(phone_number=payment_request[1])[0]
            resp.sms("We sent %s %s (%s) your request. You'll be notified if they approve or deny it!" % (other_customer.first_name, other_customer.last_name, other_customer.phone_number))
            message = client.messages.create(body="Your friend %s %s (%s) has requested $%s from you using PayWithText. Type PAYREQUEST to view your requests." % (this_customer.first_name, this_customer.last_name, this_customer.phone_number, payment_request[2]), to="+1%s" % other_customer.phone_number, from_="+15126663017")
            outstanding_requests.objects.create(issuer=this_customer, debtor=other_customer, amount=payment_request[2]).save()
        else:
            resp.sms("%s isn't a member yet. We sent them an invitation for you!")
            message = client.messages.create(body="Your friend %s %s (%s) has requested $%s from you using PayWithText. Reply SIGNUP to start using the service! (Don't worry, we won't charge you right away)" % (this_customer.first_name, this_customer.last_name, this_customer.phone_number, payment_request[2]), to="+1%s" % payment_request[1], from_="+15126663017")
    else:
        resp.sms("Usage:\nREQUEST [10-digit phone number, no spaces] [amount, no dollar sign]")
    
    return str(resp)

@twilio_view
def payrequest(request):
    resp = twilio.twiml.Response()
    try:
        this_customer = Customer.objects.get(phone_number=request.POST.get('From', '')[2:])
    except:
        message = "Please register to use this feature!"
        request.session['payment_request'] = False
        request.session['pending_payment'] = False
        resp.sms(message)
        return str(resp)
    requests = outstanding_requests.objects.filter(debtor=this_customer)
    message_body = request.POST.get('Body', '')
    message_parsed = message_body.split(" ")
    print(message_body, message_parsed)
    request_made = request.session.get('request_made', False)
    if request_made:
        print(str(message_body), str(this_customer.pin))
        if str(message_body) == str(this_customer.pin):
            this_request = outstanding_requests.objects.filter(debtor=this_customer)[int(request_made[1])]
            if request_made[2].upper() == 'APPROVE':
                if get_balance(this_customer) >= this_request.amount:
                    transfer_balance(this_customer, this_request.issuer, this_request.amount)
                    resp.sms("You paid %s %s (%s) $%s.\nAfter processing, your balance will be $%.2f." % (this_request.issuer.first_name, this_request.issuer.last_name, this_request.issuer.phone_number, this_request.amount, float(get_balance(this_customer)) - float(this_request.amount)))
                    message = client.messages.create(body="Your friend %s %s (%s) completed your request for $%s.\nAfter processing, your balance will be $%s." % (this_customer.first_name, this_customer.last_name, this_customer.phone_number, this_request.amount, float(get_balance(this_request.issuer)) + float(this_request.amount)), to="+1%s" % this_request.issuer.phone_number, from_="+15126663017")
                    this_request.delete()
                else:
                    resp.sms("Your balance ($%s) is not high enough to complete this request ($%.2f)." % (get_balance(this_customer), this_request.amount))
            else:
                resp.sms("You denied %s %s (%s)'s request." % (this_request.issuer.first_name, this_request.issuer.last_name, this_request.issuer.phone_number))
                message = client.messages.create(body="Your friend %s %s (%s) denied your request for $%s." % (this_customer.first_name, this_customer.last_name, this_customer.phone_number, this_request.amount), to="+1%s" % this_request.issuer.phone_number, from_="+15126663017")
                this_request.delete()
            request.session['request_made'] = False
        elif message_body.upper() == "LEAVE":
            resp.sms("You've left the PAYREQUEST prompt!")
            request.session['request_made'] = False
        else:
            resp.sms("Sorry, that's the wrong pin. Please try again.")
    else:
        if len(message_parsed) == 3:
            if int(message_parsed[1]) >= 0 and int(message_parsed[1]) < len(requests):
                if message_parsed[2].upper() in ["APPROVE", "DENY"]:
                    request.session['request_made'] = message_parsed
                    resp.sms("Please enter your pin.")
        else:
            if requests.count() > 0:
                message = "Requests\n" + "\n".join("%s. %s" % (index, request.show()) for index, request in enumerate(requests)) + "\nPlease select which debts to pay or ignore by sending \"PAYREQUEST INDEX APPROVE/DENY\"." + "\nYou can type LEAVE at any time to exit the prompt."
            else:
                message = "You have no requests! :)"
            resp.sms(message)
    return str(resp)

  

def viewdb(request):
    html = '<br>'.join(Customer.__repr__() for Customer in Customer.objects.all()) + '<hr>' + '<br>'.join(req.__repr__() for req in outstanding_requests.objects.all())
    return HttpResponse(html)




