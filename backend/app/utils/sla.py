import os
from datetime import datetime, timedelta

def calculate_resolution_deadline(assigned_at, working_days=None):
    """
    Calculate resolution deadline excluding weekends (Saturday and Sunday).
    If working_days is not provided, defaults to environment variable or 2 days.
    """
    if working_days is None:
        try:
            working_days = int(os.environ.get('SLA_WORKING_DAYS', 2))
        except ValueError:
            working_days = 2

    current = assigned_at
    days_added = 0
    while days_added < working_days:
        current += timedelta(days=1)
        # weekday() returns 0 for Monday ... 5 for Saturday, 6 for Sunday
        if current.weekday() < 5:
            days_added += 1
    return current
