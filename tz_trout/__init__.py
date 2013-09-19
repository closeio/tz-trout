import datetime
import json
import phonenumbers
import pytz

from phonenumbers.geocoder import description_for_number
from pyzipcode import ZipCodeDatabase

from .data import TroutData


td = TroutData()

def tz_ids_for_tz_name(tz_name):
    """ Get the TZ identifiers that are currently in a specific time zone, e.g.

    >>> tz_trout.tz_ids_for_tz_name('PDT')  # ran during DST
    [
        u'America/Dawson',
        u'America/Los_Angeles',
        u'America/Santa_Isabel',
        u'America/Tijuana',
        u'America/Vancouver',
        u'America/Whitehorse',
        u'Canada/Pacific',
        u'US/Pacific'
    ]
    >>> tz_trout.tz_ids_for_tz_name('PDT')  # ran outside of the DST period
    []
    """

    ids = td.tz_name_to_tz_ids.get(tz_name)
    valid_ids = []
    if ids:
        # only get the tz ids that match the tz name currently
        for id in ids:
            tz = pytz.timezone(id)
            try:
                if tz.tzname(datetime.datetime.utcnow()) == tz_name:
                    valid_ids.append(id)
            except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                pass
    return valid_ids


def tz_ids_for_phone(phone):
    """ Get the TZ identifiers that a phone number might be related to, e.g.

    >>> tz_trout.tz_ids_for_phone('+16503334444')
    [u'America/Los_Angeles']
    >>> tz_trout.tz_ids_for_phone('+49 (0)711 400 40990')
    [u'Europe/Berlin', u'Europe/Busingen']
    """

    try:
        phone = phonenumbers.parse(phone, 'US')
    except:
        pass
    else:
        country_iso = phonenumbers.region_code_for_number(phone)
        if country_iso == 'US':
            state = city = None
            area = description_for_number(phone, 'en').split(',')
            if len(area) == 2:
                city = area[0].strip()
                state = area[1].strip()
            elif len(area) == 1 and area[0]:
                state = area[0].lower().strip()
                state = td.normalized_states.get(state, None)

            return tz_ids_for_address(country_iso, state=state, city=city)

        elif country_iso:
            return pytz.country_timezones.get(country_iso)

    return []


def tz_ids_for_address(country, state=None, city=None, zipcode=None, **kwargs):
    """ Get the TZ identifiers for a given address, e.g.:

    >>> tz_trout.tz_ids_for_address('US', state='CA', city='Palo Alto')
    [u'America/Los_Angeles']
    >>> tz_trout.tz_ids_for_address('PL')
    [u'Europe/Warsaw']
    >>> tz_trout.tz_ids_for_address('CN')
    [
        u'Asia/Shanghai',
        u'Asia/Harbin',
        u'Asia/Chongqing',
        u'Asia/Urumqi',
        u'Asia/Kashgar'
    ]
    """

    if country == 'US':
        if zipcode:
            return td.zip_to_tz_ids.get(zipcode)
        elif state or city:
            if len(state) != 2:
                state = td.normalized_states.get(state.lower(), state)
            zipcodes = ZipCodeDatabase().find_zip(city, state)
            if zipcodes:
                return td.zip_to_tz_ids.get(zipcodes[0].zip)
            elif city:
                zipcodes = ZipCodeDatabase().find_zip(None, state)
                if zipcodes:
                    return td.zip_to_tz_ids.get(zipcodes[0].zip)
    else:
        return pytz.country_timezones.get(country)

def tz_ids_for_offset(offset_in_minutes):
    """ Get the TZ identifiers for a given UTC offset (in minutes), e.g.

    >>> tz_trout.tz_ids_for_offset(-7 * 60)  # during DST
    [
        u'America/Creston',
        u'America/Dawson',
        u'America/Dawson_Creek',
        u'America/Hermosillo',
        u'America/Los_Angeles',
        u'America/Phoenix',
        u'America/Santa_Isabel',
        u'America/Tijuana',
        u'America/Vancouver',
        u'America/Whitehorse',
        u'Canada/Pacific',
        u'US/Arizona',
        u'US/Pacific'
    ]
    """
    ids = td.offset_to_tz_ids.get(str(offset_in_minutes))
    valid_ids = []
    if ids:
        # only get the tz ids that match the tz offset currently
        for id in ids:
            tz = pytz.timezone(id)
            try:
                if int(tz.utcoffset(datetime.datetime.utcnow()).total_seconds() / 60) == offset_in_minutes:
                    valid_ids.append(id)
            except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                pass
    return valid_ids

def local_time_for_phone(phone):
    """ Get the local time for a given phone number, e.g.

    >>> datetime.datetime.utcnow()
    datetime.datetime(2013, 9, 17, 19, 44, 0, 966696)
    >>> tz_trout.local_time_for_phone('+16503334444')
    datetime.datetime(2013, 9, 17, 12, 44, 0, 966696, tzinfo=<DstTzInfo 'America/Los_Angeles' PDT-1 day, 17:00:00 DST>)
    """
    ids = tz_ids_for_phone(phone)
    if ids:
        return pytz.timezone(ids[0]).fromutc(datetime.datetime.utcnow())

def local_time_for_address(country, state=None, city=None, zipcode=None, **kwargs):
    """ Get the local time for a given address, e.g.

    >>> datetime.datetime.utcnow()
    datetime.datetime(2013, 9, 17, 19, 44, 0, 966696)
    >>> tz_trout.local_time_for_address('US', state='California')
    datetime.datetime(2013, 9, 17, 12, 44, 0, 966696, tzinfo=<DstTzInfo 'America/Los_Angeles' PDT-1 day, 17:00:00 DST>)
    """
    ids = tz_ids_for_address(country, state, city, zipcode, **kwargs)
    if ids:
        return pytz.timezone(ids[0]).fromutc(datetime.datetime.utcnow())

def offset_ranges_for_local_time(local_start, local_end):
    """ Return a list of UTC offset ranges where the local time is between
    local_start and local_end, e.g.

    >>> tz_trout.offset_ranges_for_local_time(datetime.time(9), datetime.time(17))  # ran at 8pm UTC
    [[-660, -180], [780, 840]]

    local_start and local_end can be instances of datetime.time or integers
    (minutes from midnight).
    """

    # validate
    if not isinstance(local_start, (datetime.time, int)):
        raise ValueError('local_start is not an instance of datetime.time or int')
    if not isinstance(local_end, (datetime.time, int)):
        raise ValueError('local_end is not an instance of datetime.time or int')

    # convert to ints (minutes)
    to_minutes = lambda t: t.hour * 60 + t.minute
    local_start = local_start if isinstance(local_start, int) else to_minutes(local_start)
    local_end = local_end if isinstance(local_end, int) else to_minutes(local_end)

    # get current UTC time
    current_time = to_minutes(datetime.datetime.utcnow().time())

    # tweak for ranges that pass midnight (e.g. (5pm, 9am))
    if local_end < local_start:
        local_end += 24 * 60

    # calculate offsets
    offset_ranges = [
        [local_start - current_time, local_end - current_time],
        [24 * 60 - current_time + local_start, 24 * 60 - current_time + local_end],
        [-24 * 60 - current_time + local_start, -24 * 60 - current_time + local_end]
    ]

    # cap the offsets at UTC-14:00 and UTC+14:00
    capped = lambda t: 14 * 60 if t > 14 * 60 else -14 * 60 if t < -14 * 60 else t
    for i, range in enumerate(offset_ranges):
        offset_ranges[i][0] = capped(range[0])
        offset_ranges[i][1] = capped(range[1])

    # discard the irrelevant ranges (i.e. where start == end)
    offset_ranges = [range for range in offset_ranges if range[0] != range[1]]
    return offset_ranges

def tz_ids_for_offset_range(offset_start, offset_end):
    pass  # TODO

