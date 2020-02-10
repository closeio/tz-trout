import datetime
import tztrout
import unittest
import pytest

from mock import patch


class FakeDateTime(datetime.datetime):
    "A datetime replacement that lets you set utcnow()"

    @classmethod
    def utcnow(cls, *args, **kwargs):
        if hasattr(cls, 'dt'):
            return cls.dt
        raise NotImplementedError('use FakeDateTime.set_utcnow(datetime) first')

    @classmethod
    def set_utcnow(cls, dt):
        cls.dt = dt

class TestTZTrout:
    
    def assert_only_one_tz(self, ids, tz_name, tz_names):
         """ Assert that a given set of timezone ids only matches one tz name
         in a given set of tz names
         """
         tz_names_copy = tz_names[:]
         assert tz_name in tz_names_copy
         tz_names_copy.remove(tz_name)
         assert (set(tztrout.tz_ids_for_tz_name(tz_name)) & set(ids))
         for other_name in tz_names_copy:
             assert not (set(tztrout.tz_ids_for_tz_name(other_name)) & set(ids))

    @pytest.fixture
    def us_ca_tz_names(self):
        return ['PT', 'MT', 'CT', 'ET', 'AT']
    
    @pytest.fixture 
    def au_tz_names(self):
        return ['AWT', 'ACT', 'AET']
        
    @pytest.mark.parametrize('phone, tz_ids', [
        ('+1 (650) 333 4444', ['America/Los_Angeles']),
        ('+48 601 941 311', ['Europe/Warsaw'])
    ])
    def test_ids_for_phone(self, phone, tz_ids):
        ids = tztrout.tz_ids_for_phone(phone)
        assert ids == tz_ids
    
    @pytest.mark.parametrize('country, state, city, zipcode, tz_ids, assume_any_tz', [
        ('US', 'California', None, None, ['America/Los_Angeles'], False),
        ('US', 'CA', None, None, ['America/Los_Angeles'], False),
        ('US', 'CA', '', None, ['America/Los_Angeles'], False),
        ('US', 'CA', 'Palo Alto', None, ['America/Los_Angeles'], False),
        ('US', '', 'Palo Alto', None, ['America/Los_Angeles'], False),
        ('US', None, 'Palo Alto', None, ['America/Los_Angeles'], False),
        ('US', '', '', None, ['America/Los_Angeles', 'America/New_York'], True),
        ('US', None, None, None, ['America/Los_Angeles', 'America/New_York'], True),
        ('PL', None, None, None, ['Europe/Warsaw'], False),
        # Invalid state, assume any US tz
        ('US', 'XX', None, None, ['America/Los_Angeles', 'America/New_York'], True),
        ('US', 'XX', '', None, ['America/Los_Angeles', 'America/New_York'], True),
        # Invalid city with state, ignore city
        ('US', 'CA', 'XX', None, ['America/Los_Angeles'], False),
        # Invalid city without state, assume any US tz
        ('US', '', 'XX', None, ['America/Los_Angeles', 'America/New_York'], True),
        ('US', None, 'XX', None, ['America/Los_Angeles', 'America/New_York'], True),
        ('US', 'California', None, '94041', ['America/Los_Angeles'], False),
        ('US', None, None, '94041', ['America/Los_Angeles'], False),
        ('US', None, None, 94041, ['America/Los_Angeles'], False),
        ('US', None, None, '94041-1191', ['America/Los_Angeles'], False),
        ('US', None, None, '0000', [], False),
    ])
    def test_ids_for_address(self, country, state, city, zipcode, tz_ids, assume_any_tz):
        ids = tztrout.tz_ids_for_address(country, state=state, city=city, zipcode=zipcode)
        if assume_any_tz:
            for tz_id in tz_ids:
                assert tz_id in ids
        else:
            assert tz_ids == ids
    
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
            u'US/Pacific'
        ]
        ids = tztrout.tz_ids_for_tz_name(tz_name)
        assert ids == pacific_ids
    
    @pytest.mark.parametrize('phone, result', [
        ('+1 650 333 4444', [-8 * 60]),
        ('+1 212 333 4444', [-5 * 60])
    ])
    def test_non_dst_offsets_for_phone(self, phone, result):
        offsets = tztrout.non_dst_offsets_for_phone(phone)
        assert offsets == result
    
    @pytest.mark.parametrize('state, result', [
        ('CA', [-8 * 60]),
        ('NY', [-5 * 60])
    ])
    def test_non_dst_offsets_for_address(self, state, result):
        offsets = tztrout.non_dst_offsets_for_address('US', state=state)
        assert offsets == result
    
    @patch('datetime.datetime', FakeDateTime)
    @pytest.mark.parametrize('hour_now, range_start, range_end, result', [
        (20, datetime.time(9), datetime.time(17), [
            [-11 * 60, -3 * 60],
            [13 * 60, 14 * 60]
        ]),
        (0, datetime.time(9), datetime.time(17), [
            [9 * 60, 14 * 60],
            [-14 * 60, -7 * 60]
        ]),
        (4, datetime.time(9), datetime.time(17), [
            [5 * 60, 13 * 60],
            [-14 * 60, -11 * 60]
        ]),
        (7, datetime.time(9), datetime.time(17), [
            [2 * 60, 10 * 60],
        ]),
        (20, datetime.time(17), datetime.time(9), [
            [-3 * 60, 13 * 60],
            [-14 * 60, -11 * 60]
        ]),
        (0, datetime.time(17), datetime.time(9), [
            [-7 * 60, 9 * 60],
        ]),
        (4, datetime.time(17), datetime.time(9), [
            [13 * 60, 14 * 60],
            [-11 * 60, 5 * 60]
        ]),
        (7, datetime.time(17), datetime.time(9), [
            [10 * 60, 14 * 60],
            [-14 * 60, 2 * 60]
        ]),
        (20, '9am', '5pm', [
            [-11 * 60, -3 * 60],
            [13 * 60, 14 * 60]
        ]),
        (20, '9:00', '17:00', [
            [-11 * 60, -3 * 60],
            [13 * 60, 14 * 60]
        ])
    ])
    def test_offset_ranges(self, hour_now, range_start, range_end, result):
        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, hour_now))
        offset_ranges = tztrout.offset_ranges_for_local_time(range_start, range_end)
        assert offset_ranges == result
    
    @pytest.mark.parametrize('country, state, city, phones, tz_name, assert_ids_equal', [
        # United States -- Special cases to make sure ET is not counted as part of state timezone
        ('US', 'WI', None, ['+14143334444'], 'CT', True),
        ('US', 'TX', None, ['+12143334444'], 'CT', True),
        # United States
        ('US', 'NY', 'New York', ['+12123334444', '+16463334444'], 'ET', True),
        ('US', 'CA', 'Los Angeles', ['+18183334444'], 'PT', True),
        ('US', 'IL', 'Chicago', ['+16303334444'], 'CT', True),
        ('US', 'TX', 'Houston', ['+17133334444'], 'CT', True),
        ('US', 'PA', 'Philadelphia', ['+12153334444'], 'ET', True),
        ('US', 'AZ', 'Phoenix', ['+16023334444'], 'MT', True),
        ('US', 'TX', 'San Antonio', ['+12103334444'], 'CT', True),
        ('US', 'CA', 'San Diego', ['+16193334444'], 'PT', True),
        ('US', 'TX', 'Dallas', ['+12143334444'], 'CT', True),
        ('US', 'CA', 'San Jose', ['+14083334444'], 'PT', True),
        ('US', 'TX', 'Austin', ['+15123334444'], 'CT', True),
        ('US', 'IN', 'Indianapolis', ['+13173334444'], 'ET', True),
        ('US', 'FL', 'Jacksonville', ['+19043334444'], 'ET', True),
        ('US', 'CA', 'San Francisco', ['+14153334444'], 'PT', True),
        ('US', 'OH', 'Columbus', ['+16143334444'], 'ET', True),
        ('US', 'NC', 'Charlotte', ['+17043334444'], 'ET', True),
        ('US', 'TX', 'Fort Worth', ['+16823334444'], 'CT', True),
        ('US', 'MI', 'Detroit', ['+13133334444'], 'ET', True),
        ('US', 'TX', 'El Paso', ['+19153334444'], 'MT', False),
        ('US', 'TN', 'Memphis', ['+19013334444'], 'CT', False),
        ('US', 'CO', 'Denver', ['+13033334444'], 'MT', True),
        ('US', 'DC', 'Washington', ['+12023334444'], 'ET', False),
        ('CA', 'ON', 'Toronto', ['+14163334444'], 'ET', False),
        ('CA', 'QC', 'Montreal', ['+15143334444'], 'ET', False),
        ('CA', 'AB', 'Calgary', ['+14033334444'], 'MT', False),
        ('CA', 'ON', 'Ottawa', ['+13433334444', '+16133334444'], 'ET', False),
        ('CA', 'AB', 'Edmonton', ['+17803334444'], 'MT', False),
        ('CA', 'ON', 'Mississauga', ['+12893334444'], 'ET', False),
        ('CA', 'MB', 'Winnipeg', ['+14313334444'], 'CT', False),
        ('CA', 'BC', 'Vancouver', ['+16043334444'], 'PT', False),
        ('CA', 'NS', 'Halifax', ['+19023334444'], 'AT', False),
        ('CA', 'SK', 'Saskatoon', ['+13063334444'], 'CT', False), 
    ])
    def test_major_cities_us_ca(self, country, state, city, phones, tz_name, assert_ids_equal, us_ca_tz_names):
        """ Make sure all the major cities in the United States and Canada the right time zone 
        (and the right time zone only). """
        ids = tztrout.tz_ids_for_address(country, state=state, city=city)
        for phone in phones:
            ids2 = tztrout.tz_ids_for_phone(phone)
            if assert_ids_equal:
                assert ids == ids2
            else:
                self.assert_only_one_tz(ids2, tz_name, us_ca_tz_names)
        self.assert_only_one_tz(ids, tz_name, us_ca_tz_names)
        

class TZTroutTestCase(unittest.TestCase):

    def assert_only_one_us_tz(self, ids, tz_name):
        """ Assert that a given set of timezone ids only matches one tz name
        in North America.
        """
        tz_names = ['PT', 'MT', 'CT', 'ET', 'AT']
        self.assertTrue(tz_name in tz_names)
        tz_names.remove(tz_name)
        self.assertTrue(set(tztrout.tz_ids_for_tz_name(tz_name)) & set(ids))
        for other_name in tz_names:
            self.assertFalse(set(tztrout.tz_ids_for_tz_name(other_name)) & set(ids))

    def test_canada_without_state_info(self):
        ids = tztrout.tz_ids_for_address('CA')
        expected_ids = [
            "America/Whitehorse", "America/Vancouver", "America/Yellowknife",
            "America/Edmonton", "America/Regina", "America/Winnipeg",
            "America/Iqaluit", "America/Toronto", #"America/Montreal", TODO re-add Montreal when pytz.country_timezones is fixed
            "America/Moncton", "America/Halifax", "America/St_Johns"
        ]
        for tz_id in expected_ids:
            self.assertTrue(tz_id in ids, tz_id + ' not present in the expected ids set')

    def assert_only_one_au_tz(self, ids, tz_name):
        """ Assert that a given set of timezone ids only matches one tz name
        in Australia.
        """
        tz_names = ['AWT', 'ACT', 'AET']
        self.assertTrue(tz_name in tz_names)
        tz_names.remove(tz_name)
        self.assertTrue(set(tztrout.tz_ids_for_tz_name(tz_name)) & set(ids))
        for other_name in tz_names:
            self.assertFalse(set(tztrout.tz_ids_for_tz_name(other_name)) & set(ids))

    def test_major_cities_australia(self):

        # NSW - New South Wales
        # WA - Western Australia
        # NT - Northern Territory
        # SA - South Australia
        # TAS - Tasmania
        # VIC - Victoria
        # ACT - Australian Capital Territory
        # QLD - Queensland

        # Sydney, NSW
        ids = tztrout.tz_ids_for_address('AU', state='NSW', city='Sydney')
        ids2 = tztrout.tz_ids_for_phone('+61 27 333 4444')
        ids3 = tztrout.tz_ids_for_phone('+61 28 333 4444')
        ids4 = tztrout.tz_ids_for_phone('+61 29 333 4444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assertEqual(ids, ids4)
        self.assert_only_one_au_tz(ids, 'AET')

        # Perth, WA
        ids = tztrout.tz_ids_for_address('AU', state='WA', city='Perth')
        ids2 = tztrout.tz_ids_for_phone('+61 852 22 4444')
        ids3 = tztrout.tz_ids_for_phone('+61 853 22 4444')
        ids4 = tztrout.tz_ids_for_phone('+61 854 22 4444')
        ids5 = tztrout.tz_ids_for_phone('+61 861 22 4444')
        ids6 = tztrout.tz_ids_for_phone('+61 862 22 4444')
        ids7 = tztrout.tz_ids_for_phone('+61 863 22 4444')
        ids8 = tztrout.tz_ids_for_phone('+61 864 22 4444')
        ids9 = tztrout.tz_ids_for_phone('+61 865 22 4444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assertEqual(ids, ids4)
        self.assertEqual(ids, ids5)
        self.assertEqual(ids, ids6)
        self.assertEqual(ids, ids7)
        self.assertEqual(ids, ids8)
        self.assertEqual(ids, ids9)
        self.assert_only_one_au_tz(ids, 'AWT')

        # Darwin, NT
        ids = tztrout.tz_ids_for_address('AU', state='NT', city='Darwin')
        ids2 = tztrout.tz_ids_for_phone('+61 879 22 4444')
        ids3 = tztrout.tz_ids_for_phone('+61 889 22 4444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assert_only_one_au_tz(ids, 'ACT')

        # Eucla, WA - ignore for now
        # "Eucla and the surrounding area, notably Mundrabilla and Madura, use
        # the Central Western Time Zone of UTC+8:45. Although it has no official
        # sanction, it is universally observed in this area, stopping just to
        # the east of Caiguna.

        # Adelaide, SA
        ids = tztrout.tz_ids_for_address('AU', state='SA', city='Adelaide')
        ids2 = tztrout.tz_ids_for_phone('+61 870 22 4444')
        ids3 = tztrout.tz_ids_for_phone('+61 871 22 4444')
        ids4 = tztrout.tz_ids_for_phone('+61 872 22 4444')
        ids5 = tztrout.tz_ids_for_phone('+61 873 22 4444')
        ids6 = tztrout.tz_ids_for_phone('+61 874 22 4444')
        ids7 = tztrout.tz_ids_for_phone('+61 881 22 4444')
        ids8 = tztrout.tz_ids_for_phone('+61 882 22 4444')
        ids9 = tztrout.tz_ids_for_phone('+61 883 22 4444')
        ids10 = tztrout.tz_ids_for_phone('+61 884 22 4444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assertEqual(ids, ids4)
        self.assertEqual(ids, ids5)
        self.assertEqual(ids, ids6)
        self.assertEqual(ids, ids7)
        self.assertEqual(ids, ids8)
        self.assertEqual(ids, ids9)
        self.assertEqual(ids, ids10)
        self.assert_only_one_au_tz(ids, 'ACT')

        # Hobart, TAS
        ids = tztrout.tz_ids_for_address('AU', state='TAS', city='Hobart')
        ids2 = tztrout.tz_ids_for_phone('+61 361 22 4444')
        ids3 = tztrout.tz_ids_for_phone('+61 362 22 4444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assert_only_one_au_tz(ids, 'AET')

        # Melbourne, VIC
        ids = tztrout.tz_ids_for_address('AU', state='VIC', city='Melbourne')
        ids2 = tztrout.tz_ids_for_phone('+61 37 333 4444')
        ids3 = tztrout.tz_ids_for_phone('+61 38 333 4444')
        ids4 = tztrout.tz_ids_for_phone('+61 39 333 4444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assertEqual(ids, ids4)
        self.assert_only_one_au_tz(ids, 'AET')

        # Canberra, ACT
        ids = tztrout.tz_ids_for_address('AU', state='ACT', city='Canberra')
        ids2 = tztrout.tz_ids_for_phone('+61 251 22 4444')
        ids3 = tztrout.tz_ids_for_phone('+61 252 22 4444')
        ids4 = tztrout.tz_ids_for_phone('+61 261 22 4444')
        ids5 = tztrout.tz_ids_for_phone('+61 262 22 4444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assertEqual(ids, ids4)
        self.assertEqual(ids, ids5)
        self.assert_only_one_au_tz(ids, 'AET')

        # Brisbane, QLD
        ids = tztrout.tz_ids_for_address('AU', state='QLD', city='Brisbane')
        ids2 = tztrout.tz_ids_for_phone('+61 72 333 4444')
        ids3 = tztrout.tz_ids_for_phone('+61 73 333 4444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assert_only_one_au_tz(ids, 'AET')

        # Townsville, QLD
        ids = tztrout.tz_ids_for_address('AU', state='QLD', city='Brisbane')
        ids2 = tztrout.tz_ids_for_phone('+61 744 22 4444')
        ids3 = tztrout.tz_ids_for_phone('+61 745 22 4444')
        ids4 = tztrout.tz_ids_for_phone('+61 777 22 4444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assertEqual(ids, ids4)
        self.assert_only_one_au_tz(ids, 'AET')

    def test_australia_without_state_info(self):
        ids = tztrout.tz_ids_for_address('AU')
        expected_ids = ["Australia/Sydney", "Australia/Perth", "Australia/Darwin",
            "Australia/Adelaide", "Australia/Darwin", "Australia/Adelaide",
            "Australia/Hobart", "Australia/Melbourne", "Australia/Sydney",
            "Australia/Brisbane"
        ]
        for tz_id in expected_ids:
            self.assertTrue(tz_id in ids, tz_id + ' not present in the expected ids set')

    @patch('datetime.datetime', FakeDateTime)
    def test_local_time_in_spain(self):
        """Make sure local time is properly calculated for Spain."""
        FakeDateTime.set_utcnow(datetime.datetime(2016, 9, 13, 22, 15))  # 15:15 PT / 22:15 UTC / 00:15 CEST
        local_time = tztrout.local_time_for_address('ES', city='Barcelona')
        self.assertEqual(str(local_time), '2016-09-14 00:15:00+02:00')


if __name__ == '__main__':
    unittest.main()

