#!/usr/bin/python
# encoding: utf-8
"""
mail.py
For email functions

Created by Shane O'Connor 2013
"""

from string import join
import email.Message
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

from klab.fs.fsio import read_file

class MailServer(object):

    def __init__(self, host = None, port = None):
        self.host = host
        self.port = port

    def sendmail(self, subject, sender, recipients, plaintext, htmltext=None, cc=None, debug=False, useMIMEMultipart=True):
        if recipients:
            if type(recipients) == type(""):
                recipients = [recipients]
            elif type(recipients) != type([]):
                raise Exception("Unexpected type for recipients.")
            if cc:
                if type(cc) == type(""):
                    recipients.append(cc)
                elif type(cc) == type([]):
                    recipients.extend(cc)
                else:
                    raise Exception("Unexpected type for cc.")
            recipients = join(recipients, ";")

            if plaintext and htmltext and useMIMEMultipart:
                msg = MIMEMultipart('alternative')
            else:
                msg = email.Message.Message()

            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = recipients
            msg['Reply-To'] = sender
            if plaintext and htmltext and useMIMEMultipart:
                part1 = MIMEText(plaintext, 'plain')
                part2 = MIMEText(htmltext, 'html')
                msg.attach(part1)
                msg.attach(part2)
            else:
                msg.set_type("text/plain")
                msg.set_payload(plaintext)

            if debug:
                print(msg)
            else:
                if self.host and self.port:
                    s = smtplib.SMTP(self.host, self.port)
                elif self.host:
                    s = smtplib.SMTP(self.host)
                else:
                    s = smtplib.SMTP()
                s.connect()
                s.sendmail(msg['From'], recipients, msg.as_string())
                s.close()
            return True
        return False

    def sendgmail(self, subject, recipients, plaintext, htmltext=None, cc=None, debug=False, useMIMEMultipart=True, gmail_account = 'kortemmelab@gmail.com', pw_filepath = None):
        '''For this function to work, the password for the gmail user must be colocated with this file or passed in.'''
        smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo
        gmail_account = 'kortemmelab@gmail.com'
        if pw_filepath:
            smtpserver.login(gmail_account, read_file(pw_filepath))
        else:
            smtpserver.login(gmail_account, read_file('pw'))
        for recipient in recipients:

            if htmltext:
                msg = MIMEText(htmltext, 'html')
                msg['From'] = gmail_account
                msg['To'] = recipient
                msg['Subject'] = subject
                smtpserver.sendmail(gmail_account, recipient, msg.as_string())
            else:
                header = 'To:' + recipient + '\n' + 'From: ' + gmail_account + '\n' + 'Subject:' + subject + '\n'
                msg = header + '\n ' + plaintext + '\n\n'
                smtpserver.sendmail(gmail_account, recipient, msg)
        smtpserver.close()

    def sendgmail2(self, subject, recipients, plaintext, htmltext=None, cc=None, debug=False, useMIMEMultipart=True, gmail_account = 'kortemmelab@gmail.com', pw_filepath = None):
        '''For this function to work, the password for the gmail user must be colocated with this file or passed in.'''
        smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo
        gmail_account = 'kortemmelab@gmail.com'
        if pw_filepath:
            smtpserver.login(gmail_account, read_file(pw_filepath))
        else:
            smtpserver.login(gmail_account, read_file('pw'))
        for recipient in recipients:
            header = 'To:' + recipient + '\n' + 'From: ' + gmail_account + '\n' + 'Subject:' + subject + '\n'
            if htmltext:
                msg = header + '\n ' + htmltext + '\n\n'
            else:
                msg = header + '\n ' + plaintext + '\n\n'
            smtpserver.sendmail(gmail_account, recipient, msg)
        smtpserver.close()