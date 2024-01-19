import imaplib
import smtplib
from email import message_from_bytes
from email.mime.text import MIMEText


class EmailClient:
    def __init__(self, email_address, password,smtp_server, imap_server, smtp_port, imap_port):
        self.email_address = email_address
        self.password = password
        self.smtp_port = smtp_port
        self.smtp_server = smtp_server
        self.imap_port = imap_port
        self.imap_server = imap_server
        self.imap = imaplib.IMAP4_SSL(self.imap_server ,self.imap_port)
        self.smtp = smtplib.SMTP_SSL(self.smtp_server,self.smtp_port)
    def login_imap(self):
        try:
            response, _ = self.imap.login(self.email_address, self.password)
            if response == 'OK':
                print("Logowanie powiodło się.")
                self.imap.select("Sent")
                _, msgnums = self.imap.search(None, "ALL")
                for msgnum in msgnums[0].split():
                    _, data = self.imap.fetch(msgnum, "(RFC822)")
                    message = message_from_bytes(data[0][1])
                    print(f"Message Number: {msgnum}")
                    print(f"From: {message.get('From')}")
                    print(f"To: {message.get('To')}")
                    print(f"BBC: {message.get('BCC')}")
                    print(f"Date: {message.get('Date')}")
                    print(f"Subject: {message.get('Subject')}")
                    print("Content:")
                    for part in message.walk():
                        if part.get_content_type() == "text/plain":
                            print(part.as_string())
            else:
                print("Logowanie nie powiodło się.")
            self.imap.logout()
        except imaplib.IMAP4.error as e:
            print(f"Błąd logowania: {e}")
    def send_email(self, body ='Email Body', subject='Hello World', to_emails=None):
        
        

if __name__ == "__main__":
    client = EmailClient("busprojekt1@op.pl","Busowehaslo123", "smtp.poczta.onet.pl","imap.poczta.onet.pl",465,993)
    print("siema")
    #client.login_imap()
    client.send_email()