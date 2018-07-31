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
To test the api methods you can use the following curl commands:

* create_engine:

  curl -i -H "Content-Type: application/jsone -X POST http://localhost:5000/api/v1.0/create_engine
* get_position:

  curl -i http://localhost:5000/api/v1.0/position
* init_engine:

  curl -i -H "Content-Type: application/json" -X POST -d '{"id":1}'  http://localhost:5000/api/v1.0/init
* move:

  curl -i -H "Content-Type: application/json" -X POST -d '{"id":1,"angle":140}'  http://localhost:5000/api/v1.0/move