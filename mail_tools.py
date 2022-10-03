import os
import imaplib
import email
from datetime import datetime
import re
from recognition_tools import Preprocessing, GetQRCode
from defs import *
import shutil
import tempfile
from attachment_processing import *


def unseen_mails(mail):
    status, messages = mail.search(None, '(UNSEEN)')
    if status == "OK":
        mail_ids = messages[0].split()
        return mail_ids
    return []


class Mail:
    def __init__(self, credential):
        self._login = credential.get("login")
        self._name = credential.get("name")
        self._password = credential.get("password")
        self._server = credential.get("server")
        self.mail = None
        self.mail_ids = None

    def find_mails(self):
        self.mail = imaplib.IMAP4_SSL(self._server)
        self.mail.login(self._login, self._password)
        self.mail.select('inbox')
        self.mail_ids = unseen_mails(self.mail)
        if not self.mail_ids:
            return self.mail, []

        return self.mail, self.mail_ids

    def get_name_and_login(self):
        return self._name, self._login


class Letter(Mail):
    def __init__(self, credential, mail):
        super().__init__(credential)
        self.file_path = None
        self.current_file_path = None
        self.mail = mail
        self.email_date = None
        self.msg = None
        self.mail_id = None
        self.current_mail_path = None

    def fetch_mail(self, mail_id):
        self.mail_id = mail_id
        typ, data = self.mail.fetch(self.mail_id, '(RFC822)')
        self.mail.store(self.mail_id, '+FLAGS', '\\SEEN')
        for response_part in data:
            if isinstance(response_part, tuple):
                self.msg = email.message_from_bytes(response_part[1])
                try:
                    self.email_date = datetime.strptime(self.msg['date'], '%a, %d %b %Y %H:%M:%S %z')
                except Exception as e:
                    self.email_date = datetime.now()
                # from qr_recognition
                self.email_date = utc_time(self.email_date)

    def define_owner_path(self, server_path, aliases):
        parse_email = re.findall('<([^<>]*)>', self.msg['from'])
        email_from = parse_email[0] if parse_email else self.msg['from']

        parse_email_to = re.findall('<([^<>]*)>', self.msg['to'])
        email_to = parse_email_to[0] if parse_email_to else self.msg['to']
        if email_to.lower() in aliases:
            name_folder = aliases[email_to.lower()]
            self.current_mail_path = os.path.join(server_path, name_folder,
                                                  email_to.lower(), email_from,
                                                  str(int(self.mail_id)) + '(' + str(self.email_date) + ')')
        else:
            self.current_mail_path = os.path.join(server_path, self.name,
                                                  self.login, email_from,
                                                  str(int(self.mail_id)) + '(' + str(self.email_date) + ')')
        return self.current_mail_path

    def message_walker(self):
        for part_counter, part in enumerate(self.msg.walk()):
            self.current_file_path, self.file_path = find_attachment(part, self.current_mail_path, part_counter)
            if self.file_path:
                print('filepath= ' + self.file_path)
                original, extension = rename_with_extension(self.file_path, self.current_file_path)
                with tempfile.TemporaryDirectory() as path:
                    if extension == '.pdf':
                        pdf_processing(original, path, self.current_file_path)
                    elif extension == '.jpg' or extension == '.jpeg' or extension == '.png' or extension == '.tif':
                        image_processing(original, self.current_file_path)
                    else:
                        print('bad-extension: ' + extension)

    def check_current_mail(self):
        status = '-success'
        if not os.path.exists(self.current_mail_path + status):
            os.rename(self.current_mail_path, self.current_mail_path + status)
            os.chmod(self.current_mail_path + status, 0o0777)
        else:
            shutil.rmtree(self.current_mail_path + status)
            os.rename(self.current_mail_path, self.current_mail_path + status)
            os.chmod(self.current_mail_path + status, 0o0777)
