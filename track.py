import logging
log_ = logging.getLogger(__name__)

import time
import json
import threading
import Queue
import ConfigParser
import zlib
from operator import itemgetter
from decorator import decorator
from inspect import isfunction, getargspec
from string import split

# track levels
NONE = 10
DEFAULT = 0
INFO = -10
DEBUG = -20

engine_location = None

def set_manager(manager=None):
	global m
	m = manager

class LogsEncoder(json.JSONEncoder):
	def default(self, obj):
		return obj.__track__() if hasattr(obj, '__track__') else unicode(obj)

class Manager(object):

	def __init__(self, root=None):
		self.trackers = {}
		if root:
			self.trackers['root'] = root

	def getTracker(self, prefix):
		if prefix in self.trackers.keys():
			return self.trackers[prefix]
		else:
			tr = Tracker(prefix)
			self.trackers[prefix] = tr
			return tr
			
	def get_root(self):
		return self.trackers['root']
			
class Context(threading.local):
	
	def __init__(self):
		self.depth = -1
		self.info = {}
		self.data = []
		self.extra = {}
		self.ignore = {'value': False, 'level': 0}
	
class RootTracker(object):
	
	def __init__(self, level=DEFAULT, pickle=False):
		self.state = Context()
		self.q = Queue.Queue()
		self.level = level
		self.pickle = pickle
		
	def get_state(self):
		return self.state
		
	def _push(self):
		s = self.state
		s.depth += 1
		s.extra[s.depth] = {}

	def _pop(self):
		s = self.state
		d = self._get_ignore()
		ignore = d['value']
		if ignore and d['depth'] == s.depth:
			self._set_ignore()
		s.depth -= 1
		if s.depth == -1:
			if not ignore and s.info != []:
				self.queue()

	def _set_ignore(self, value=False):
		s = self.state
		s.ignore['value'] = value
		s.ignore['depth'] = s.depth

	def _get_ignore(self):
		s = self.state
		return s.ignore
		
	def get_depth(self):
		return self.state.depth

	def log(self, exception=False, prefix='', func=None, fname=None, duration=0, inc=None, exc=None, *args, **kwargs):
		
		s = self.get_state()
		d = {}
		
		d['prefix'] = prefix
		d['function'] = fname if fname else func.__name__
		d['depth'] = s.depth
		d['duration'] = duration
			
		params = {}

		if isfunction(func):
			argspec = getargspec(func)

			if len(argspec.args) > 0:
				fst = argspec.args[0]

				if fst == 'self':
					d['class_name'] = args[0].__class__.__name__
				elif fst == 'kls':
					d['class_name'] = args[0].__name__

				for arg, value in zip(argspec.args, args):
					if inc is None or (arg in inc):
						if exc is None or (arg not in exc):
							params[arg] = json.dumps(value, cls=LogsEncoder)
							
				for karg, value in kwargs.iteritems():
					if inc is None or (karg in inc):
						if exc is None or (karg not in exc):
							params[karg] = json.dumps(value, cls=LogsEncoder)

		d['params'] = params
		d['ts'] = time.localtime()
		
		for k,v in s.extra[s.depth].iteritems():
			d[k] = v
			
		d['exception'] = exception

		self.state.data.append(d)
		
	def queue(self):
		s = self.get_state()
		
		if self.q:
			if not self.pickle:
				s.data = unicode(s.data)
				
			s.info['data'] = s.data
			
			self.q.put(s.info)
			s.info = {}
			s.data = []
		else:
			log_.exception("Log cannot be queued because there is no Queue")
			
	def add_data(self, key, value, depth=None):
		s = self.state
		if depth is not None:
			s.extra[depth][key] = value
		else:
			s.extra[s.depth][key] = value
		
	def add_info(self, key, value):
		s = self.state
		s.info[key] = value

class Tracker(object):

	def __init__(self, prefix):
		self._prefix = prefix
		
	def add_data(self, key, value, depth=None):
		rootTracker = m.get_root()
		rootTracker.add_data(key, value, depth)
		
	def add_info(self, key, value):
		rootTracker = m.get_root()
		rootTracker.add_info(key,value)
		
	def extend_log():
		# This method can be overridden to add application specific
		# information to logs.
		pass

	def probe(self, level=DEFAULT, fname=None, inc=None, exc=None):
		@decorator
		def wrap(f, *args, **kwargs):
			rootTracker = m.get_root()
			rootTracker._push()
			if level < rootTracker.level:
				rootTracker._set_ignore(True)
			time_before = time.time()
			try:
				exception = False
				if rootTracker.get_depth() == 0:
					self.extend_log()
				result = f(*args, **kwargs)
			except:
				exception = True
			finally:
				time_after = time.time()
				duration = time_after - time_before
				if not rootTracker._get_ignore()['value']:
					rootTracker.log(exception, self._prefix, f, fname, duration, inc, exc, *args, **kwargs)
				rootTracker._pop()
				if exception:
					raise
			return result
		return wrap
		
def getTracker(prefix=''):
	return m.getTracker(prefix)

def file_handle_logs():
	rootTracker = m.get_root()
	while True:
		logs = []
		
		while len(logs) < top:
			logs.append(rootTracker.q.get(True))

		FILE = open(filename, "a")
		content = ""
		for log in logs:
			for c in cols:
				v = log.get(c, None)
				if content == "":
					content = str(v)
				elif content[-1] == "\n":
					content = "%s%s" % (content, str(v))
				else:
					content = "%s, %s" % (content, str(v))
			content = "%s \n" % content
			
		FILE.write(content)
		FILE.close()

def db_handle_logs():
	from knowledgeplaza.libs.track.model import Log, LogsSession
	
	logs_session = LogsSession()
	rootTracker = m.get_root()

	while True:
		logs = []
		
		while len(logs) < top:
			logs.append(rootTracker.q.get(True))

		for log in logs:
			try:
				kwargs = {}
				for c in cols:
					kwargs[c] = log.get(c, None)
					
				s = Log(**kwargs)
				logs_session.add(s)
				logs_session.flush()
			except:
				log_.exception("Error when trying to log")
			
def start_handler(type_='file'):
	if type_ == 'file':
		t = threading.Thread(target=file_handle_logs)
	elif type_ == 'db':
		t = threading.Thread(target=db_handle_logs)
	else:
		log_.exception("Handler type_ not recognized: %r", type_)
		return
	t.daemon = True
	t.start()
	
def init_handle():
	try:
		global cols, top, filename, engine_location
		c = ConfigParser.ConfigParser()
		c.read('track.cfg')
	
		cols = [(int(n),v) for (n, v) in c.items('COLUMNS')]
		cols = [v for (n,v) in sorted(cols, key=itemgetter(0))]
	
		top = int(c.items('TOP')[0][1])
		
		handler_type = c.items('HANDLER_TYPE')
		
		for k,v in handler_type:
			if k == 'out':
				ht = v
			elif k == 'uri':
				engine_location = v
			elif k == 'filename':
				filename = v
	except:
		log_.exception("Problem parsing configuration file.")

	start_handler(type_=ht)
	
def init_track():
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
	m = Manager(rootTracker)
	set_manager(m)