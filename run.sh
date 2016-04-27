# Starts Redis, webserver and application on localhost

redis-server &
gunicorn -k gevent -t 4 --worker-connections 1000 --log-level debug -b 127.0.0.1:5000 app:app
