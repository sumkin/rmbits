import pandas as pd

from emailsender.email_sender import EmailSender

error_counter = {}

def send_quick(frm, to, sbj, txt):
    es = EmailSender('email-smtp.eu-west-1.amazonaws.com',587,'AKIAITNWXVR77FGGINLA','ArOwR7uG5Tovy/4xJkUVs4gLgsi7dw8zACluZ3t39m+C')
    es.send_quick(frm, to, sbj, txt)


def send_multipart(frm, to, sbj, txt, files):
    es = EmailSender('email-smtp.eu-west-1.amazonaws.com',587,'AKIAITNWXVR77FGGINLA','ArOwR7uG5Tovy/4xJkUVs4gLgsi7dw8zACluZ3t39m+C')
    es.send_multipart(frm, to, sbj, txt, files)


def send_multipart_or(sbj, txt, files):
    df = pd.read_csv('s3://ay-rmp-home/static/emails.csv')
    df = df.loc[df['ROLE'] == 'OR']
    for idx,r in df.iterrows():
        try:
            send_multipart('fedor.nikitin@finnair.com', r['EMAIL'], sbj, txt, files)
        except:
            pass

def send_error(where, what):
    if where not in error_counter.keys():
        error_counter[where] = 1
    else:
        error_counter[where] += 1
    if error_counter[where] > 5:
        sbj = 'error in ' + where
        send_quick('fedor.nikitin@finnair.com','fedor.nikitin@finnair.com',sbj,what)
       

if __name__ == '__main__':
    for i in range(8):
        send_error('123','456')



