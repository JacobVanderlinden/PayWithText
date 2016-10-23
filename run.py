# Imports

from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, request, redirect, session
import twilio.twiml
import os

# Create Flask app
SECRET_KEY = 'PNf624d537ef7e64bd1d7ed64100569af1' #SID
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
#app.config.from_object(__name__)

# Entry point to application

@app.route("/", methods=['GET', 'POST'])
def entry():
    # Get current message and uppercase value of message (in case of keyword)
    message_body = request.values.get('Body').strip()
    message_upper = message_body.upper()
    # Create a twilio response
    resp = twilio.twiml.Response()
    # Check if user is authenticated
    is_authenticated = session.get('is_authenticated', False)
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
        if session.get(state):
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
    return str(resp)

# Signup view
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    # Create Twilio response
    resp = twilio.twiml.Response()
    # Get message body
    message_body = request.values.get('Body').strip()
    # Check for signup states
    signup_started = session.get('signup_started', False)
    pin_requested = session.get('pin_requested', False)
    is_authenticated = session.get('is_authenticated', False)
    first_name_given = session.get('first_name_given', False)
    # Begin signup tree traversal
    if signup_started:
        if first_name_given:
            if pin_requested:
                if len(message_body) == 4 and message_body.isnumeric():
                    session['pin'] = message_body
                    message = "Signup complete! Type CMD for a list of available commands."
                    session['is_authenticated'] = True
                    session['signup_started'] = False
                    resp.sms(message)
                else:
                    message = "Sorry, please send a 4-digit numeric pin."
                    resp.sms(message)
            else:
                session['last_name'] = message_body
                message = "Great. Now, please enter a 4-digit numeric pin we'll use to confirm your payments."
                session['pin_requested'] = True
                resp.sms(message)
        else:
            session['first_name'] = message_body
            session['first_name_given'] = True
            message = "Thanks %s! What's your last name?" % message_body
            resp.sms(message)
    else:
        if is_authenticated:
            message = "Whoops, looks like you've already registered!\nYou can send RESTART to reset your account."
            resp.sms(message)
        else:
            message = "Let's get you signed up! Please reply with your first name."
            session['signup_started'] = True
            resp.sms(message)
    # Return TwiML
    return str(resp)

# View to see current user information. Remove in production, used for debugging
@app.route("/view", methods=["GET", "POST"])
def view():
    # Create TwiML response
    resp = twilio.twiml.Response()
    # String with user information
    message = "Name: %s %s\nPin:%s" % (session['first_name'], session['last_name'], session['pin'])
    resp.sms(message)
    # Return TwiML
    return str(resp)

# Resets account associated with phone number
# In production, replace middle section by deleting row in DB associated with phone number
@app.route("/restart", methods=["GET", "POST"])
def restart():
    # Create TwiML response
    resp = twilio.twiml.Response()
    # Remove states from signup
    session['is_authenticated'] = False
    session['signup_started'] = False
    session['pin_requested'] = False
    session['first_name_given'] = False
    # Remove user information
    session['first_name'] = None
    session['last_name'] = None
    session['pin'] = None
    # Remove states from edit
    session['edit_started'] = False
    session['pin_confirmed'] = False
    session['trait_selected'] = False
    # Confirm removal
    message = "Your account has been reset. Please respond with SIGNUP to re-register."
    resp.sms(message)
    # Return TwiML
    return str(resp)

# See list of available commands 
@app.route("/cmd", methods=["GET", "POST"])
def cmd():
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
@app.route("/edit", methods=["GET", "POST"])
def edit():
    # Establish response and evaluate message body text
    resp = twilio.twiml.Response()
    message_body = request.values.get('Body').strip()
    # Check for Edit states
    edit_started = session.get('edit_started', False)
    pin_verified = session.get('pin_verified', False)
    trait_selected = session.get('trait_selected', False)
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
                    session[characteristics[trait_selected][0]] = message_body
                    session["edit_started"] = False
                    session["pin_verified"] = False
                    session["trait_selected"] = False
                    message = "Change successful."
                    resp.sms(message)
                else:
                    if len(message_body) == 4 and message_body.isnumeric():
                        session['pin'] = message_body
                        session["edit_started"] = False
                        session["pin_verified"] = False
                        session["trait_selected"] = False
                        message = "Change successful."
                        resp.sms(message)
                    else:
                        message = "Sorry, that's not a valid PIN number."
                        resp.sms(message)
            else:
                
                if message_body in characteristics:
                    trait_selected = message_body
                    session['trait_selected'] = message_body
                    message = "What would you like to change your %s to?" % characteristics[trait_selected][1]
                    resp.sms(message)
                else:
                    message = "Sorry, please enter a valid option.\n1. First name\n2. Last name\n3. Pin"
                    resp.sms(message)
        else:
            if message_body.upper() == "LEAVE":
                session['edit_started'] = False
                session['pin_verified'] = False
                session['trait_selected'] = False
                message = "Edit cancelled!"
                resp.sms(message)
            elif message_body == session['pin']:
                session['pin_verified'] = True
                message = "Please reply with the number of the item you'd like to edit:\n1. First name\n2. Last name\n3. Pin"
                resp.sms(message)
            else:
                message = "Sorry, that's not the right pin. Please try again, or type LEAVE to exit this prompt."
                resp.sms(message)
    else:
        message = "Please enter your pin to make changes."
        session['edit_started'] = True
        resp.sms(message)
    # Return TwiML
    return str(resp)
# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)