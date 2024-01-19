from PyQt5.QtWidgets import *
from PyQt5 import uic
import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
class GUI(QMainWindow):
    def __init__(self):
        super(GUI, self).__init__()
        uic.loadUi("gui.ui",self)
        self.show()

        self.loginButton.clicked.connect(self.login)
        self.attachmentButton.clicked.connect(self.attach)
        self.sendButton.clicked.connect(self.send_mail)




    def login(self):
        try:
            #self.server = smtplib.SMTP(self.smtpserverEdit.text(), self.smtpportEdit.text())
           # self.server.ehlo()
           # self.server.starttls()
          #  self.server.ehlo()
          #  self.server.login(self.emailEdit.text(), self.passwordEdit.text())
            
            self.emailEdit.setEnabled(False)
            self.passwordEdit.setEnabled(False)
            self.smtpserverEdit.setEnabled(False)
            self.smtpportEdit.setEnabled(False)
            self.imapserverEdit.setEnabled(False)
            self.imapportEdit.setEnabled(False)


            self.toEdit.setEnabled(True)
            self.subjectEdit.setEnabled(True)
            self.textEdit.setEnabled(True)
            self.sendButton.setEnabled(True)
            self.attachmentButton.setEnabled(True)
            self.inboxView.setEnabled(True)

            self.msg = MIMEMultipart()
        except smtplib.SMTPAuthenticationError:
            message_box = QMessageBox()
            message_box.setText("Błędne dane logowania!")
            message_box.exec()
        except:
            message_box = QMessageBox()
            message_box.setText("Logowanie zakończone niepowodzeniem")
            message_box.exec()
    def attach(self):
        options = QFileDialog.Options()
        filenames,_ = QFileDialog.getOpenFileNames(self,"Open File","","All files (*.*)")
        if filenames != []:
            for filename in filenames:
                attachment = open(filename, 'rb')
                filename = filename[filename.rfind("/") + 1:]
                p = MIMEBase('application', 'octet-stream')
                p.set_payload(attachment.read())
                encoders.encode_base64(p)
                p.add_header("Content-Disposition", f"attachment; filename={filename}")
                self.msg.attach(p)
                if not self.attachmentLabel.text().endswith(": "):
                    self.attachmentLabel.setText(self.attachmentLabel.text() + ",")
                self.attachmentLabel.setText(self.attachmentLabel.text() + " " + filename)
    def send_mail(self):
        dialog = QMessageBox()
        dialog.setTest("Czy na pewno chcesz wysłać tą wiadomość?")
        dialog.addButton(QPushButton("Tak"), QMessageBox.YesRole) #0
        dialog.addButton(QPushButton("Nie"), QMessageBox.NoRole) #1
        if dialog.exec_() == 0:
            try:
                self.msg['From'] = "jakis ziomek"
                self.msg['To'] = self.toEdit.text()
                self.msg['Subject'] = self.subjectEdit.text()
                self.msg.attach(MIMEText(self.textEdit.toPlainText(),'plain'))
                text = self.msg.as_string()
                self.server.sendmail(self.lineEdit.text(),self.lineEdit_5.text(),text)
                message_box = QMessageBox()
                message_box.setText("Wiadomosc wysłana")
                message_box.exec()
            except:
                message_box = QMessageBox()
                message_box.setText("Wysyłanie zakończono niepowodzeinem")
                message_box.exec()

app = QApplication([])
window = GUI()
app.exec_()