### Timezone Trout

This library tries to solve the common problem of figuring out what time zone
a specific address or a phone number is in. It does so by using several
mappings that are generated with the help of pytz (http://pytz.sourceforge.net/)
and pyzipcode (https://github.com/fdintino/pyzipcode).

Current version is fairly accurate for the United States and the countries
with a single time zone.

Vocabulary used in this library:
* PST - time zone name
* America/Los_Angeles - time zone identifier
* UTC-07:00 or -420 - utc offset (the latter given in minutes)
* DST - daylight savings time

#### Examples

```
>>> import tz_trout
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
```

```
>>> tz_trout.tz_ids_for_phone('+16503334444')
[u'America/Los_Angeles']
>>> tz_trout.tz_ids_for_phone('+49 (0)711 400 40990')
[u'Europe/Berlin', u'Europe/Busingen']
```

```
>>> tz_trout.tz_ids_for_address('US', state='CA')
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
```

```
>>> tz_trout.local_time_for_phone('+1 (650) 333-4444')
datetime.datetime(2013, 9, 16, 17, 45, 43, 0000000, tzinfo=<DstTzInfo 'America/Los_Angeles' PDT-1 day, 17:00:00 DST>)

>>> tz_trout.local_time_for_phone('+48 601 941 311)
datetime.datetime(2013, 9, 17, 2, 45, 43, 0000000, tzinfo=<DstTzInfo 'Europe/Warsaw' CEST+2:00:00 DST>)
```

```
>>> tz_trout.local_time_for_address('US', state='CA')
datetime.datetime(2013, 9, 16, 17, 45, 43, 0000000, tzinfo=<DstTzInfo 'America/Los_Angeles' PDT-1 day, 17:00:00 DST>)
>>> tz_trout.local_time_for_address('PL')
datetime.datetime(2013, 9, 17, 2, 45, 43, 0000000, tzinfo=<DstTzInfo 'Europe/Warsaw' CEST+2:00:00 DST>)
```

```
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
>>> tz_trout.tz_ids_for_offset(+2 * 60)  # during DST
[
    "Africa/Blantyre",
    "Africa/Bujumbura",
    "Africa/Cairo",
    "Africa/Ceuta",
    "Africa/Gaborone",
    "Africa/Harare",
    "Africa/Johannesburg",
    "Africa/Kigali",
    "Africa/Lubumbashi",
    "Africa/Lusaka",
    "Africa/Maputo",
    "Africa/Maseru",
    "Africa/Mbabane",
    "Africa/Tripoli",
    "Africa/Windhoek",
    "Arctic/Longyearbyen",
    "Europe/Amsterdam",
    "Europe/Andorra",
    "Europe/Belgrade",
    "Europe/Berlin",
    "Europe/Bratislava",
    "Europe/Brussels",
    "Europe/Budapest",
    "Europe/Busingen",
    "Europe/Copenhagen",
    "Europe/Gibraltar",
    "Europe/Ljubljana",
    "Europe/Luxembourg",
    "Europe/Madrid",
    "Europe/Malta",
    "Europe/Monaco",
    "Europe/Oslo",
    "Europe/Paris",
    "Europe/Podgorica",
    "Europe/Prague",
    "Europe/Rome",
    "Europe/San_Marino",
    "Europe/Sarajevo",
    "Europe/Skopje",
    "Europe/Stockholm",
    "Europe/Tirane",
    "Europe/Vaduz",
    "Europe/Vatican",
    "Europe/Vienna",
    "Europe/Warsaw",
    "Europe/Zagreb",
    "Europe/Zurich"
]
```
