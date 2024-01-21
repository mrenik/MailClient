"""
package python-gnupg, and gpg in path from:
https://gnupg.org/download/index.html
or
https://gpg4win.org/download.html (full-featured)
"""
import gnupg
import os
from datetime import datetime
import re


class PgpBus:
    def __init__(self, home_dir = os.path.join(os.getcwd(), '.gnupghome')):
        if not os.path.exists(home_dir):
            os.makedirs(home_dir)
        self.gpg = gnupg.GPG(gnupghome=home_dir)
        self.gpg.encoding = 'utf-8'

    def generate_key(self, name_email, passphrase, key_type = 'RSA', key_length = 2048, name_real = None):
        if name_real is None:
            name_real = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        input_data = self.gpg.gen_key_input(**{
            'Key-Type' : key_type,
            'Name-Email' : name_email,
            'passphrase' : passphrase,
            'key_length' : key_length,
            'Name-Real' : name_real
        })
        print(input_data)
        new_key = self.gpg.gen_key(input_data)
        print(new_key)
        print(self.gpg.export_keys(str(new_key)))
        return new_key

    def encrypt_message(self, message, recipients, sign = None):
        kwargs = {}
        if sign is not None:
            kwargs['sign'] = str(sign)
        return self.gpg.encrypt(message, recipients, **kwargs)

    # can't be used for verifying
    def decrypt_message(self, message, passphrase):
        return self.gpg.decrypt(message, **{'passphrase' : passphrase})

    # god knows why decrypting works in utf-8, but verifying not
    def verify_message(self, message, passphrase):
        # xd
        self.gpg.encoding = 'latin-1'
        to_verify_latin = self.gpg.decrypt(message, **{'passphrase' : passphrase})
        self.gpg.encoding = 'utf-8'
        return to_verify_latin.valid

    def get_email_keys(self, name_email):
        return [key for key in self.gpg.list_keys()
                if any(email == name_email for email in self.get_key_emails(key))]

    def import_public_key(self, key_data):
        import_result = self.gpg.import_keys(key_data)
        self.gpg.trust_keys(import_result.fingerprint, 'TRUST_ULTIMATE')


    # czy to potrzebne idk
    def select_key(self, current_email, selected_id = 0):
        possible_keys = self.get_email_keys(current_email)
        if not possible_keys:
            return None
        return possible_keys[selected_id]

    @staticmethod
    def get_key_emails(key):
        # basicly between <>
        email_extraction = r'<([^<>]+)>'
        emails = []


        for uid in key['uids']:
            matches = re.search(email_extraction, uid).group(1)
            to_remove = "[]'"
            no_bracket = matches.translate(str.maketrans('', '', to_remove))
            matches = no_bracket.split(', ')
            if matches:
                emails.extend(matches)
        # print(emails)
        return emails


if __name__ == "__main__":
    # testy
    gpg_manager = PgpBus()
    key = gpg_manager.generate_key(name_email="john.doe@example.com", passphrase="passphrase")
    print("Generated Key:", key)

    plaintext_message = "JOm JOk JOł"
    recipients = "john.doe@example.com"  # Use the fingerprint of the recipient's key

    print("@" * 40)
    signed = gpg_manager.gpg.sign(plaintext_message, **{'keyid' : key.fingerprint, 'passphrase' : "passphrase"})
    print(signed)
    print("@" * 40)
    # verification_result = gpg_manager.gpg.verify(signed.data)
    # print("Signature Verification Result:", verification_result)

    # encrypted_message = gpg_manager.encrypt_message(plaintext_message, recipients)
    encrypted_message = gpg_manager.encrypt_message(plaintext_message, recipients, sign=gpg_manager.select_key("john.doe@example.com")['keyid'])
    print("Encrypted Message:", encrypted_message)
    #
    #
    #
    decrypted_message = gpg_manager.decrypt_message(encrypted_message.data, "passphrase")
    print("Decrypted Message:", decrypted_message)
    #
    gpg_manager.gpg.encoding = 'latin-1'
    decrypted_message = gpg_manager.decrypt_message(encrypted_message.data, "passphrase")
    verification_result = gpg_manager.gpg.verify(decrypted_message.data)
    # print("Signature Verification Result:", verification_result)
    print("Ayo czy git?", decrypted_message.status, decrypted_message.valid, decrypted_message.trust_text)
    print("Ayo czy git?", verification_result.status, verification_result.valid, verification_result.trust_text)
    #
    # for key in gpg_manager.get_email_keys("john.doe@example.com"):
    #     print(key)
    # for key in gpg_manager.get_email_keys("whotwhot@whot.whot"):
    #     print(key)
    # print()
    # for key in gpg_manager.gpg.list_keys():
    #     print(key)
    #     print(key['fingerprint'])
    #     print(gpg_manager.get_key_emails(key))