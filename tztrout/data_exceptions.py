"""
Put the exceptions for the auto-generated data here. The format should be:

'type:value': {
    'include': [list, of, tz, ids],
    'exclude': [list, of, tz, ids]
}

Allowed types are: ('zip', 'state', 'all', 'city', 'areacode').

Note that exceptions for cities and area codes have a higher priority than any
other timezone rule. E.g. if you do 'city:new york': { 'include': ['America/New_York'] },
that's *the only* tz id to be returned for tztrout.tz_ids_for_address('US', state='NY', city='New York').
"""

data_exceptions = {

    'all': {
        'exclude': ['America/Indiana/Tell_City', 'America/Indiana/Knox',
                    'America/North_Dakota/Beulah', 'America/Indiana/Winamac',
                    'America/Indiana/Petersburg', 'America/Indiana/Vincennes']
    },

    'state:NY': {
        'exclude': [u'America/Indiana/Winamac', u'America/Indiana/Petersburg',
                    u'America/Indiana/Vincennes']
    },

    'state:PA': {
        'exclude': [u'America/Indiana/Winamac', u'America/Indiana/Petersburg',
                    u'America/Indiana/Vincennes']
    },

    'state:IN': {
        'include': ['America/Indiana/Indianapolis']
    },

    'city:el paso': {
        'include': ['America/Denver']
    },

    'areacode:915': {
        'include': ['America/Denver']
    },

    'areacode:901': {
        'include': ['America/Chicago']
    },

    'areacode:202': {
        'include': ['America/New_York']
    }

}
