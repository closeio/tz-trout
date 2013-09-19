import datetime
import tz_trout
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
        ids = tz_trout.tz_ids_for_phone('+1 (650) 333 4444')
        self.assertEqual(ids, ['America/Los_Angeles'])
        ids = tz_trout.tz_ids_for_phone('+48 601 941 311')
        self.assertEqual(ids, ['Europe/Warsaw'])

    def test_ids_for_address(self):
        ids = tz_trout.tz_ids_for_address('US', state='California')
        self.assertEqual(ids, ['America/Los_Angeles'])
        ids = tz_trout.tz_ids_for_address('US', state='CA')
        self.assertEqual(ids, ['America/Los_Angeles'])
        ids = tz_trout.tz_ids_for_address('PL')
        self.assertEqual(ids, ['Europe/Warsaw'])

    @patch('datetime.datetime', FakeDateTime)
    def test_offset_ranges_for_9_to_5(self):
        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 20))  # 8 pm UTC
        offset_ranges = tz_trout.offset_ranges_for_local_time(datetime.time(9), datetime.time(17))
        self.assertEqual(offset_ranges, [
            [-11 * 60, -3 * 60],
            [13 * 60, 14 * 60]
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1))  # 12am UTC
        offset_ranges = tz_trout.offset_ranges_for_local_time(datetime.time(9), datetime.time(17))
        self.assertEqual(offset_ranges, [
            [9 * 60, 14 * 60],
            [-14 * 60, -7 * 60]
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 4))  # 4am UTC
        offset_ranges = tz_trout.offset_ranges_for_local_time(datetime.time(9), datetime.time(17))
        self.assertEqual(offset_ranges, [
            [5 * 60, 13 * 60],
            [-14 * 60, -11 * 60]
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 7))  # 7am UTC
        offset_ranges = tz_trout.offset_ranges_for_local_time(datetime.time(9), datetime.time(17))
        self.assertEqual(offset_ranges, [
            [2 * 60, 10 * 60],
        ])

    @patch('datetime.datetime', FakeDateTime)
    def test_offset_ranges_for_5_to_9(self):
        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 20))  # 8 pm UTC
        offset_ranges = tz_trout.offset_ranges_for_local_time(datetime.time(17), datetime.time(9))
        self.assertEqual(offset_ranges, [
            [-3 * 60, 13 * 60],
            [-14 * 60, -11 * 60]
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1))  # 12am UTC
        offset_ranges = tz_trout.offset_ranges_for_local_time(datetime.time(17), datetime.time(9))
        self.assertEqual(offset_ranges, [
            [-7 * 60, 9 * 60],
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 4))  # 4am UTC
        offset_ranges = tz_trout.offset_ranges_for_local_time(datetime.time(17), datetime.time(9))
        self.assertEqual(offset_ranges, [
            [13 * 60, 14 * 60],
            [-11 * 60, 5 * 60]
        ])

        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 7))  # 7am UTC
        offset_ranges = tz_trout.offset_ranges_for_local_time(datetime.time(17), datetime.time(9))
        self.assertEqual(offset_ranges, [
            [10 * 60, 14 * 60],
            [-14 * 60, 2 * 60]
        ])

    @patch('datetime.datetime', FakeDateTime)
    def test_offset_ranges_for_parsed_time(self):
        FakeDateTime.set_utcnow(datetime.datetime(2013, 1, 1, 20))  # 8 pm UTC
        offset_ranges = tz_trout.offset_ranges_for_local_time('9am', '5 pm')
        self.assertEqual(offset_ranges, [
            [-11 * 60, -3 * 60],
            [13 * 60, 14 * 60]
        ])

        offset_ranges = tz_trout.offset_ranges_for_local_time('9:00', '17:00')
        self.assertEqual(offset_ranges, [
            [-11 * 60, -3 * 60],
            [13 * 60, 14 * 60]
        ])


if __name__ == '__main__':
    unittest.main()

