#!/bin/bash
# Wrapper script for GHN Dashboard Auto-refresh
cd "/Users/macbook/Downloads/GHN"
/usr/local/bin/python3 auto_refresh.py --once >> auto_refresh.log 2>&1
