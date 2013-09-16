import tz_trout
import unittest


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

if __name__ == '__main__':
    unittest.main()

