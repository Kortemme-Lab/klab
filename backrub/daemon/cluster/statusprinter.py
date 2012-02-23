import colortext
from datetime import datetime

class StatusPrinter(object):

	def __init__(self):
		self._statuslevel = 0
		self._statusType = "status"
		self._statusID = "_"
		self._color = "silver"
		
	def _setStatusPrintingParameters(self, ID, statustype = None, level = None, color = None):
		self._statusID = str(ID)
		if level != None:
			self._statuslevel = int(level)
		if statustype != None:
			self._statusType = str(statustype)
		if color != None:
			self._color = str(color)
		
	def _status(self, message, level = 0, plain = False, tags = (), color = None):
		color = color or self._color
		if level <= self._statuslevel:
			timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			if plain:
				colortext.printf((timestamp, message), color)
			else:
				if self._statusID == "_":
					ID = '' 
				else:
					ID = ' id="%s"' % self._statusID
				colortext.write('<debug%s type="%s" time="%s"' % (ID, self._statusType, timestamp), "silver")
				for t in tags:
					colortext.write(' %s="%s"' % t, "silver")
				colortext.write('>', "silver")
				colortext.write('%s' % message, color)
				colortext.printf('</debug>', "silver")
