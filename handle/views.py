from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import twilio.twiml
from models import Customer
from django.http.response import HttpResponse
from django_twilio.decorators import twilio_view

# Create your views here.
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
    }
    # States user can be in that require redirect
    states = {
        "signup_started":"/signup",
        "edit_started":"/edit",
    }
    # Check if user is in states established above
    state_added = False
    for state in states:
        if request.session.get(state):
            resp.redirect(states[state])
            state_added = True
    # Check if user sent keyword
    if message_upper in keywords and not state_added:
        resp.redirect(keywords[message_upper])
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
                    new_user.save()
                    
                    message = "Signup complete! Type CMD for a list of available commands."
                    request.session['is_authenticated'] = True
                    request.session['signup_started'] = False
                    resp.sms(message)
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
    # String with user information
    user_number = request.POST.get('From', None)[2:]
    print(user_number)
    print(Customer.objects.all())
    user_list = Customer.objects.filter(phone_number=user_number)
    if len(user_list) == 1:
        user = user_list[0]
        message = "First name: %s\nLast name: %s\nPhone number: %s\nPin: %s" % (user.first_name, user.last_name, user.phone_number, user.pin)
    else:
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
    # Removing row from database
    try:
        Customer.objects.filter(phone_number=request.POST.get('From', None)[2:]).delete()
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
                message = "Sorry, that's not the right pin. Please try again, or type LEAVE to exit this prompt."
                resp.sms(message)
    else:
        message = "Please enter your pin to make changes."
        request.session['edit_started'] = True
        resp.sms(message)
    # Return TwiML
    return str(resp)