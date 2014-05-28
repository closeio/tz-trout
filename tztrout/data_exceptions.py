"""
Put the exceptions for the auto-generated data here. The format should be:

'type:value': {
    'include': [list, of, tz, ids],
    'exclude': [list, of, tz, ids]
}

Allowed types are: ('zip', 'state').
"""

data_exceptions = {
    'state:WI': {
        'exclude': ['America/Indiana/Tell_City', 'America/Indiana/Knox']
    }
}
