import imaplib
import time
import os
from PyQt5.QtWidgets import *
from PyQt5 import uic
import smtplib
from email import encoders, message_from_bytes
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart




class GUI(QMainWindow):
    def __init__(self):
        super(GUI, self).__init__()
        uic.loadUi("gui.ui",self)
        self.show()
        self.messages = []
        self.wholemessages = []
        self.loginButton.clicked.connect(self.login)
        self.attachmentButton.clicked.connect(self.attach)
        self.sendButton.clicked.connect(self.send_mail)
        self.mailButton.clicked.connect(self.get_inbox)
        self.readButton.clicked.connect(self.read_mail)
        self.inboxTable.setColumnWidth(0,50)
        self.inboxTable.setColumnWidth(1,234)
        self.inboxTable.setColumnWidth(2,320)
        self.inboxTable.setColumnWidth(3,175)
 
    def login(self):
        try:
            self.smtpserver = smtplib.SMTP_SSL(self.smtpserverEdit.text(), self.smtpportEdit.text())
            #self.smtpserver.ehlo()
            #self.smtpserver.starttls()
            #self.smtpserver.ehlo()
            self.smtpserver.login(self.emailEdit.text(), self.passwordEdit.text())
            self.imapserver = imaplib.IMAP4_SSL(self.imapserverEdit.text(), self.imapportEdit.text())
            self.imapserver.login(self.emailEdit.text(), self.passwordEdit.text())

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
            self.inboxTable.setEnabled(True)      
            self.mailButton.setEnabled(True)


            self.msg = MIMEMultipart()
        except smtplib.SMTPAuthenticationError:
            message_box = QMessageBox()
            message_box.setText("Błędne dane logowania!")
            message_box.exec()
        except Exception as e:
            message_box = QMessageBox()
            message_box.setText("Logowanie zakończone niepowodzeniem")
            print(e)
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
        dialog.setText("Czy na pewno chcesz wysłać tą wiadomość?")
        dialog.addButton(QPushButton("Tak"), QMessageBox.YesRole) #0
        dialog.addButton(QPushButton("Nie"), QMessageBox.NoRole) #1
        if dialog.exec_() == 0:
            try:
                self.msg['From'] = self.emailEdit.text()
                self.msg['To'] = self.toEdit.text()
                self.msg['Subject'] = self.subjectEdit.text()
                self.msg.attach(MIMEText(self.textEdit.toPlainText(),'plain'))
                text = self.msg.as_string()
                self.smtpserver.sendmail(self.emailEdit.text(),self.toEdit.text(),text)
                message_box = QMessageBox()
                message_box.setText("Wiadomosc wysłana")
                message_box.exec()
            except Exception as e:
                message_box = QMessageBox()
                message_box.setText("Wysyłanie zakończono niepowodzeinem")
                print(e)
                message_box.exec()
    def get_inbox(self):
        try:
            row = 0
            self.messages = []
            self.wholemessages = []
            self.imapserver.select("inbox")
            _, msgnums = self.imapserver.search(None, "ALL")
            for msgnum in msgnums[0].split():
                _, data = self.imapserver.fetch(msgnum, "(RFC822)")
                message = message_from_bytes(data[0][1])
                self.wholemessages.append(message)
                self.inboxTable.setRowCount(row+1)
                self.inboxTable.setItem(row, 0, QTableWidgetItem(str(row+1)))
                self.inboxTable.setItem(row, 1, QTableWidgetItem(str(message.get('From'))))
                self.inboxTable.setItem(row, 2, QTableWidgetItem(str(message.get('Subject'))))
                self.inboxTable.setItem(row, 3, QTableWidgetItem(str(message.get('Date'))))
                row = row + 1
                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        content = part.as_string()
                        break
                messagedata = {'Nr': row+1, 'Od': str(message.get('From')), 'Do': str(message.get('To')), 'Data': str(message.get('Date')), 'Temat': str(message.get('Subject')), 'Tresc': content}
                self.messages.append(messagedata)        
            self.imapserver.logout()
            time.sleep(1)
            self.imapserver = imaplib.IMAP4_SSL(self.imapserverEdit.text(), self.imapportEdit.text())
            self.imapserver.login(self.emailEdit.text(), self.passwordEdit.text())
            self.readButton.setEnabled(True)
        except Exception as e :
            print(e)

    def read_mail(self):
        try:
            selectedItems = self.inboxTable.selectedItems()
            if selectedItems:
                firstSelectedItem = selectedItems[0]
                selectedRow = firstSelectedItem.row()

            rowData = []
            for column in range(self.inboxTable.columnCount()):
                item = self.inboxTable.item(selectedRow, column)
                if item is not None:
                    rowData.append(item.text())
                else:
                    rowData.append("")
            self.mailnumber = int(rowData[0])
            #print(self.mailnumber)
            dialog = QDialog()
            uic.loadUi("mail.ui",dialog)
            tresc = self.messages[self.mailnumber-1]['Tresc']
            tresc = tresc.split("\n\n", 1)[1]
            filename = ""
            for part in self.wholemessages[self.mailnumber-1].walk():
                if part.get_content_maintype() == 'multipart':
                    continue

                # Znajdowanie załączników
                if part.get('Content-Disposition') is None:
                    continue

                filename = filename + part.get_filename() + ", "
                print(filename)
            if filename.endswith(", "):
                filename = filename[:-2]
            if filename == "": 
                dialog.dowloadButton.setEnabled(False)
            dialog.attachmentLabel.setText(dialog.attachmentLabel.text() + filename)
            dialog.dowloadButton.clicked.connect(self.download_attachment)
            dialog.fromLine.setText(self.messages[self.mailnumber-1]['Od'])
            dialog.dateLine.setText(self.messages[self.mailnumber-1]['Data'])
            dialog.subjectLine.setText(self.messages[self.mailnumber-1]['Temat'])
            dialog.contentBox.setText(tresc)
            dialog.exec()
        except Exception as e:
            print(e)
    def download_attachment(self):
        try:
            
            message = self.wholemessages[self.mailnumber-1]
            #print(message)
            for part in message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue

                # Znajdowanie załączników
                if part.get('Content-Disposition') is None:
                    continue

                nazwa_pliku = part.get_filename()
                if bool(nazwa_pliku):
                    # Dekodowanie i zapisywanie załącznika
                    zawartosc = part.get_payload(decode=True)
                    path = os.path.dirname(os.path.abspath(__file__))
                    #print(path)
                    sciezka = path +"\\attachments\\" + nazwa_pliku
                    #print(sciezka)
                    if not os.path.exists(path +"\\attachments\\"):
                        os.makedirs(path +"\\attachments\\")
                    with open(sciezka, 'wb') as f:
                        f.write(zawartosc)
            message_box = QMessageBox()
            message_box.setText("Pomyślnie pobrano załącznik")
            message_box.exec()
        except Exception as e:
            message_box = QMessageBox()
            message_box.setText("Błąd przy pobieraniu załącznika")
            print(e)
            message_box.exec()
app = QApplication([])
window = GUI()
app.exec_()