import os
import imaplib
import ConfigParser

class EmailReceiver:

    def __init__(self):
        # Read config
        config = ConfigParser.RawConfigParser()
        path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
        path_to_config = os.path.normpath(path_to_config)
        config.read(path_to_config)

        self.prot = 'IMAP'
        self.server = config.get('IMAP','server')
        self.user   = config.get('IMAP','user')
        self.pwd    = config.get('IMAP','pass')

        print self.prot
        print self.server
        print self.user
        print self.pwd

    def login(self):
        if self.prot == 'IMAP':
            self.conn = imaplib.IMAP4(self.server)
            self.conn.login(self.user,self.pwd)
            self.conn.select()    
            return True 
        else:
            return False 

    def get_unseen_mails(self):
        if self.prot == 'IMAP':
            typ, data = self.conn.search(None, '(UNSEEN)')
            if typ != 'OK':
                pass
            ids = data[0].split()
            for idd in ids:
                typ, data = self.conn.fetch(idd, '(RFC822)')
                if typ != 'OK':
                    yield None   
                else:    
                    yield data[0][1] 

    def __del__(self):
        if self.conn is not None:
            self.conn.close()
            self.conn.logout() 
        


