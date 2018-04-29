import smtplib
from secret import PASSWORD

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL = ""
ACTIVATION_LINK = "localhost:1753/activate?code=%s"

MESSAGE_CODE = """You have successfully signed up!
For activating your account open this link: %s"""

MESSAGE_PASSWORD = """You have requested a new password and there is:
%s
Do not forget it again!"""


class MailServer:

    server = None

    def __init__(self):
        self.server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        self.server.starttls()
        self.server.login(EMAIL, PASSWORD)

    def send_code(self, email, code):
        link = ACTIVATION_LINK % code
        self.server.sendmail(EMAIL, email, MESSAGE_CODE % link)

    def send_password(self, email, password):
        self.server.sendmail(EMAIL, email, MESSAGE_PASSWORD % password)

    def __del__(self):
        self.server.quit()
