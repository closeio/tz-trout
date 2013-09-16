### Timezone Trout

This library tries to solve the common problem of figuring out what time zone
a specific address or a phone number is in.

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
```

