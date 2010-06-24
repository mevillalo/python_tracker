import turbogears, cherrypy
from turbogears import identity

# FIXME change to correct path
# from (application path to python_tracker folder).python_tracker.track import *

import logging
log = logging.getLogger(__name__)

class AugManager(Manager):
	
	def getTracker(self, prefix):
		if prefix in self.trackers.keys():
			return self.trackers[prefix]
		else:
			tr = AugTracker(prefix)
			self.trackers[prefix] = tr
			return tr
			
class AugTracker(Tracker):

	# TODO
	# Override method to add personalized info or data to logs
	# It is executed only when calling depth is 0 (first calling function)
	# Check where this method is called in track.py for more details
	def extend_log(self):
		# EXAMPLE:
		# self.add_info('app-version', app.get_version())
		# self.add_data('path', app.get_path())
		
	# You can also add other methods to push data or info while
	# functions are being executed.
	
# You should use this method to start tracking process when augmented version is being used.
def init_aug_track():
	level = DEFAULT
	try:
		c = ConfigParser.ConfigParser()
		c.read('track.cfg')
		root = c.items('ROOT')
		for k,v in root:
			if k == 'pickle':
				pickle = True if v == 'True' else False
			elif k == 'level':
				level = v
	except:
		log.exception("Problem parsing configuration file.")
		
	if level == 'DEFAULT':
		level = DEFAULT
	elif level == 'INFO':
		level = INFO
	elif level == 'DEBUG':
		level = DEBUG
		
	rootTracker = RootTracker(level, pickle)
	m = AugManager(rootTracker)
	set_manager(m)