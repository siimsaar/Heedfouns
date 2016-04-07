# Starts Redis, webserver and application on localhost

redis-server &
gunicorn -k gevent -b 127.0.0.1:5000 app:app