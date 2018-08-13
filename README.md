punter node
-----------

This is an experiment for physical antenna management in the context of Ninux.

By mounting the antenna on the axis of a stepper motor we can change the orientation
without phisical access to the node.

This could be critical for nodes in remote location or exposed to harsh conditions as
the mantainance could be done from far away.

-----------
It is possible to test the code launching

~~~
python3 turnantenna.py
~~~

and test the api's methods with the following curl commands:

* get_position:
  ~~~~
  curl -i -H "Content-Type: application/vnd.api+json" -X GET -d '{"id":"1"}' http://localhost:5000/api/v1.0/position
  ~~~~

* init_engine:
  ~~~~
  curl -i -H "Content-Type: application/vnd.api+json" -X POST -d '{"id":"1"}'  http://localhost:5000/api/v1.0/init
  ~~~~

* move:
  ~~~~
  curl -i -H "Content-Type: application/vnd.api+json" -X POST -d '{"id":"1","angle":"XX"}'  http://localhost:5000/api/v1.0/move
  ~~~~
  where XX is the value of the angle

To have more information during the excecution, it is possible to use

~~~
python3 turnantenna.py -vvv
~~~

in order to see every change in the states of the States Machine

test_stepmotor
--------------
To run test_stepmotor.py module you need to install the 'wiringpi' library from https://github.com/WiringPi/WiringPi-Python
and to create the directory

~~~
\debugfiles
~~~

Tests start with:

~~~
python3 test_stepmotor.py
~~~

test_api
--------
Before launching test_api.py, the flask server should be started with:

~~~
export FLASK_APP=api.py
flask run
~~~

differently from stepmotor, to start api tests we'll use pytest:

~~~
pytest test_api.py
~~~