# MoviesFastAPI

### Launch instance on a server
First install all the required packages:
``pip install -r requirements.txt``
Then you can launch the app using either ``uvicorn`` or ``gunicorn``.

Gunicorn allows you to start a daemon server.

### Using ``uvicorn``
1. ``cd`` to the folder where ``main.py`` is located.
2. run the command: ``uvicorn main:app --host 127.0.0.1 --port 8000``

You can change the port by changing the ``--port 8000`` value to ``--port *``, where ``*`` is the port.

You can use ``--host 0.0.0.0`` in order to listen to all the IPs on the server.

### Using ``gunicorn``
1. ``cd`` to the folder where ``main.py`` is located.
2. Install gunicorn. On Ubuntu you can install using apt-get: ``sudo apt-get install gunicorn``
3. Launch the uvicorn worker using gunicorn:
````
gunicorn main:app --workers 1 --workers-class uvicorn.workers.UvicornWorker --access-logfile [file location] 
--bind 127.0.0.1:8000 --timeout 0 --daemon
````

You can change the worker count, however, keep in mind that each worker loads the word vector file into RAM (approx. 150MB per worker).


Change logfile location ``--access-logfile '-'`` to log directly to STDOUT