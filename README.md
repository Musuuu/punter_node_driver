punter node
-----------

This is an experiment for physical antenna management in the context of Ninux.

By mounting the antenna on the axis of a stepper motor we can change the orientation
without phisical access to the node.

This could be critical for nodes in remote location or exposed to harsh conditions as
the mantainance could be done from far away.

-----------
To run the test module you need to install the 'wiringpi' library from https://github.com/WiringPi/WiringPi-Python

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
  curl -i -H "Content-Type: application/vnd.api+json" -X POST -d '{"id":"1","angle":"140"}'  http://localhost:5000/api/v1.0/move
  ~~~~

To have more information during the excecution, it is possible to use

~~~
python3 turnantenna.py -vvv
~~~

in order to see every change in the states of the States Machine