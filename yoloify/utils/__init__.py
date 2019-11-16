def total_minutes(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6 / 60
