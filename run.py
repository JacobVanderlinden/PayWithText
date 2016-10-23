from flask import Flask, request, redirect, session
import twilio.twiml

SECRET_KEY = 'PNf624d537ef7e64bd1d7ed64100569af1' #SID
app = Flask(__name__)
app.config.from_object(__name__)

@app.route("/", methods=['GET', 'POST'])
def entry():
    message_body = request.values.get('Body').strip()
    message_upper = message_body.upper()
    resp = twilio.twiml.Response()
    is_authenticated = session.get('is_authenticated', False)
    keywords = {
        "CMD":"/cmd",
        "SIGNUP":"/signup",
        "EDIT":"/edit",
        "RESTART":"/restart",
        "VIEW":"/view",
        "BALANCE":"/balance",
        "PAY":"/pay",
        "REQUEST":"/request",
    }

    states = {
        "signup_started":"/signup",
        "edit_started":"/edit",
    }

    state_added = False
    for state in states:
        if session.get(state):
            resp.redirect(states[state])
            state_added = True
    if message_upper in keywords and not state_added:
        resp.redirect(keywords[message_upper])
    elif not state_added:
        if is_authenticated:
            resp.sms("Welcome to PayWithText! Send CMD for a list of commands.")
        else:
            resp.sms("Welcome to PayWithText! Respond SIGNUP to start using our service.")
    
    return str(resp)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    resp = twilio.twiml.Response()
    message_body = request.values.get('Body').strip()

    signup_started = session.get('signup_started', False)
    pin_requested = session.get('pin_requested', False)
    is_authenticated = session.get('is_authenticated', False)
    first_name_given = session.get('first_name_given', False)
    
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
    
    return str(resp)

@app.route("/view", methods=["GET", "POST"])
def view():
    resp = twilio.twiml.Response()
    message = "Name: %s %s\nPin:%s" % (session['first_name'], session['last_name'], session['pin'])
    resp.sms(message)
    return str(resp)

@app.route("/restart", methods=["GET", "POST"])
def restart():
    resp = twilio.twiml.Response()

    session['is_authenticated'] = False
    session['signup_started'] = False
    session['pin_requested'] = False
    session['first_name_given'] = False
    
    session['first_name'] = None
    session['last_name'] = None
    session['pin'] = None
    
    session['edit_started'] = False
    session['pin_confirmed'] = False
    session['trait_selected'] = False
    message = "Your account has been reset. Please respond with SIGNUP to re-register."
    resp.sms(message)
    return str(resp)

@app.route("/cmd", methods=["GET", "POST"])
def cmd():
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
    return str(resp)

@app.route("/edit", methods=["GET", "POST"])
def edit():
    resp = twilio.twiml.Response()
    message_body = request.values.get('Body').strip()

    edit_started = session.get('edit_started', False)
    pin_verified = session.get('pin_verified', False)
    trait_selected = session.get('trait_selected', False)

    characteristics = {
        "1":["first_name", "first name"],
        "2":["last_name", "last name"],
        "3":["pin", "pin"],
    }

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
    return str(resp)


if __name__ == "__main__":
    app.run(debug=True)