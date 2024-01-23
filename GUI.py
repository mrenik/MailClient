import imaplib
import time
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5 import uic
import smtplib
from email import encoders, message_from_bytes
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

from PgpBus import PgpBus

class GUI(QMainWindow):

    def __init__(self):
        super(GUI, self).__init__()
        uic.loadUi("gui.ui", self)
        self.show()
        self.messages = []
        self.wholemessages = []
        self.loginButton.clicked.connect(self.login)
        self.attachmentButton.clicked.connect(self.attach)
        self.sendButton.clicked.connect(self.send_mail)
        self.mailButton.clicked.connect(self.get_inbox)
        self.readButton.clicked.connect(self.read_mail)
        self.setWindowTitle("MailClient")

        self.inboxTable.setColumnWidth(0,50)
        self.inboxTable.setColumnWidth(1,234)
        self.inboxTable.setColumnWidth(2,320)
        self.inboxTable.setColumnWidth(3,175)

        self.keyGenFormButton.clicked.connect(self.show_gen_form)
        self.keyImportFormButton.clicked.connect(self.show_import_form)
        self.keyListButton.clicked.connect(self.select_all)
        self.keySelectPrivButton.clicked.connect(self.select_priv)
        self.keySelectPubButton.clicked.connect(self.select_pub)
        self.signBox.stateChanged.connect(self.modify_msg)
        self.encryptBox.stateChanged.connect(self.modify_msg)

        self.listPriv.hide()
        self.listPriv.itemSelectionChanged.connect(self.selected_priv)
        self.listPub.hide()
        self.listPub.itemSelectionChanged.connect(self.selected_pub)
        self.listKeys.hide()
        self.listKeys.itemSelectionChanged.connect(self.selected_all)

        self.gpg = PgpBus()
        self.lock_original_msg = False
    def login(self):
        try:
            self.smtpserver = smtplib.SMTP_SSL(self.smtpserverEdit.text(), self.smtpportEdit.text())
            # self.smtpserver.ehlo()
            # self.smtpserver.starttls()
            # self.smtpserver.ehlo()
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
            self.keySelectPrivButton.setEnabled(True)
            self.keySelectPubButton.setEnabled(True)
            self.passwordEditPriv.setEnabled(True)
            self.keyGenFormButton.setEnabled(True)
            self.keyImportFormButton.setEnabled(True)
            self.keyListButton.setEnabled(True)


            self.msg = MIMEMultipart()
        except smtplib.SMTPAuthenticationError:
            message_box = QMessageBox()
            message_box.setWindowTitle("Błąd")
            message_box.setText("Błędne dane logowania!")
            message_box.exec()
        except:
            message_box = QMessageBox()
            message_box.setWindowTitle("Błąd")
            message_box.setText("Logowanie zakończone niepowodzeniem!")
            message_box.exec()

    def attach(self):
        options = QFileDialog.Options()
        filenames, _ = QFileDialog.getOpenFileNames(self, "Open File", "", "All files (*.*)")
        if filenames != []:
            for filename in filenames:
                extension = ''
                if self.encryptBox.isChecked():
                    encrypted_file = self.gpg.encrypt_file(filename, self.current_key_priv)
                    extension = '.pgp'
                attachment = open(filename, 'rb')
                filename = filename[filename.rfind("/") + 1:]
                p = MIMEBase('application', 'octet-stream')
                if self.encryptBox.isChecked():
                    p.set_payload(encrypted_file.data)
                else:
                    p.set_payload(attachment.read())
                # p.set_payload(attachment.read())
                encoders.encode_base64(p)
                p.add_header("Content-Disposition", f"attachment; filename={filename}{extension}")
                # p.add_header("Content-Disposition", f"attachment; filename={filename}")
                self.msg.attach(p)
                if not self.attachmentLabel.text().endswith(": "):
                    self.attachmentLabel.setText(self.attachmentLabel.text() + ",")
                self.attachmentLabel.setText(self.attachmentLabel.text() + " " + filename)

    def send_mail(self):
        dialog = QMessageBox()
        dialog.setText("Czy na pewno chcesz wysłać tą wiadomość?")
        dialog.addButton(QPushButton("Tak"), QMessageBox.YesRole)  # 0
        dialog.addButton(QPushButton("Nie"), QMessageBox.NoRole)  # 1
        if dialog.exec_() == 0:
            try:
                # clear last msg
                self.msg = MIMEMultipart()
                self.msg['From'] = self.emailEdit.text()
                self.msg['To'] = self.toEdit.text()
                self.msg['Subject'] = self.subjectEdit.text()
                self.msg.attach(MIMEText(self.textEdit.toPlainText(), 'plain'))
                text = self.msg.as_string()
                self.smtpserver.sendmail(self.emailEdit.text(), self.toEdit.text(), text)
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
                self.inboxTable.setRowCount(row + 1)
                self.inboxTable.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                self.inboxTable.setItem(row, 1, QTableWidgetItem(str(message.get('From'))))
                self.inboxTable.setItem(row, 2, QTableWidgetItem(str(message.get('Subject'))))
                self.inboxTable.setItem(row, 3, QTableWidgetItem(str(message.get('Date'))))
                row = row + 1
                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        content = part.as_string()
                        break
                messagedata = {'Nr': row + 1, 'Od': str(message.get('From')), 'Do': str(message.get('To')),
                               'Data': str(message.get('Date')), 'Temat': str(message.get('Subject')), 'Tresc': content}
                self.messages.append(messagedata)
            self.imapserver.logout()
            time.sleep(1)
            self.imapserver = imaplib.IMAP4_SSL(self.imapserverEdit.text(), self.imapportEdit.text())
            self.imapserver.login(self.emailEdit.text(), self.passwordEdit.text())
            self.readButton.setEnabled(True)
        except Exception as e:
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
            # print(self.messages[int(mailnumber) - 1]['Tresc'])
            dialog = QDialog()

            uic.loadUi("mail.ui", dialog)
            tresc = self.messages[self.mailnumber - 1]['Tresc']
            tresc = tresc.split("\n\n", 1)[1]
            self.original_recv_msg = tresc
            filename = ""
            for part in self.wholemessages[self.mailnumber - 1].walk():
                if part.get_content_maintype() == 'multipart':
                    continue

                # Znajdowanie załączników
                if part.get('Content-Disposition') is None:
                    continue

                filename = filename + part.get_filename() + ", "
                #print(filename)
            if filename.endswith(", "):
                filename = filename[:-2]
            if filename == "":
                dialog.dowloadButton.setEnabled(False)
            dialog.setWindowTitle("Wiadomość od: " + self.messages[self.mailnumber - 1]['Od'])
            dialog.attachmentLabel.setText(dialog.attachmentLabel.text() + filename)
            dialog.dowloadButton.clicked.connect(self.download_attachment)
            dialog.fromLine.setText(self.messages[self.mailnumber - 1]['Od'])
            dialog.dateLine.setText(self.messages[self.mailnumber - 1]['Data'])
            dialog.subjectLine.setText(self.messages[self.mailnumber - 1]['Temat'])
            dialog.contentBox.setText(tresc)

            dialog.decryptButton.clicked.connect(self.decrypt_msg)
            self.decrypt_password = dialog.decryptPasswordEdit
            self.verify_sign = dialog.verifyLabel
            self.received_content = dialog.contentBox
            self.verify_sign.setText("Brak uwierzytelnienia")
            self.verify_msg()

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

                    self.decrypt_msg()
                    if nazwa_pliku.endswith("pgp"):
                        nazwa_pliku = nazwa_pliku.rstrip(".pgp")
                        zawartosc = self.gpg.decrypt_message(zawartosc, self.decrypt_password.text()).data
                    #print(path)
                    sciezka = path +"\\attachments\\" + nazwa_pliku
                    #print(sciezka)
                    if not os.path.exists(path +"\\attachments\\"):
                        os.makedirs(path +"\\attachments\\")
                    with open(sciezka, 'wb') as f:
                        f.write(zawartosc)
            message_box = QMessageBox()
            message.setWindowTitle("Pomyślnie pobrano")
            message_box.setText("Pomyślnie pobrano załączniki")
            message_box.exec()
        except Exception as e:
            message_box = QMessageBox()
            message.setWindowTitle("Błąd")
            message_box.setText("Błąd przy pobieraniu załącznika")
            print(e)
            message_box.exec()

    def show_gen_form(self):
        try:
            self.gen_form = QDialog()
            uic.loadUi("key.ui", self.gen_form)
            self.gen_form.setWindowTitle("Wygeneruj nowy klucz")
            self.gen_form.mailEdit.setText(self.emailEdit.text())
            # self.gen_form.mailEdit.setReadOnly(True)
            self.gen_form.keyGenButton.clicked.connect(self.add_key)

            self.gen_form.exec()
        except Exception as e:
            print(e)

    def add_key(self):
        try:
            name_real = self.gen_form.nameEdit.text()
            if name_real == '':
                name_real = None

            new_key = self.gpg.generate_key(
                name_real=name_real,
                name_email=self.gen_form.mailEdit.text(),
                passphrase=self.gen_form.passwordEdit.text(),
                key_type=self.gen_form.typeEdit.text(),
                key_length=int(self.gen_form.sizeEdit.text())
            )


            self.gen_form.fingerprintText.setText(new_key.fingerprint)
            self.gen_form.textKey.setText(self.gpg.gpg.export_keys(str(new_key)))
            print(self.gpg.gpg.export_keys(str(new_key)))
        except Exception as e:
            print(e)

    def show_import_form(self):
        dialog = ImportKeyDialog(self.gpg)
        dialog.setWindowTitle("Importuj klucze")
        dialog.exec_()


    def select_priv(self):
        try:
            self.listPriv.clear()
            keys = self.gpg.get_email_keys(self.emailEdit.text())
            items = [uid + key.get('fingerprint', '')
               for key in keys
               for uid in key.get('uids', [''])]
            self.listPriv.addItems(items)

            item_count = self.listPriv.count()
            # print(item_count)
            if item_count > 0:
                height = min(item_count * self.listPriv.sizeHintForRow(0), 100)
                self.listPriv.setMinimumHeight(height)
                self.listPriv.setMaximumHeight(100)
                self.listPriv.setFixedWidth(500)
                self.listPriv.show()
            # for uid in uids:
            #     print(uid)
        except Exception as e:
            print(e)

    def selected_priv(self):
        try:
            selected = self.listPriv.currentItem()
            id = self.listPriv.row(selected)
            if selected:
                self.keySelectPrivButton.setText(selected.text())
                self.current_key_priv = self.gpg.select_key(self.emailEdit.text(), id)
                self.listPriv.hide()
                self.keySelectPrivButton.setStyleSheet("text-align: left;")
                self.signBox.setEnabled(True)
                # print(self.current_key_priv)
        except Exception as e:
            print(e)

    def select_pub(self):
        try:
            self.listPub.clear()
            keys = self.gpg.get_email_keys(self.toEdit.text())
            items = [uid + key.get('fingerprint', '')
               for key in keys
               for uid in key.get('uids', [''])]
            self.listPub.addItems(items)

            item_count = self.listPub.count()
            # print(item_count)
            if item_count > 0:
                height = min(item_count * self.listPub.sizeHintForRow(0), 100)
                self.listPub.setMinimumHeight(height)
                self.listPub.setMaximumHeight(100)
                self.listPub.setFixedWidth(500)
                self.listPub.show()
            # for uid in uids:
            #     print(uid)
        except Exception as e:
            print(e)

    def selected_pub(self):
        try:
            selected = self.listPub.currentItem()
            id = self.listPub.row(selected)
            if selected:
                self.keySelectPubButton.setText(selected.text())
                self.current_key_pub = self.gpg.select_key(self.toEdit.text(), id)
                self.listPub.hide()
                self.keySelectPubButton.setStyleSheet("text-align: left;")
                self.encryptBox.setEnabled(True)
                # print(self.current_key_pub)
        except Exception as e:
            print(e)

    def select_all(self):
        try:
            self.listKeys.clear()
            keys = self.gpg.gpg.list_keys()
            items = [uid + key.get('fingerprint', '')
                     for key in keys
                     for uid in key.get('uids', [''])]
            self.listKeys.addItems(items)

            item_count = self.listKeys.count()
            # print(item_count)
            if item_count > 0:
                height = min(item_count * self.listKeys.sizeHintForRow(0), 200)
                self.listKeys.setMinimumHeight(height)
                self.listKeys.setMaximumHeight(200)
                self.listKeys.setFixedWidth(500)
                self.listKeys.show()
            # for uid in uids:
            #     print(uid)
        except Exception as e:
            print(e)

    def selected_all(self):
        try:
            selected = self.listKeys.currentItem()
            if selected:
                self.listKeys.hide()
        except Exception as e:
            print(e)
    def modify_msg(self):
        try:
            if self.signBox.isChecked():
                if self.encryptBox.isChecked():
                    # Both
                    sign = self.gpg.sign_message(self.original_send_msg, self.current_key_priv, self.passwordEditPriv.text())
                    msg = self.gpg.encrypt_message(sign.data, self.current_key_pub)
                    self.textEdit.setPlainText(msg.data.decode('utf-8'))
                    # prevent saving changed msg
                    self.lock_original_msg = True

                else:
                    # Sign
                    if not self.lock_original_msg:
                        self.original_send_msg = self.textEdit.toPlainText()
                    # print(self.passwordEditPriv.text())
                    sign = self.gpg.sign_message(self.original_send_msg, self.current_key_priv, self.passwordEditPriv.text())
                    self.textEdit.setPlainText(sign.data.decode('utf-8'))
            else:
                if self.encryptBox.isChecked():
                    # Encrypt
                    if not self.lock_original_msg:
                        self.original_send_msg = self.textEdit.toPlainText()
                    msg = self.gpg.encrypt_message(self.original_send_msg, self.current_key_pub)
                    self.textEdit.setPlainText(msg.data.decode('utf-8'))
                else:
                    # None
                    self.textEdit.setPlainText(self.original_send_msg)
                    self.lock_original_msg = False
        except Exception as e:
            print(e)

    def decrypt_msg(self):
        try:
            # print(self.decrypt_password.text())
            # print(self.verify_sign.text())

            # print(self.original_recv_msg)
            result_crypt = self.gpg.decrypt_message(self.original_recv_msg, self.decrypt_password.text())
            if result_crypt.ok:
                self.received_content.setPlainText(result_crypt.data.decode('utf-8'))
            # print(self.received_content.toPlainText())



            # self.decrypt_password = dialog.decryptPasswor dEdit
            self.verify_msg()
        except Exception as e:
            print(e)

    def verify_msg(self):
        try:
            verification_result = (
                    self.gpg.verify_message(self.original_recv_msg, self.decrypt_password.text()) or
                    self.gpg.verify_message_appended(self.original_recv_msg) or
                    self.gpg.verify_message_appended(
                        self.gpg.decrypt_message(self.original_recv_msg, self.decrypt_password.text()).data)
            )
            # print(verification_result)
            if verification_result:
                self.verify_sign.setText("Znany podpis")
                return True
            self.verify_sign.setText("Brak uwierzytelnienia")
            return False
        except Exception as e:
            print(e)

class ImportKeyDialog(QDialog):
    def __init__(self, gpg):
        super().__init__()

        self.gpg = gpg
        self.text_field = QTextEdit(self)
        self.text_field.setFixedSize(501, 261)

        self.result_browser = QTextBrowser(self)
        self.result_browser.setFixedSize(411, 31)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok, self)
        self.button_box.accepted.connect(self.import_key)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_field, alignment=Qt.AlignCenter)
        layout.addWidget(self.button_box, alignment=Qt.AlignCenter)
        layout.addWidget(self.result_browser, alignment=Qt.AlignCenter)

    def import_key(self):
        try:
            key_text = self.text_field.toPlainText()
            result = self.gpg.import_public_key(key_text)
            # print(result)
            fingerprints = ''
            for fingerprint in result.fingerprints:
                fingerprints += f"{fingerprint}\n"
            self.result_browser.setText(fingerprints)
        except Exception as e:
            print(e)
            self.result_browser.setText("Niepowodzenie")

app = QApplication([])
window = GUI()
app.exec_()