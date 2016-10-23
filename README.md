#PayWithText

PayWithText is a simple way to make payments to others using only SMS. Only 37% of people in emerging economies have smartphones(Pew Research Center). By enabling peer-to-peer commerce over SMS, we hope to help increase trade in emerging economies.

PayWithText doesn't require any internet - only a cell signal. It was designed with those who can't afford internet-enabled phones in mind by Ian Mobbs and Jacob Vanderlinden for HackTX 2016.

##Usage

Text (512) 666-3017 to get started!
Commands
  * EDIT - Edit your profile
  * RESTART - Reset all your information
  * BALANCE - Check your balance
  * PAY - Create a payment
  * REQUEST - Request a payment
  * PAYREQUEST - Approve/deny a request
  * VIEW - View your information

##Real world application

This application is a proof of concept. Every user is given a mock account using CapitalOne's Reimagine Banking API, "Nessie", and allocated a random amount of money between $1 and $10,000. It then allows you to pay, request, and receive money from anyone with a cell phone number. By eliminating the need to carry around physical currency, we can boost the economy and bring new technologies to places where digital currency isn't the norm, but carrying a cell phone is.

##Technology

PayWithText was built using Django, a set of Python web frameworks. We store our information using PostgresSQL and host our application on Heroku. Communication is facilitated by Twilio, and payment processing is done by the Capital One API.

##Authors and Contributors

@IanMobbs and @JacobVanderlinden - Authors