# Starts Redis, webserver and application on localhost
# You shouldn't run this outside of your local network

redis-server &
gunicorn -k gevent --worker-connections 1000 --timeout 240 --log-level debug -b 127.0.0.1:5000 app:app
