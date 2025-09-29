import email

STS_OK = 0
STS_SUBJECT_UNKNOWN = 1
STS_MULTIPART_ERROR = 2

class emailMsg(object):

    @staticmethod
    def get_type(email_str):
        msg = email.message_from_string(email_str)
        return msg.get('Subject').strip() 

    def __init__(self,email_str):
        self.email_str    = email_str
        self.sender       = ''
        self.subject      = ''
        self.is_multipart = False
        self.sub_msgs     = []
        self.contents     = []

    def _parse(self):
        msg = email.message_from_string(self.email_str)
        self.sender = msg.get('From').strip()
        self.subject = msg.get('Subject').strip()

        if msg.is_multipart():
            self.is_multipart = True
            sub_msgs = msg.get_payload()
            for sub_msg in sub_msgs:
                self.sub_msgs.append(sub_msg)
                self.contents.append(sub_msg.get_payload())
        else:
            self.is_multipart = False
            self.sub_msgs.append(msg.get_payload())
            self.contents.append(msg.get_payload())

    def get_content(self):
        return self.contents[0]

    def get_sender(self):
        return self.sender

    def validate(self):
        # Method should be re-implemented
        # in derived classes 
        pass

  

