import datetime

import pytest
from mock import patch

import tztrout

US_CA_TZ_NAMES = ['PT', 'MT', 'CT', 'ET', 'AT']
AU_TZ_NAMES = ['AWT', 'ACT', 'AET']


def assert_only_one_tz(ids, expected_tz_name, tz_names):
    """Assert that a set of timezone identifiers exists in only one expected timezone across
    a given list of timezones.

    assert_only_one_tz(['America/New_York', America/Detroit'], 'ET', ['CT', 'ET', 'PT'])
    would pass because both 'America/New_York' and 'America/Detroit' are in the 'ET' timezone.

    assert_only_one_tz(['America/New_York', America/Los_Angeles'], 'ET', ['CT', 'ET', 'PT'])
    would fail because 'America/New_York' is in the ET timezone and 'America/Los_Angeles' is
    in the 'PT' timezone.
    """
    assert expected_tz_name in tz_names
    expected_tz_ids = set(tztrout.tz_ids_for_tz_name(expected_tz_name))

    # The given set of timezone ids should have a least one timezone id in commmon
    # with the expected timezone's timezone ids.
    ids = set(ids)
    assert ids & expected_tz_ids

    # The given set of timezone ids should not have any timezone ids in common with
    # any other (non-expected) timezones in the given timezone list.
    non_expected_tz_names = [i for i in tz_names if i != expected_tz_name]
    non_expected_tz_ids = set()
    for tz_name in non_expected_tz_names:
        tz_ids_for_name = set(tztrout.tz_ids_for_tz_name(tz_name))
        non_expected_tz_ids.update(tz_ids_for_name)

    assert not ids & non_expected_tz_ids


class FakeDateTime(datetime.datetime):
    """A datetime replacement that lets you set utcnow()"""

    @classmethod
    def utcnow(cls, *args, **kwargs):
        if hasattr(cls, 'dt'):
            return cls.dt
        raise NotImplementedError(
            'use FakeDateTime.set_utcnow(datetime) first'
        )

    @classmethod
    def set_utcnow(cls, dt):
        cls.dt = dt


class TestTZIdsForPhone:
    @pytest.mark.parametrize(
        'phone, tz_ids',
        [
            ('+1 (650) 333 4444', ['America/Los_Angeles']),
            ('+48 601 941 311', ['Europe/Warsaw']),
        ],
    )
    def test_ids_for_phone(self, phone, tz_ids):
        ids = tztrout.tz_ids_for_phone(phone)
        assert ids == tz_ids

    @pytest.mark.parametrize(
        'phone, tz_name',
        [
            # United States -- Special cases to make sure ET is not counted as part of state timezone
            # Wisconsin
            ('+14143334444', 'CT'),
            # Texas
            ('+12143334444', 'CT'),
            # United States
            # New York, NY
            ('+12123334444', 'ET'),
            ('+16463334444', 'ET'),
            # Los Angeles, CA
            ('+18183334444', 'PT'),
            # Chicago, IL
            ('+16303334444', 'CT'),
            # Houston, TX
            ('+17133334444', 'CT'),
            # Philadelphia, PA
            ('+12153334444', 'ET'),
            # Phoenix, AZ
            ('+16023334444', 'MT'),
            # San Antonio, TX
            ('+12103334444', 'CT'),
            # San Diego, CA
            ('+16193334444', 'PT'),
            # Dallas, TX
            ('+12143334444', 'CT'),
            # San Jose, CA
            ('+14083334444', 'PT'),
            # Austin, TX
            ('+15123334444', 'CT'),
            # Indianapolis, IN
            ('+13173334444', 'ET'),
            # Jacksonville, FL
            ('+19043334444', 'ET'),
            # San Francisco, CA
            ('+14153334444', 'PT'),
            # Columbus, OH
            ('+16143334444', 'ET'),
            # Charlotte, NC
            ('+17043334444', 'ET'),
            # Fort Worth, TX
            ('+16823334444', 'CT'),
            # Detroit, MI
            ('+13133334444', 'ET'),
            # El Paso, TX
            ('+19153334444', 'MT'),
            # Memphis, TN
            ('+19013334444', 'CT'),
            # Denver, CO
            ('+13033334444', 'MT'),
            # Washington, DC
            ('+12023334444', 'ET'),
            # Canada
            # Toronto, ON
            ('+14163334444', 'ET'),
            # Montreal, QC
            ('+15143334444', 'ET'),
            # Calgary, AB
            ('+14033334444', 'MT'),
            # Ottawa, ON
            ('+13433334444', 'ET'),
            ('+16133334444', 'ET'),
            # Edmonton, AB
            ('+17803334444', 'MT'),
            # Mississauga, ON
            ('+12893334444', 'ET'),
            # Winnipeg, MB
            ('+14313334444', 'CT'),
            # Vancouver, BC
            ('+16043334444', 'PT'),
            # Halifax, NS
            ('+19023334444', 'AT'),
            # Saskatoon, SK
            ('+13063334444', 'CT'),
        ],
    )
    def test_major_cities_us_ca(
        self, phone, tz_name,
    ):
        """Make sure all the major cities in the United States and Canada match the right time zone
        (and the right time zone only).
        """
        ids = tztrout.tz_ids_for_phone(phone)
        assert_only_one_tz(ids, tz_name, US_CA_TZ_NAMES)

    @pytest.mark.parametrize(
        'phone, tz_name',
        [
            # NSW - New South Wales
            # WA - Western Australia
            # NT - Northern Territory
            # SA - South Australia
            # TAS - Tasmania
            # VIC - Victoria
            # ACT - Australian Capital Territory
            # QLD - Queensland
            # Sydney, NSW
            ('+61 27 333 4444', 'AET'),
            ('+61 28 333 4444', 'AET'),
            ('+61 29 333 4444', 'AET'),
            # Perth, WA
            ('+61 852 22 4444', 'AWT'),
            ('+61 853 22 4444', 'AWT'),
            ('+61 854 22 4444', 'AWT'),
            ('+61 861 22 4444', 'AWT'),
            ('+61 862 22 4444', 'AWT'),
            ('+61 863 22 4444', 'AWT'),
            ('+61 864 22 4444', 'AWT'),
            ('+61 865 22 4444', 'AWT'),
            # Darwin, NT
            ('+61 879 22 4444', 'ACT'),
            ('+61 889 22 4444', 'ACT'),
            # Adelaide, SA
            ('+61 870 22 4444', 'ACT'),
            ('+61 871 22 4444', 'ACT'),
            ('+61 872 22 4444', 'ACT'),
            ('+61 873 22 4444', 'ACT'),
            ('+61 874 22 4444', 'ACT'),
            ('+61 881 22 4444', 'ACT'),
            ('+61 882 22 4444', 'ACT'),
            ('+61 883 22 4444', 'ACT'),
            ('+61 884 22 4444', 'ACT'),
            # Hobart, TAS
            ('+61 361 22 4444', 'AET'),
            ('+61 362 22 4444', 'AET'),
            # Melbourne, VIC
            ('+61 37 333 4444', 'AET'),
            ('+61 38 333 4444', 'AET'),
            ('+61 39 333 4444', 'AET'),
            # Canberra, ACT
            ('+61 251 22 4444', 'AET'),
            ('+61 252 22 4444', 'AET'),
            ('+61 261 22 4444', 'AET'),
            ('+61 262 22 4444', 'AET'),
            # Brisbane, QLD
            ('+61 72 333 4444', 'AET'),
            ('+61 73 333 4444', 'AET'),
            # Townsville, QLD
            ('+61 744 22 4444', 'AET'),
            ('+61 745 22 4444', 'AET'),
            ('+61 777 22 4444', 'AET'),
        ],
    )
    def test_major_cities_australia(self, phone, tz_name):
        """Make sure all the major cities in Australia match the right time zone
        (and the right time zone only).
        """
        ids = tztrout.tz_ids_for_phone(phone)
        assert_only_one_tz(ids, tz_name, AU_TZ_NAMES)


class TestTZIdsForAddress:
    @pytest.mark.parametrize(
        'country, state, city, zipcode, expected_tz_ids, is_exact_match',
        [
            ('US', 'California', None, None, ['America/Los_Angeles'], True),
            ('US', 'CA', None, None, ['America/Los_Angeles'], True),
            ('US', 'CA', '', None, ['America/Los_Angeles'], True),
            ('US', 'CA', 'Palo Alto', None, ['America/Los_Angeles'], True),
            ('US', '', 'Palo Alto', None, ['America/Los_Angeles'], True),
            ('US', None, 'Palo Alto', None, ['America/Los_Angeles'], True),
            (
                'US',
                '',
                '',
                None,
                ['America/Los_Angeles', 'America/New_York'],
                False,
            ),
            (
                'US',
                None,
                None,
                None,
                ['America/Los_Angeles', 'America/New_York'],
                False,
            ),
            ('PL', None, None, None, ['Europe/Warsaw'], True),
            # Invalid state, assume any US tz
            (
                'US',
                'XX',
                None,
                None,
                ['America/Los_Angeles', 'America/New_York'],
                False,
            ),
            (
                'US',
                'XX',
                '',
                None,
                ['America/Los_Angeles', 'America/New_York'],
                False,
            ),
            # Invalid city with state, ignore city
            ('US', 'CA', 'XX', None, ['America/Los_Angeles'], True),
            # Invalid city without state, assume any US tz
            (
                'US',
                '',
                'XX',
                None,
                ['America/Los_Angeles', 'America/New_York'],
                False,
            ),
            (
                'US',
                None,
                'XX',
                None,
                ['America/Los_Angeles', 'America/New_York'],
                False,
            ),
            (
                'US',
                'California',
                None,
                '94041',
                ['America/Los_Angeles'],
                True,
            ),
            ('US', None, None, '94041', ['America/Los_Angeles'], True),
            ('US', None, None, 94041, ['America/Los_Angeles'], True),
            ('US', None, None, '94041-1191', ['America/Los_Angeles'], True),
            ('US', None, None, '0000', [], True),
        ],
    )
    def test_ids_for_address(
        self, country, state, city, zipcode, expected_tz_ids, is_exact_match
    ):
        ids = tztrout.tz_ids_for_address(
            country, state=state, city=city, zipcode=zipcode
        )
        if is_exact_match:
            assert expected_tz_ids == ids
        else:
            for tz_id in expected_tz_ids:
                assert tz_id in ids

    @pytest.mark.parametrize(
        'country, state, city, tz_name',
        [
            # United States -- Special cases to make sure ET is not counted as part of state timezone
            ('US', 'WI', None, 'CT'),
            ('US', 'TX', None, 'CT'),
            # United States
            ('US', 'NY', 'New York', 'ET'),
            ('US', 'CA', 'Los Angeles', 'PT'),
            ('US', 'IL', 'Chicago', 'CT'),
            ('US', 'TX', 'Houston', 'CT'),
            ('US', 'PA', 'Philadelphia', 'ET'),
            ('US', 'AZ', 'Phoenix', 'MT'),
            ('US', 'TX', 'San Antonio', 'CT'),
            ('US', 'CA', 'San Diego', 'PT'),
            ('US', 'TX', 'Dallas', 'CT'),
            ('US', 'CA', 'San Jose', 'PT'),
            ('US', 'TX', 'Austin', 'CT'),
            ('US', 'IN', 'Indianapolis', 'ET'),
            ('US', 'FL', 'Jacksonville', 'ET'),
            ('US', 'CA', 'San Francisco', 'PT'),
            ('US', 'OH', 'Columbus', 'ET'),
            ('US', 'NC', 'Charlotte', 'ET'),
            ('US', 'TX', 'Fort Worth', 'CT'),
            ('US', 'MI', 'Detroit', 'ET'),
            ('US', 'TX', 'El Paso', 'MT'),
            ('US', 'TN', 'Memphis', 'CT'),
            ('US', 'CO', 'Denver', 'MT'),
            ('US', 'DC', 'Washington', 'ET'),
            # Canada
            ('CA', 'ON', 'Toronto', 'ET'),
            ('CA', 'QC', 'Montreal', 'ET'),
            ('CA', 'AB', 'Calgary', 'MT'),
            ('CA', 'ON', 'Ottawa', 'ET'),
            ('CA', 'AB', 'Edmonton', 'MT'),
            ('CA', 'ON', 'Mississauga', 'ET'),
            ('CA', 'MB', 'Winnipeg', 'CT'),
            ('CA', 'BC', 'Vancouver', 'PT'),
            ('CA', 'NS', 'Halifax', 'AT'),
            ('CA', 'SK', 'Saskatoon', 'CT'),
        ],
    )
    def test_major_cities_us_ca(
        self, country, state, city, tz_name,
    ):
        """Make sure all the major cities in the United States and Canada match the right time zone
        (and the right time zone only).
        """
        ids = tztrout.tz_ids_for_address(country, state=state, city=city)
        assert_only_one_tz(ids, tz_name, US_CA_TZ_NAMES)

    @pytest.mark.parametrize(
        'state, city, tz_name',
        [
            # NSW - New South Wales
            # WA - Western Australia
            # NT - Northern Territory
            # SA - South Australia
            # TAS - Tasmania
            # VIC - Victoria
            # ACT - Australian Capital Territory
            # QLD - Queensland
            ('NSW', 'Sydney', 'AET'),
            ('WA', 'Perth', 'AWT'),
            ('NT', 'Darwin', 'ACT'),
            ('SA', 'Adelaide', 'ACT'),
            ('TAS', 'Hobart', 'AET'),
            ('VIC', 'Melbourne', 'AET'),
            ('ACT', 'Canberra', 'AET'),
            ('QLD', 'Brisbane', 'AET'),
            ('QLD', 'Townsville', 'AET'),
        ],
    )
    def test_major_cities_australia(self, state, city, tz_name):
        """Make sure all the major cities in Australia match the right time zone
        (and the right time zone only).
        """
        ids = tztrout.tz_ids_for_address('AU', state=state, city=city)
        assert_only_one_tz(ids, tz_name, AU_TZ_NAMES)

    def test_australia_without_state_info(self):
        ids = tztrout.tz_ids_for_address('AU')
        expected_ids = [
            "Australia/Sydney",
            "Australia/Perth",
            "Australia/Darwin",
            "Australia/Adelaide",
            "Australia/Darwin",
            "Australia/Adelaide",
            "Australia/Hobart",
            "Australia/Melbourne",
            "Australia/Sydney",
            "Australia/Brisbane",
        ]
        for tz_id in expected_ids:
            assert tz_id in ids

    def test_canada_without_state_info(self):
        ids = tztrout.tz_ids_for_address('CA')
        expected_ids = [
            "America/Whitehorse",
            "America/Vancouver",
            "America/Yellowknife",
            "America/Edmonton",
            "America/Regina",
            "America/Winnipeg",
            "America/Iqaluit",
            "America/Toronto",  # "America/Montreal", TODO re-add Montreal when pytz.country_timezones is fixed
            "America/Moncton",
            "America/Halifax",
            "America/St_Johns",
        ]
        for tz_id in expected_ids:
            assert tz_id in ids

    @pytest.mark.parametrize(
        'zipcode, expected_tz_name',
        [
            ('00501', 'ET'),
            ('01473', 'ET'),
            ('02120', 'ET'),
            ('03342', 'ET'),
            ('04046', 'ET'),
            ('05201', 'ET'),
            ('06108', 'ET'),
            ('07677', 'ET'),
            ('08501', 'ET'),
            ('10709', 'ET'),
            ('11542', 'ET'),
            ('12019', 'ET'),
            ('13052', 'ET'),
            ('14741', 'ET'),
            ('15552', 'ET'),
            ('16701', 'ET'),
            ('17250', 'ET'),
            ('18769', 'ET'),
            ('19399', 'ET'),
            ('20153', 'ET'),
            ('21619', 'ET'),
            ('22485', 'ET'),
            ('23509', 'ET'),
            ('24147', 'ET'),
            ('25503', 'ET'),
            ('26568', 'ET'),
            ('27619', 'ET'),
            ('28409', 'ET'),
            ('29351', 'ET'),
            ('30334', 'ET'),
            ('31764', 'ET'),
            ('32224', 'ET'),
            ('33758', 'ET'),
            ('34280', 'ET'),
            ('35218', 'CT'),
            ('36177', 'CT'),
            ('37304', 'ET'),
            ('38569', 'CT'),
            ('39553', 'CT'),
            ('40964', 'ET'),
            ('41543', 'ET'),
            ('42086', 'CT'),
            ('43338', 'ET'),
            ('44799', 'ET'),
            ('45448', 'ET'),
            ('46135', 'ET'),
            ('47250', 'ET'),
            ('48919', 'ET'),
            ('49565', 'ET'),
            ('50039', 'CT'),
            ('51555', 'CT'),
            ('52101', 'CT'),
            ('53561', 'CT'),
            ('54546', 'CT'),
            ('55128', 'CT'),
            ('56473', 'CT'),
            ('57661', 'MT'),
            ('58079', 'CT'),
            ('59038', 'MT'),
            ('60902', 'CT'),
            ('61477', 'CT'),
            ('62089', 'CT'),
            ('63024', 'CT'),
            ('64674', 'CT'),
            ('65264', 'CT'),
            ('66505', 'CT'),
            ('67578', 'CT'),
            ('68348', 'CT'),
            ('69170', 'CT'),
            ('70175', 'CT'),
            ('71772', 'CT'),
            ('72629', 'CT'),
            ('73622', 'CT'),
            ('74051', 'CT'),
            ('75287', 'CT'),
            ('76164', 'CT'),
            ('77380', 'CT'),
            ('78851', 'CT'),
            ('79405', 'CT'),
            ('80279', 'MT'),
            ('81132', 'MT'),
            ('82443', 'MT'),
            ('83637', 'MT'),
            ('84761', 'MT'),
            ('85671', 'MT'),
            ('86440', 'MT'),
            ('87901', 'MT'),
            ('88023', 'MT'),
            ('89496', 'PT'),
            ('90310', 'PT'),
            ('91950', 'PT'),
            ('92262', 'PT'),
            ('93552', 'PT'),
            ('94080', 'PT'),
            ('95968', 'PT'),
            ('96079', 'PT'),
            ('97470', 'PT'),
            ('98109', 'PT'),
            ('99950', 'PT'),
        ],
    )
    def test_tz_names_for_zipcode_only_addresses(
        self, zipcode, expected_tz_name
    ):
        ids = tztrout.tz_ids_for_address('US', zipcode=zipcode)
        assert_only_one_tz(ids, expected_tz_name, US_CA_TZ_NAMES)


class TestTZIdsForTZName:
    @pytest.mark.parametrize('tz_name', ['PT', 'PACIFIC'])
    def test_ids_for_tz_name(self, tz_name):
        pacific_ids = [
            u'America/Dawson',
            u'America/Fort_Nelson',
            u'America/Los_Angeles',
            u'America/Metlakatla',
            u'America/Tijuana',
            u'America/Vancouver',
            u'America/Whitehorse',
            u'Canada/Pacific',
            u'US/Pacific',
        ]
        ids = tztrout.tz_ids_for_tz_name(tz_name)
        assert ids == pacific_ids


class TestLocalTimeForAddress:
    @patch('datetime.datetime', FakeDateTime)
    def test_local_time_in_spain(self):
        """Make sure local time is properly calculated for Spain."""
        FakeDateTime.set_utcnow(
            datetime.datetime(2016, 9, 13, 22, 15)
        )  # 15:15 PT / 22:15 UTC / 00:15 CEST
        local_time = tztrout.local_time_for_address('ES', city='Barcelona')
        assert str(local_time) == '2016-09-14 00:15:00+02:00'


class TestOffsetRangesForLocalTime:
    @patch('datetime.datetime', FakeDateTime)
    @pytest.mark.parametrize(
        'hour_now, local_time_start, local_time_end, expected_offset_results',
        [
            (
                20,
                datetime.time(9),
                datetime.time(17),
                [[-11 * 60, -3 * 60], [13 * 60, 14 * 60]],
            ),
            (
                0,
                datetime.time(9),
                datetime.time(17),
                [[9 * 60, 14 * 60], [-14 * 60, -7 * 60]],
            ),
            (
                4,
                datetime.time(9),
                datetime.time(17),
                [[5 * 60, 13 * 60], [-14 * 60, -11 * 60]],
            ),
            (7, datetime.time(9), datetime.time(17), [[2 * 60, 10 * 60]]),
            (
                20,
                datetime.time(17),
                datetime.time(9),
                [[-3 * 60, 13 * 60], [-14 * 60, -11 * 60]],
            ),
            (0, datetime.time(17), datetime.time(9), [[-7 * 60, 9 * 60]]),
            (
                4,
                datetime.time(17),
                datetime.time(9),
                [[13 * 60, 14 * 60], [-11 * 60, 5 * 60]],
            ),
            (
                7,
                datetime.time(17),
                datetime.time(9),
                [[10 * 60, 14 * 60], [-14 * 60, 2 * 60]],
            ),
            (20, '9am', '5pm', [[-11 * 60, -3 * 60], [13 * 60, 14 * 60]]),
            (20, '9:00', '17:00', [[-11 * 60, -3 * 60], [13 * 60, 14 * 60]]),
        ],
    )
    def test_offset_ranges(
        self,
        hour_now,
        local_time_start,
        local_time_end,
        expected_offset_results,
    ):
        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, hour_now))
        offset_ranges = tztrout.offset_ranges_for_local_time(
            local_time_start, local_time_end
        )
        assert offset_ranges == expected_offset_results


class TestNonDSTOffsetsForPhone:
    @pytest.mark.parametrize(
        'phone, result',
        [('+1 650 333 4444', [-8 * 60]), ('+1 212 333 4444', [-5 * 60])],
    )
    def test_non_dst_offsets_for_phone(self, phone, result):
        offsets = tztrout.non_dst_offsets_for_phone(phone)
        assert offsets == result


class TestNonDSTOffsetsForAddress:
    @pytest.mark.parametrize(
        'state, result', [('CA', [-8 * 60]), ('NY', [-5 * 60])]
    )
    def test_non_dst_offsets_for_address(self, state, result):
        offsets = tztrout.non_dst_offsets_for_address('US', state=state)
        assert offsets == result
