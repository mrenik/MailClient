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
        # print(input_data)
        new_key = self.gpg.gen_key(input_data)
        # print(new_key)
        # print(self.gpg.export_keys(str(new_key)))
        return new_key

    def sign_message(self, message, key, passphrase):
        return self.gpg.sign(message, **{
            'keyid' : key['fingerprint'],
            'passphrase' : passphrase})

    def encrypt_message(self, message, key, sign = None):
        kwargs = {}
        if sign is not None:
            kwargs['sign'] = str(sign)
        return self.gpg.encrypt(message, key['fingerprint'], **kwargs)

    # kinda pointless
    def encrypt_file(self, file, key):
        return self.gpg.encrypt_file(file, key['fingerprint'])

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

    def verify_message_appended(self, message):
        self.gpg.encoding = 'latin-1'
        to_verify_latin = self.gpg.verify(message)
        # gpg.verify returns correct .valid and .trust_text but .data is empty?
        self.gpg.encoding = 'utf-8'
        return to_verify_latin.valid

    def get_email_keys(self, name_email):
        return [key for key in self.gpg.list_keys()
                if any(email == name_email for email in self.get_key_emails(key))]

    def import_public_key(self, key_data):
        import_result = self.gpg.import_keys(key_data)
        self.gpg.trust_keys(import_result.fingerprints, 'TRUST_ULTIMATE')
        return import_result


    def select_key(self, current_email, selected_id = 0):
        possible_keys = self.get_email_keys(current_email)
        if not possible_keys:
            return None
        return possible_keys[selected_id]

    # turns out to be useless since we use uids and fingerprints
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
    # key = gpg_manager.generate_key(name_email="john.boe@example.com", passphrase="passphrase")
    # # "john.doe@example.com"
    # print("Generated Key:", key)
    # # print(type(key))
    #
    # plaintext_message = "JOm JOk JOł"
    # recipients = "john.doe@example.com"  # Use the fingerprint of the recipient's key
    #
    # # print("@" * 40)
    # # signed = gpg_manager.gpg.sign(plaintext_message, **{'keyid' : key.fingerprint, 'passphrase' : "passphrase"})
    # # print(signed)
    # # print("@" * 40)
    # # verification_result = gpg_manager.gpg.verify(signed.data)
    # # print("Signature Verification Result:", verification_result)
    #
    # # encrypted_message = gpg_manager.encrypt_message(plaintext_message, recipients)
    # encrypted_message = gpg_manager.encrypt_message(plaintext_message, recipients, sign=gpg_manager.select_key("john.doe@example.com")['keyid'])
    # print("Encrypted Message:", encrypted_message)
    # #
    # #
    # #
    # decrypted_message = gpg_manager.decrypt_message(encrypted_message.data, "passphrase")
    # print("Decrypted Message:", decrypted_message)
    # #
    # gpg_manager.gpg.encoding = 'latin-1'
    # decrypted_message = gpg_manager.decrypt_message(encrypted_message.data, "passphrase")
    # verification_result = gpg_manager.gpg.verify(decrypted_message.data)
    # # print("Signature Verification Result:", verification_result)
    # print("Ayo czy git?", decrypted_message.status, decrypted_message.valid, decrypted_message.trust_text)
    # print("Ayo czy git?", verification_result.status, verification_result.valid, verification_result.trust_text)
    # #
    # for key in gpg_manager.get_email_keys("john.doe@example.com"):
    #     print(key)
    #     print("key ?/\\")
    # # # for key in gpg_manager.get_email_keys("whotwhot@whot.whot"):
    # # #     print(key)
    # # # print()
    # for key in gpg_manager.gpg.list_keys():
    #     print(key)
    #     print(key['fingerprint'])
    #     print(gpg_manager.get_key_emails(key))

    pgp_signed_message = """-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA256

whot
-----BEGIN PGP SIGNATURE-----

iQEzBAEBCAAdFiEEsYjpENKDer0uJ9GWa2X8j+Z1fnAFAmWvK1IACgkQa2X8j+Z1
fnBp4ggAikTUz3IifaqbNUw4KoAS1kxJ5KLQ9LyUiKd0oOzJzhVXo+8l2qjBw3r0
SkbrOklA2eSGl+r6oYRHhImVFV4CJ/ZIUubN+hHIurwgcmJ0S096fn8sw0B+Cucy
BTjtfEs/5mHzXVYfWMV9zQ3IXNHC/ZFEJpNiQYnBJ1h5CbBlhH4WHhODDMiX51XK
3EtglxvYFRih1eMF0osmV7/5us4FbI/KLrOsWeIz7r8vUcfZtraCFPteG94TU2Br
Sg5KExODwheoCG/wIpdFHX85jDqAHvSxVGLk8c1grEN1SleTPRUzFXjRqlN1ehg+
frKdQwl50atinNkkkOIPMcd+xhnHSg==
=Uq/N
-----END PGP SIGNATURE-----
    """

    pgp_testowana = """-----BEGIN PGP MESSAGE-----

hQEMA2tl/I/mdX5wAQf+NwEMtezwgavdmrmXSjLDN++n1w3nrRtnRNd9sbqjcGWI
etBwqvT3cA/8BNHb9PIATlmYV5KKpGMOnqbfxxgzviLkAinHgXjQrmor3U2zTlmc
91BM5cJAWKsDvjNE/us+VDIoNCoTxcF1KOwvlRIfNh1JP9t3LmArOuCgZxPAb0Cf
v4BEhwuJm7ULtApQ5x8Qs0BQOLF0KZbgnQXfOzKCUypgoVfSWy4VaymuiRpVJ6dB
rhiTZTvAmIsuvLBA35q2SnRQubM47zwPwMM+MKr1Au04QCcG39+AAPDtnaXuGevp
+Gq4JL8mtfJqYKE7uX9Y3LvaSXBOHoIj7fipdxHh1dTpAQkCEMKD7KTMIRmaFt0I
dAJDUo/bfhsd3z1k0bvaVxc8cT0hV8jLTHQ9S/uTGTJNvBKeAFXpR9M/iDR/lFDO
7ditT+BaRuCUTq20dDQg/dtwVOap3aMCdPFbnBhEBp29RK4vZrmrd0AH2SXFf3l4
eJPtvULO8oTqjW3Jpxtb3XnGPDtAHBVCjweMXQfulhX+pFD+N2cxBc2jfEOXgGvU
MYLBXtlUbaJSHOxxbwE0x+wSHigSKJ1o3MpeieBVmwpaQxQULaUiZahZz5zRxKBN
/Jv2/6MSFUSghxKLOZbLxh1TqwO1D/hjf8gyTaeYNMRtXM9WIFmxDgiayJ+jhJ1n
/BMHTzLPEwaSbQaCAKhYkc7zRwQCfMfpSJzs5IRo7spFR4YmRGoWOVspA2kJeNDE
eiZYc2nXuHJLKqskCIUuAVTj1UHK4Oe8+Op+p1R/co+hQ9AvhirQJPC2+Q0U1ypD
XHaxyhu77hveBTqTPwixGhygumC6oHjP+ATswEOJOIL5X3KhcNud3JWIDZHVB3Xw
wZK+WfkvUrfuB6Y+CpodoAcMepJmPPUBSJrw2Mcj9XB4UshFxTGXW35dGyKIW98R
LzsozACtwRlm+nX2XJYOLDJqLBJhNKajYvbLl+nvOB7H+HKIPzBGj4dAhtH8onkP
O/NillLkKswEsxfRLcngzo8DIs+h
=hbGE
-----END PGP MESSAGE-----
"""
    # print(pgp_signed_message)
    # verification_result = gpg_manager.verify_message_appended(pgp_signed_message)
    # print("wery", verification_result.data.decode('utf-8', errors='replace'))
    # print("Ayo czy git?", verification_result.valid, verification_result.status)
    #
    print(pgp_testowana)
    decrypt = gpg_manager.decrypt_message(pgp_testowana, "123123")
    print(decrypt.status)



