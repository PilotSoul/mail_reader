import os
from attachment_processing import *
import dotenv
from mail_tools import Mail, Letter
from credentials import credentials, aliases


env = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_path=env)
server_path = os.getenv('server_path')
pidfile = os.getenv('pidfile')


if __name__ == "__main__":
    cred, file_path = None, None
    if os.path.exists(pidfile):
        print('Process already started')
    else:
        with open(pidfile, "w") as file:
            file.write(str(os.getpid()))
        try:
            for cred in credentials:
                mail_obj = Mail(cred)
                mail, mail_ids = mail_obj.find_mails()
                if not mail_ids:
                    print("Unseen messages not found")
                    continue
                for mail_id in mail_ids:
                    letter_obj = Letter(cred, mail)
                    letter_obj.fetch_mail(mail_id)
                    current_mail_path = letter_obj.define_owner_path(server_path, aliases)
                    os.makedirs(current_mail_path, 0o777, True)
                    letter_obj.message_walker()
                    letter_obj.check_current_mail()
        except Exception as e:
            print("   ERROR   ")
            if cred and file_path:
                print("Post: ", cred.get("login"), 'file: ', file_path)
            elif cred:
                print("Post: ", cred.get("login"))
            print("Something wrong\n" + str(e))
            os.remove(pidfile)

    os.remove(pidfile)

