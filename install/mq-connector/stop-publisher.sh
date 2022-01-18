SIGNAL=${SIGNAL:-TERM}
PIDS=$(ps ax | grep java | grep -i Adabas | grep -v grep | awk '{print $1}')
if [ -z "$PIDS" ]; then
  echo "No Adabas publisher server to stop"
  exit 1
else
  kill -s $SIGNAL $PIDS
fi

