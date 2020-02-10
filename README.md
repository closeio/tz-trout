### Timezone Trout

This library tries to solve the common problem of figuring out what time zone
a specific address or a phone number is in. It does so by using several
mappings that are generated with the help of pytz (http://pytz.sourceforge.net/)
and pyzipcode (https://github.com/fdintino/pyzipcode).

Current version is fairly accurate for the United States, Canada, Australia, and
countries which fit within a single time zone.

Vocabulary used in this library:
* PST - time zone name
* America/Los_Angeles - time zone identifier
* UTC-07:00 or -420 - UTC offset (the latter given in minutes)
* DST - Daylight Saving Time

#### Examples

```
>>> import tztrout
>>> tztrout.tz_ids_for_tz_name('PDT')  # ran during DST
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
>>> tztrout.tz_ids_for_tz_name('PDT')  # ran outside of the DST period
[]
```

```
>>> tztrout.tz_ids_for_phone('+16503334444')
[u'America/Los_Angeles']
>>> tztrout.tz_ids_for_phone('+49 (0)711 400 40990')
[u'Europe/Berlin', u'Europe/Busingen']
```

```
>>> tztrout.tz_ids_for_address('US', state='CA')
[u'America/Los_Angeles']
>>> tztrout.tz_ids_for_address('PL')
[u'Europe/Warsaw']
>>> tztrout.tz_ids_for_address('CN')
[
    u'Asia/Shanghai',
    u'Asia/Harbin',
    u'Asia/Chongqing',
    u'Asia/Urumqi',
    u'Asia/Kashgar'
]
```

```
>>> tztrout.local_time_for_phone('+1 (650) 333-4444')
datetime.datetime(2013, 9, 16, 17, 45, 43, 0000000, tzinfo=<DstTzInfo 'America/Los_Angeles' PDT-1 day, 17:00:00 DST>)

>>> tztrout.local_time_for_phone('+48 601 941 311)
datetime.datetime(2013, 9, 17, 2, 45, 43, 0000000, tzinfo=<DstTzInfo 'Europe/Warsaw' CEST+2:00:00 DST>)
```

```
>>> tztrout.local_time_for_address('US', state='CA')
datetime.datetime(2013, 9, 16, 17, 45, 43, 0000000, tzinfo=<DstTzInfo 'America/Los_Angeles' PDT-1 day, 17:00:00 DST>)
>>> tztrout.local_time_for_address('PL')
datetime.datetime(2013, 9, 17, 2, 45, 43, 0000000, tzinfo=<DstTzInfo 'Europe/Warsaw' CEST+2:00:00 DST>)
```

```
>>> tztrout.tz_ids_for_offset(-7 * 60)  # during DST
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
>>> tztrout.tz_ids_for_offset(+2 * 60)  # during DST
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

#### Testing

Just run `pytest`

#### Updates

If any data needs updating, your first step should be to upgrade `pytz` and
`pyzipcode` and then run `python regenerate_data.py`. If this doesn't fix the
problem, consider opening an issue or adding an exception in `data_exceptions.py`.

#### Known Issues

* Australian Central Western Standard Time (CWST) is treated as Australian Central Standard Time (ACST). See [Australian anomalies](http://en.wikipedia.org/wiki/Time_in_Australia#Anomalies) for more details.
* Lord Howe Standard Time (LHST) is treated as Australian Eastern Standard Time (AEST). In reality, they're 30 minutes apart.
* The whole state of British Columbia (Canada) is recognized as Pacific Time, although a small portion of its south-east territory should be recognized as Mountain Time.
* The whole state of Ontario (Canada) is recognized as Eastern Time, although a small portion of its west territory should be recognized as Central Time.
* All +1 867 phone numbers are recognized as Mountain Time, although this prefix is shared by three Canadian territories in the Arctic far north, spanning across Pacific, Mountain, and Central Time.
