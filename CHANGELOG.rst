0.9.7
-----

* Declared timeout_to_timespec() static - fixes an 'undefined symbol'
  error (Michael Haben <michael.haben@roke.co.uk)

0.9.6
-----

* Add support for arbitrary serializers
  (Roman Timofeev <cryptoloop@gmail.com>)

0.9.5
-----

* Fix maximum value of the tv_nsec in timeout_to_timespec function

0.9.4
-----

* Fix building cffi modules

0.9.3
-----

* Fix setup.py

0.9.2
-----

* Both Python 2 and Python 3 support

0.9.1
-----

* Decrease default `maxmsgsize` limit for POSIX queue to `1024`
* Define error codes constants
* Improve documentation

0.9.0
-----

* First release
