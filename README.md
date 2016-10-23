#PayWithText

PayWithText is a simple way to make payments to others using only SMS developed by Ian Mobbs and Jacob Vanderlinden for HackTX 2016. By combining our passion for development and humanitarianism, we decided to do our best to create something that can truly change the world. PayWithText doesn't require any internet - only a cell signal. PayWithText was designed with those who can't afford internet-enabled phones in mind. A simple-to-use text-based interface facilitates trade for anyone with an account.

##Usage

Simply text 512.666.3017 to get started!

##Real world application

This application is a proof of concept. Every user is given a mock account using CapitalOne's Reimagine Banking API, "Nessie", and allocated a random amount of money between $1 and $10,000. It then allows you to pay, request, and receive money from anyone with a cell phone number. By eliminating the need to carry around physical currency, we can help decrease robbery in places where digital currency isn't the norm, but carrying a cell phone is.

##Technology

PayWithText was built using Django, a set of Python web frameworks. We store our information using PostgresSQL and host our application on Heroku. Communication is facilitated by Twilio, and payment processing is done by the Capital One API.

##Authors and Contributors

@IanMobbs and @JacobVanderlinden - Authors