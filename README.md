What is it?
========
python_tracker is a library inspired in Python's logging module that helps logging user activity in a Python application.

It was developed to generate statistics over a collaborative web application by processing logs.

It has support for:

* logging levels
* function call hierarchy
* file or database handling
* parameters inclusion or exclusion
* parameter objects serialization 
* chosen object parameter's representation
* thread safety
* possibility to augment or personalize functionality using inheritance and method overriding.

How to use?
========
Just download the source code and place it somewhere inside your application.

Required libraries are SQLAlchemy, decorator and a configured Python logging.

Check out:

* [SQLAlchemy installation][sqlalchemy-install]
* [decorator module installation][decorator-install]
* [Python logging configuration][python-logging]

Then fill your track.cfg file with adequate values. The file specifies how to do this.

One thing to notice is that if you're using a database handling, [COLUMNS] values, model.py log table specification and key, values added as info must coincide.

You also have to specify python-track location for imports in model.py and augment.py
(If you do a <git grep FIXME> you'll find the right places).

Then you have two possibilities, use the default tracker classes or override these to get personalized behavior:

1. You have to execute the init_track() method from track.py somewhere in your application initialization to start the tracking process.
2. Follow the indications in augment.py file. Then execute the init_aug_track() method from augment.py somewhere in your application initialization to start the tracking process.

How to track a function?
-------------------------------------------

Tracker class has a probe function decorator.

All decorated functions are tracked if the level specified in probe parameters is higher than the level specified in RootTracker initialization. 

Level order is DEBUG < INFO < DEFAULT < NONE.

In a nutshell:

Create a tracker object in your module import section:

	(application path to python_tracker folder).python_tracker import track
	tr = track.getTracker(__name__)

For every function you want to track decorate with probe method:

	@tr.probe(level=DEFAULT, fname=None, inc=None, exc=None)
	level: logging level for function, if this level is lower than the one specified in RootTracker this function and the ones called by it are ignored.
	fname: specify a different name for function (for example if you change the original name, but not functionality)
	inc: parameters to include in log data parameters. Only parameter in inc but not in exc are included. 
	exc: paramaters to exclude from log data parameters.
	
How is the structure of a log?
-------------------------------------------

A log has the following structure:

	{'info_key' : value, 'data' : [{'data_key_f1' : value}, {'data_key_f2' : value}]}
	
It is important to notice two things:

1. A log holds information for all functions in call hierarchy, meaning that if a decorated function calls another decorated function, data added is collected in the same log. That's why data value is a list of dictionaries.
2. There are two ways of adding information to logs: info and data. Info values are shared by all functions in a hierarchy, this could be the user, the application version, the application instance, etc. Data is particular to each function, typical data values are function parameters.

In order to add info:

	tr.add_info(key, value)
	
In order to add data:

	tr.add_data(key, value, depth=None)
	
You can also add info or data in the extend_log method in the augment.py file. Take a look at the file for more details.

More Documentation
==================
Soon...

Who Are You?
============
I'm [María Elena Villalobos][mati] Computer Engineering student and soon graduate =)


[sqlalchemy-install]:http://www.sqlalchemy.org/docs/05/intro.html#installing-sqlalchemy
[decorator-install]:http://pypi.python.org/pypi/decorator
[python-logging]:http://docs.python.org/library/logging.html
[mati]:http://be.linkedin.com/in/mevp7