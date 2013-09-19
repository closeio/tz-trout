import datetime
import json
import os
import pytz
from sys import stdout

from pyzipcode import ZipCodeDatabase, ZipCode
from .utils import build_normalization_map


# paths to the data files
basepath = os.path.dirname(os.path.abspath(__file__))
ZIP_TO_TZ_IDS_MAP_PATH = os.path.join(basepath, 'data/zip_to_tz_id.json')
TZ_NAME_TO_TZ_IDS_MAP_PATH = os.path.join(basepath, 'data/tz_name_to_tz_ids.json')
OFFSET_TO_TZ_IDS_MAP_PATH = os.path.join(basepath, 'data/offset_to_tz_ids.json')
STATES_PATH = os.path.join(basepath, 'data/normalized_states.json')

class TroutData():
    """ Helper class that generates the JSON data used by TZTrout """

    # We don't care about the historic data - we just want to know the recent
    # state of time zones, zip codes, etc. RECENT_YEARS_START describes how
    # far back we should go to check for DST changes, timezone names, etc.
    RECENT_YEARS_START = 2005

    # Sometimes we need to go back a few steps to figure out DSTs, timezone
    # names, etc. This is a kwargs dict that is passed to datetime.timedelta
    # to determine the size of a single step
    TD_STEP = { 'days': 40 }

    def __init__(self):

        # load the data files, if they exist
        if os.path.exists(ZIP_TO_TZ_IDS_MAP_PATH):
            self.zip_to_tz_ids = json.loads(open(ZIP_TO_TZ_IDS_MAP_PATH, 'r').read())
        if os.path.exists(TZ_NAME_TO_TZ_IDS_MAP_PATH):
            self.tz_name_to_tz_ids = json.loads(open(TZ_NAME_TO_TZ_IDS_MAP_PATH, 'r').read())
        if os.path.exists(OFFSET_TO_TZ_IDS_MAP_PATH):
            self.offset_to_tz_ids = json.loads(open(OFFSET_TO_TZ_IDS_MAP_PATH, 'r').read())
        if os.path.exists(STATES_PATH):
            self.normalized_states  = json.loads(open(STATES_PATH, 'r').read())

    def _get_latest_non_dst_offset(self, tz):
        """ Get the UTC offset for a given time zone identifier. Ignore the
        DST offsets.
        """
        dt = datetime.datetime.utcnow()
        while dt.year > self.RECENT_YEARS_START:
            try:
                dst = tz.dst(dt).total_seconds()
                if not dst:
                    return tz.utcoffset(dt)
            except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                pass
            dt -= datetime.timedelta(**self.TD_STEP)

    def _get_latest_offsets(self, tz):
        """ Get all the UTC offsets (in minutes) that a given time zone
        experienced in the recent years.
        """
        dt = datetime.datetime.utcnow()
        offsets = []
        while dt.year > self.RECENT_YEARS_START:
            try:
                offset = int(tz.utcoffset(dt).total_seconds() / 60)
                if offset not in offsets:
                    offsets.append(offset)
            except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                pass
            dt -= datetime.timedelta(**self.TD_STEP)
        return offsets

    def _experiences_dst(self, tz):
        """ Check if the time zone identifier has experienced the DST in the
        recent years.
        """
        dt = datetime.datetime.utcnow()
        while dt.year > self.RECENT_YEARS_START:
            try:
                dst = tz.dst(dt).total_seconds()
                if dst:
                    return True
            except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                pass
            dt -= datetime.timedelta(**self.TD_STEP)
        return False

    def _get_latest_tz_names(self, tz):
        """ Get the recent time zone names for a given time zone identifier.
        """
        dt = datetime.datetime.utcnow()
        tz_names = []
        while dt.year > self.RECENT_YEARS_START:
            try:
                tz_name = tz.tzname(dt)
                if tz_name not in tz_names:
                    tz_names.append(tz_name)
            except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                pass
            dt -= datetime.timedelta(**self.TD_STEP)
        return tz_names

    def _get_tz_identifiers_for_offset(self, country, offset):
        """ Get all the possible time zone identifiers for a given UTC offset.
        Ignore the DST offsets.
        """
        identifiers = pytz.country_timezones.get(country)
        ids = []
        for id in identifiers:
            tz = pytz.timezone(id)
            tz_offset = self._get_latest_non_dst_offset(tz)
            if offset == tz_offset:
                ids.append(id)
        return ids

    def _get_tz_identifiers_for_us_zipcode(self, zipcode):
        """ Get all the possible identifiers for a given US zip code.
        """
        if not isinstance(zipcode, ZipCode):
            zipcode = ZipCodeDatabase().get(zipcode)
            if zipcode:
                zipcode = zipcode[0]
            else:
                return

        # Find all the TZ identifiers with a non-DST offset of zipcode.timezone
        tz_ids = self._get_tz_identifiers_for_offset('US', datetime.timedelta(hours=zipcode.timezone))

        # For each of the found identifiers, cross-reference the DST data from
        # pytz and pyzipcode and only include the identifier if they match
        ret_ids = []
        for id in tz_ids:
            tz = pytz.timezone(id)
            tz_experiences_dst = self._experiences_dst(tz)
            if tz_experiences_dst == bool(zipcode.dst):
                ret_ids.append(id)
        return ret_ids

    def generate_zip_to_tz_id_map(self):
        """ Generate the map of US zip codes to time zone identifiers. The
        method finds all the possible time zone identifiers for each zip code
        based on a UTC offset stored for that zip in pyzipcode.ZipCodeDatabase.
        """
        zcdb = ZipCodeDatabase()
        zip_tz_ids = {}
        zips = list(zcdb.find_zip())
        zips_len = len(zips)
        for cnt, zip in enumerate(zips):
            zip_tz_ids[zip.zip] = self._get_tz_identifiers_for_us_zipcode(zip)

            stdout.write('\r%d/%d' % (cnt + 1, zips_len))
            stdout.flush()

        file = open(ZIP_TO_TZ_IDS_MAP_PATH , 'w')
        file.write(json.dumps(zip_tz_ids))
        file.close()

    def generate_tz_name_to_tz_id_map(self):
        """ Generate the map of timezone names to time zone identifiers.
        """
        tz_name_ids = {}
        tzs_len = len(pytz.common_timezones)
        for cnt, id in enumerate(pytz.common_timezones):
            tz = pytz.timezone(id)
            tz_names = self._get_latest_tz_names(tz)
            for name in tz_names:
                if name in tz_name_ids:
                    tz_name_ids[name].append(id)
                else:
                    tz_name_ids[name] = [id]
            stdout.write('\r%d/%d' % (cnt + 1, tzs_len))
            stdout.flush()

        file = open(TZ_NAME_TO_TZ_IDS_MAP_PATH, 'w')
        file.write(json.dumps(tz_name_ids))
        file.close()

    def generate_offset_to_tz_id_map(self):
        """ Generate the map of UTC offsets to time zone identifiers.
        """
        offset_tz_ids = {}
        tzs_len = len(pytz.common_timezones)
        for cnt, id in enumerate(pytz.common_timezones):
            tz = pytz.timezone(id)
            offsets = self._get_latest_offsets(tz)
            for offset in offsets:
                if offset in offset_tz_ids:
                    offset_tz_ids[offset].append(id)
                else:
                    offset_tz_ids[offset] = [id]
            stdout.write('\r%d/%d' % (cnt + 1, tzs_len))
            stdout.flush()

        print offset_tz_ids
        file = open(OFFSET_TO_TZ_IDS_MAP_PATH, 'w')
        file.write(json.dumps(offset_tz_ids))
        file.close()

