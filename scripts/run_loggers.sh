#!/bin/bash
# Starts both loggers; Ctrl+C stops both.
trap 'kill 0' EXIT

python -m src.log_btc &
python -m src.log_kalshi &

wait