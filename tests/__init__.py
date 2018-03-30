import datetime
import tztrout
import unittest

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


class TZTroutTestCase(unittest.TestCase):

    def test_ids_for_phone(self):
        ids = tztrout.tz_ids_for_phone('+1 (650) 333 4444')
        self.assertEqual(ids, ['America/Los_Angeles'])
        ids = tztrout.tz_ids_for_phone('+48 601 941 311')
        self.assertEqual(ids, ['Europe/Warsaw'])

    def test_ids_for_address(self):
        ids = tztrout.tz_ids_for_address('US', state='California')
        self.assertEqual(ids, ['America/Los_Angeles'])
        ids = tztrout.tz_ids_for_address('US', state='CA')
        self.assertEqual(ids, ['America/Los_Angeles'])
        ids = tztrout.tz_ids_for_address('US', state='CA', city='')
        self.assertEqual(ids, ['America/Los_Angeles'])
        ids = tztrout.tz_ids_for_address('US', state='CA', city='Palo Alto')
        self.assertEqual(ids, ['America/Los_Angeles'])
        ids = tztrout.tz_ids_for_address('US', state='', city='Palo Alto')
        self.assertEqual(ids, ['America/Los_Angeles'])
        ids = tztrout.tz_ids_for_address('US', city='Palo Alto')
        self.assertEqual(ids, ['America/Los_Angeles'])

        ids = tztrout.tz_ids_for_address('US', state='', city='')
        self.assertTrue('America/Los_Angeles' in ids)
        self.assertTrue('America/New_York' in ids)

        ids = tztrout.tz_ids_for_address('US')
        self.assertTrue('America/Los_Angeles' in ids)
        self.assertTrue('America/New_York' in ids)

        ids = tztrout.tz_ids_for_address('PL')
        self.assertEqual(ids, ['Europe/Warsaw'])

        # Invalid state, assume any US tz
        ids = tztrout.tz_ids_for_address('US', state='XX')
        self.assertTrue('America/Los_Angeles' in ids)
        self.assertTrue('America/New_York' in ids)
        ids = tztrout.tz_ids_for_address('US', state='XX', city='')
        self.assertTrue('America/Los_Angeles' in ids)
        self.assertTrue('America/New_York' in ids)

        # Invalid city with state, ignore city
        ids = tztrout.tz_ids_for_address('US', state='CA', city='XX')
        self.assertEqual(ids, ['America/Los_Angeles'])

        # Invalid city without state, assume any US tz
        ids = tztrout.tz_ids_for_address('US', state='', city='XX')
        self.assertTrue('America/Los_Angeles' in ids)
        self.assertTrue('America/New_York' in ids)
        ids = tztrout.tz_ids_for_address('US', city='XX')
        self.assertTrue('America/Los_Angeles' in ids)
        self.assertTrue('America/New_York' in ids)

    def test_ids_for_address_with_zipcode(self):
        ids = tztrout.tz_ids_for_address('US', state='California', zipcode='94041')
        self.assertEqual(ids, ['America/Los_Angeles'])
        ids = tztrout.tz_ids_for_address('US', zipcode='94041')
        self.assertEqual(ids, ['America/Los_Angeles'])

        # make sure passing an int works, too
        ids = tztrout.tz_ids_for_address('US', zipcode=94041)
        self.assertEqual(ids, ['America/Los_Angeles'])

        # make sure passing an extended zipcode works as well
        ids = tztrout.tz_ids_for_address('US', zipcode='94041-1191')
        self.assertEqual(ids, ['America/Los_Angeles'])

    def test_city_empty_string(self):
        ids = tztrout.tz_ids_for_address('US', state='California', city='')
        self.assertEqual(ids, ['America/Los_Angeles'])

    def test_ids_for_tz_name(self):
        pacific_ids = [
            u'America/Dawson',
            u'America/Los_Angeles',
            u'America/Santa_Isabel',
            u'America/Tijuana',
            u'America/Vancouver',
            u'America/Whitehorse',
            u'Canada/Pacific',
            u'Pacific/Pitcairn',
            u'US/Pacific'
        ]
        ids = tztrout.tz_ids_for_tz_name('PT')
        self.assertEqual(ids, pacific_ids)
        ids = tztrout.tz_ids_for_tz_name('PACIFIC')
        self.assertEqual(ids, pacific_ids)

    def test_non_dst_offsets_for_phone(self):
        offsets = tztrout.non_dst_offsets_for_phone('+1 650 333 4444')
        self.assertEqual(offsets, [-8 * 60])

        offsets = tztrout.non_dst_offsets_for_phone('+1 212 333 4444')
        self.assertEqual(offsets, [-5 * 60])

    def test_non_dst_offsets_for_address(self):
        offsets = tztrout.non_dst_offsets_for_address('US', state='CA')
        self.assertEqual(offsets, [-8 * 60])

        offsets = tztrout.non_dst_offsets_for_address('US', state='NY')
        self.assertEqual(offsets, [-5 * 60])

    @patch('datetime.datetime', FakeDateTime)
    def test_offset_ranges_for_9_to_5(self):
        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 20))  # 8 pm UTC
        offset_ranges = tztrout.offset_ranges_for_local_time(datetime.time(9), datetime.time(17))
        self.assertEqual(offset_ranges, [
            [-11 * 60, -3 * 60],
            [13 * 60, 14 * 60]
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1))  # 12am UTC
        offset_ranges = tztrout.offset_ranges_for_local_time(datetime.time(9), datetime.time(17))
        self.assertEqual(offset_ranges, [
            [9 * 60, 14 * 60],
            [-14 * 60, -7 * 60]
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 4))  # 4am UTC
        offset_ranges = tztrout.offset_ranges_for_local_time(datetime.time(9), datetime.time(17))
        self.assertEqual(offset_ranges, [
            [5 * 60, 13 * 60],
            [-14 * 60, -11 * 60]
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 7))  # 7am UTC
        offset_ranges = tztrout.offset_ranges_for_local_time(datetime.time(9), datetime.time(17))
        self.assertEqual(offset_ranges, [
            [2 * 60, 10 * 60],
        ])

    @patch('datetime.datetime', FakeDateTime)
    def test_offset_ranges_for_5_to_9(self):
        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 20))  # 8 pm UTC
        offset_ranges = tztrout.offset_ranges_for_local_time(datetime.time(17), datetime.time(9))
        self.assertEqual(offset_ranges, [
            [-3 * 60, 13 * 60],
            [-14 * 60, -11 * 60]
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1))  # 12am UTC
        offset_ranges = tztrout.offset_ranges_for_local_time(datetime.time(17), datetime.time(9))
        self.assertEqual(offset_ranges, [
            [-7 * 60, 9 * 60],
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 4))  # 4am UTC
        offset_ranges = tztrout.offset_ranges_for_local_time(datetime.time(17), datetime.time(9))
        self.assertEqual(offset_ranges, [
            [13 * 60, 14 * 60],
            [-11 * 60, 5 * 60]
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 7))  # 7am UTC
        offset_ranges = tztrout.offset_ranges_for_local_time(datetime.time(17), datetime.time(9))
        self.assertEqual(offset_ranges, [
            [10 * 60, 14 * 60],
            [-14 * 60, 2 * 60]
        ])

    @patch('datetime.datetime', FakeDateTime)
    def test_offset_ranges_for_parsed_time(self):
        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 20))  # 8 pm UTC
        offset_ranges = tztrout.offset_ranges_for_local_time('9am', '5 pm')
        self.assertEqual(offset_ranges, [
            [-11 * 60, -3 * 60],
            [13 * 60, 14 * 60]
        ])

        offset_ranges = tztrout.offset_ranges_for_local_time('9:00', '17:00')
        self.assertEqual(offset_ranges, [
            [-11 * 60, -3 * 60],
            [13 * 60, 14 * 60]
        ])

    def test_wisconsin(self):
        """ Make sure WI is not counted as part of ET. """

        ids = tztrout.tz_ids_for_address('US', state='WI')
        ids2 = tztrout.tz_ids_for_address('US', state='Wisconsin')
        ids3 = tztrout.tz_ids_for_phone('+14143334444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assertTrue(all(['Indiana' not in tz_id for tz_id in ids]))
        self.assert_only_one_us_tz(ids, 'CT')

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

    def test_texas(self):
        """ Make sure TX is not counted as part of ET. """

        ids = tztrout.tz_ids_for_address('US', state='TX')
        ids2 = tztrout.tz_ids_for_address('US', state='Texas')
        ids3 = tztrout.tz_ids_for_phone('+12143334444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assertTrue(all(['Indiana' not in tz_id for tz_id in ids]))
        self.assert_only_one_us_tz(ids, 'CT')

    def test_major_cities_us(self):
        """ Make sure all the major cities match the right time zone (and the
        right time zone only). """

        # New York
        ids = tztrout.tz_ids_for_address('US', state='NY', city='New York')
        ids2 = tztrout.tz_ids_for_phone('+12123334444')
        ids3 = tztrout.tz_ids_for_phone('+16463334444')
        self.assertEqual(ids, ids2)
        self.assertEqual(ids, ids3)
        self.assert_only_one_us_tz(ids, 'ET')

        # Los Angeles
        ids = tztrout.tz_ids_for_address('US', state='CA', city='Los Angeles')
        ids2 = tztrout.tz_ids_for_phone('+18183334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'PT')

        # Chicago
        ids = tztrout.tz_ids_for_address('US', state='IL', city='Chicago')
        ids2 = tztrout.tz_ids_for_phone('+16303334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'CT')

        # Houston
        ids = tztrout.tz_ids_for_address('US', state='TX', city='Houston')
        ids2 = tztrout.tz_ids_for_phone('+17133334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'CT')

        # Philadelphia
        ids = tztrout.tz_ids_for_address('US', state='PA', city='Philadelphia')
        ids2 = tztrout.tz_ids_for_phone('+12153334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'ET')

        # Phoenix
        ids = tztrout.tz_ids_for_address('US', state='AZ', city='Phoenix')
        ids2 = tztrout.tz_ids_for_phone('+16023334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'MT')

        # San Antonio
        ids = tztrout.tz_ids_for_address('US', state='TX', city='San Antonio')
        ids2 = tztrout.tz_ids_for_phone('+12103334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'CT')

        # San Diego
        ids = tztrout.tz_ids_for_address('US', state='CA', city='San Diego')
        ids2 = tztrout.tz_ids_for_phone('+16193334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'PT')

        # Dallas
        ids = tztrout.tz_ids_for_address('US', state='TX', city='Dallas')
        ids2 = tztrout.tz_ids_for_phone('+12143334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'CT')

        # San Jose
        ids = tztrout.tz_ids_for_address('US', state='CA', city='San Jose')
        ids2 = tztrout.tz_ids_for_phone('+14083334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'PT')

        # Austin
        ids = tztrout.tz_ids_for_address('US', state='TX', city='Austin')
        ids2 = tztrout.tz_ids_for_phone('+15123334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'CT')

        # Indianapolis
        ids = tztrout.tz_ids_for_address('US', state='IN', city='Indianapolis')
        ids2 = tztrout.tz_ids_for_phone('+13173334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'ET')

        # Jacksonville
        ids = tztrout.tz_ids_for_address('US', state='FL', city='Jacksonville')
        ids2 = tztrout.tz_ids_for_phone('+19043334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'ET')

        # San Francisco
        ids = tztrout.tz_ids_for_address('US', state='CA', city='San Francisco')
        ids2 = tztrout.tz_ids_for_phone('+14153334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'PT')

        # Columbus
        ids = tztrout.tz_ids_for_address('US', state='OH', city='Columbus')
        ids2 = tztrout.tz_ids_for_phone('+16143334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'ET')

        # Charlotte
        ids = tztrout.tz_ids_for_address('US', state='NC', city='Charlotte')
        ids2 = tztrout.tz_ids_for_phone('+17043334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'ET')

        # Fort Worth
        ids = tztrout.tz_ids_for_address('US', state='TX', city='Fort Worth')
        ids2 = tztrout.tz_ids_for_phone('+16823334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'CT')

        # Detroit
        ids = tztrout.tz_ids_for_address('US', state='MI', city='Detroit')
        ids2 = tztrout.tz_ids_for_phone('+13133334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'ET')

        # El Paso
        ids = tztrout.tz_ids_for_address('US', state='TX', city='El Paso')
        ids2 = tztrout.tz_ids_for_phone('+19153334444')
        self.assert_only_one_us_tz(ids, 'MT')
        self.assert_only_one_us_tz(ids2, 'MT')

        # Memphis
        ids = tztrout.tz_ids_for_address('US', state='TN', city='Memphis')
        ids2 = tztrout.tz_ids_for_phone('+19013334444')
        self.assert_only_one_us_tz(ids, 'CT')
        self.assert_only_one_us_tz(ids2, 'CT')

        # Denver
        ids = tztrout.tz_ids_for_address('US', state='CO', city='Denver')
        ids2 = tztrout.tz_ids_for_phone('+13033334444')
        self.assertEqual(ids, ids2)
        self.assert_only_one_us_tz(ids, 'MT')

        # Washington
        ids = tztrout.tz_ids_for_address('US', state='DC', city='Washington')
        ids2 = tztrout.tz_ids_for_phone('+12023334444')
        self.assert_only_one_us_tz(ids, 'ET')
        self.assert_only_one_us_tz(ids2, 'ET')

    def test_major_cities_canada(self):
        """ Make sure all the major cities match the right time zone (and the
        right time zone only). """

        # Toronto, Ontario
        ids = tztrout.tz_ids_for_address('CA', state='ON', city='Toronto')
        ids2 = tztrout.tz_ids_for_phone('+14163334444')
        self.assert_only_one_us_tz(ids, 'ET')
        self.assert_only_one_us_tz(ids2, 'ET')

        # Montreal, Quebec
        ids = tztrout.tz_ids_for_address('CA', state='QC', city='Montreal')
        ids2 = tztrout.tz_ids_for_phone('+15143334444')
        self.assert_only_one_us_tz(ids, 'ET')
        self.assert_only_one_us_tz(ids2, 'ET')

        # Calgary, Alberta
        ids = tztrout.tz_ids_for_address('CA', state='AB', city='Calgary')
        ids2 = tztrout.tz_ids_for_phone('+14033334444')
        self.assert_only_one_us_tz(ids, 'MT')
        self.assert_only_one_us_tz(ids2, 'MT')

        # Ottawa, Ontario
        ids = tztrout.tz_ids_for_address('CA', state='ON', city='Ottawa')
        ids2 = tztrout.tz_ids_for_phone('+13433334444')
        ids3 = tztrout.tz_ids_for_phone('+16133334444')
        self.assert_only_one_us_tz(ids, 'ET')
        self.assert_only_one_us_tz(ids2, 'ET')
        self.assert_only_one_us_tz(ids3, 'ET')

        # Edmonton, Alberta
        ids = tztrout.tz_ids_for_address('CA', state='AB', city='Edmonton')
        ids2 = tztrout.tz_ids_for_phone('+17803334444')
        self.assert_only_one_us_tz(ids, 'MT')
        self.assert_only_one_us_tz(ids2, 'MT')

        # Mississauga, Ontario
        ids = tztrout.tz_ids_for_address('CA', state='ON', city='Mississauga')
        ids2 = tztrout.tz_ids_for_phone('+12893334444')
        self.assert_only_one_us_tz(ids, 'ET')
        self.assert_only_one_us_tz(ids2, 'ET')

        # Winnipeg, Manitoba
        ids = tztrout.tz_ids_for_address('CA', state='MB', city='Winnipeg')
        ids2 = tztrout.tz_ids_for_phone('+14313334444')
        self.assert_only_one_us_tz(ids, 'CT')
        self.assert_only_one_us_tz(ids2, 'CT')

        # Vancouver, British Columbia
        ids = tztrout.tz_ids_for_address('CA', state='BC', city='Vancouver')
        ids2 = tztrout.tz_ids_for_phone('+16043334444')
        self.assert_only_one_us_tz(ids, 'PT')
        self.assert_only_one_us_tz(ids2, 'PT')

        # Halifax, Nova Scotia
        ids = tztrout.tz_ids_for_address('CA', state='NS', city='Halifax')
        ids2 = tztrout.tz_ids_for_phone('+19023334444')
        self.assert_only_one_us_tz(ids, 'AT')
        self.assert_only_one_us_tz(ids2, 'AT')

        # Saskatoon, Saskatchewan - CT that doesn't observe DST
        ids = tztrout.tz_ids_for_address('CA', state='SK', city='Saskatoon')
        ids2 = tztrout.tz_ids_for_phone('+13063334444')
        self.assert_only_one_us_tz(ids, 'CT')
        self.assert_only_one_us_tz(ids2, 'CT')

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

