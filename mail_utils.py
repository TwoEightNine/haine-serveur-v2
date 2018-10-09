import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from secret import PASSWORD
from mail_templates import *

SMTP_HOST = 'smtp.bk.ru'
SMTP_PORT = 25
EMAIL = "haine.officielle@bk.ru"
SUBJECT = "Haine Messenger"
ACTIVATION_LINK = "localhost:1753/activate?code=%s"


class MailServer:

    server = None

    def __init__(self):
        self.server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        self.server.starttls()
        self.server.login(EMAIL, PASSWORD)

    def send_code(self, email, code):
        link = ACTIVATION_LINK % code
        self.__send(email, MESSAGE_CODE % (link, link), MESSAGE_CODE_PLAIN % (link, link), "code " + code)

    def send_password(self, email, password):
        self.__send(email, MESSAGE_PASSWORD % password, MESSAGE_PASSWORD_PLAIN % password, "password " + password)

    def __send(self, email, html, plain, tag=""):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = SUBJECT
        msg['From'] = EMAIL
        msg['To'] = email
        msg.attach(MIMEText(plain, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        print("Sending", tag, "to", email)
        self.server.sendmail(EMAIL, email, msg.as_string())

    def __del__(self):
        self.server.quit()

