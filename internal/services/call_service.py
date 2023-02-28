import os
from dotenv import load_dotenv
load_dotenv()

from twilio.rest import Client

def demo():
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    from_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    to_phone_number = os.getenv('MY_PHONE_NUMBER')

    client = Client(account_sid, auth_token)

    message = client.calls.create(
        to=to_phone_number,
        from_=from_phone_number,
        url='http://demo.twilio.com/docs/voice.xml'
    )

    print(message.sid)

if __name__ == '__main__':
    demo()
