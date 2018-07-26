import os
import shutil
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from collections import namedtuple
SENDER_EMAIL_CREDENTIALS = 'email_credentials.txt'

# Convert to absolute file paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
SENDER_EMAIL_CREDENTIALS = SENDER_EMAIL_CREDENTIALS\
                        if os.path.isabs(SENDER_EMAIL_CREDENTIALS)\
                        else os.path.join(DIR_PATH, SENDER_EMAIL_CREDENTIALS)

def send_email(subject, msg, destination_emails):
    try:
        email = Email()
        email.login(SENDER_EMAIL_CREDENTIALS)
        email.send_mail(destination_emails, msg, subject)
        email.print_log()
        email.close()
    except Exception as e:
        print('Email failed to send!')
        print('subject, msg, destination_emails')
        print([subject, msg, destination_emails])
        print(str(e))

class Email:
    def __init__(self):
        print('Initializing email server')
        self.server = smtplib.SMTP('smtp.gmail.com', 587)
        self.sent_mail = []
        self.Mail = namedtuple('SentMail', ['sender', 'destination', 'message'])

    def login(self, email_credentials):
        '''
        Email credentials file should look like this:
        email@address.com
        password
        '''
        print('Logging into email: ', end='')
        self.server.starttls()
        with open(email_credentials, 'r') as f:
            self.sender_email, sender_pswd = f.read().splitlines()[:2]
            self.server.login(self.sender_email, sender_pswd)

    def send_mail(self, destination_emails, msg, subject, attachment=''):
        print('Sending mail')
        email = MIMEMultipart()
        email['From'] = self.sender_email
        email['To'] = ', '.join(destination_emails)
        email['Subject'] = subject
        email.attach(MIMEText(msg, 'html'))

        if attachment:
            zf = open(attachment, 'rb')
            email_file = MIMEBase('application', 'zip')
            email_file.set_payload(zf.read())
            encoders.encode_base64(email_file)
            email_file.add_header('Content-Disposition', 'attachment',
                                filename=attachment)
            email.attach(email_file)

        email_args = self.sender_email, destination_emails, email.as_string()
        self.server.sendmail(*email_args)
        self.sent_mail.append(self.Mail(*email_args))

    def print_log(self):
        with open('email.log', 'w') as f:
            sep = '-' * 15
            for email in self.sent_mail:
                f.write('\n'+sep+'\n'.join(['%s' % e for e in email]))

    def close(self):
        self.server.quit()
