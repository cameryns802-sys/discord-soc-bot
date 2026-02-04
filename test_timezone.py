#!/usr/bin/env python3
"""Test PST timezone conversion"""
from datetime import datetime, timezone
import pytz

pst = pytz.timezone('America/Los_Angeles')
utc = timezone.utc

utc_now = datetime.now(utc)
pst_now = pst.localize(datetime.now())

print(f"UTC time: {utc_now}")
print(f"PST time: {pst_now}")
print(f"Difference: {utc_now.hour - pst_now.hour} hours")
