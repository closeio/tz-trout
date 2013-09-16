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

    ids = td.tz_name_to_tz_ids.get(tz_name, [])
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

