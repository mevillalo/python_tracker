from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import mapper, sessionmaker

# FIXME change to correct path
# from (application path to python_tracker folder).python_tracker.track import engine_location

if engine_location:
	logs_engine = create_engine(engine_location)
	logs_metadata = MetaData(logs_engine)
	LogsSession = sessionmaker(bind=logs_engine, autocommit=True)

	logs_session = LogsSession()

	class Log(object):
	
		def __init__(self, **kwargs):
			for key, val in kwargs.iteritems():
				setattr(self, key, val)
			
	logs_table = Table('logs', logs_metadata,
		Column('id',	Integer, primary_key=True),
		Column('ts',	DateTime, default=datetime.utcnow),
		Column('data',	PickleType),
	)
	logs_metadata.create_all()

	mapper(Log, logs_table)