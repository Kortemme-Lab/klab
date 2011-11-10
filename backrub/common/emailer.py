from string import join 
import email.Message
import smtplib
from email.MIMEMultipart import MIMEMultipart 
from email.MIMEText import MIMEText

default_email = "shane.oconnor@ucsf.edu"

def sendEmail(subject, sender, recipients, plaintext, htmltext = None, cc = None, debug = False, useMIMEMultipart = True):
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
		
		if useMIMEMultipart:
			msg = MIMEMultipart('alternative')
		else:
			msg = email.Message.Message()
			
		msg['Subject'] = subject
		msg['From'] = sender
		msg['To'] = recipients
		msg['Reply-To'] = default_email
		if useMIMEMultipart:
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
			s = smtplib.SMTP()
			s.connect()
			s.sendmail(msg['From'], recipients, msg.as_string())
			s.close()
		return True
	return False
