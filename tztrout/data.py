import cPickle as pickle
import datetime
import dawg
import json
import operator
import os
import pytz
from collections import defaultdict
from sys import stdout

from pyzipcode import ZipCodeDatabase, ZipCode

from tztrout.data_exceptions import data_exceptions


# paths to the data files
basepath = os.path.dirname(os.path.abspath(__file__))
US_ZIPS_TO_TZ_IDS_MAP_PATH = os.path.join(basepath, 'data/us_zips_to_tz_ids.pkl')
TZ_NAME_TO_TZ_IDS_MAP_PATH = os.path.join(basepath, 'data/tz_name_to_tz_ids.json')
OFFSET_TO_TZ_IDS_MAP_PATH = os.path.join(basepath, 'data/offset_to_tz_ids.json')
STATES_PATH = os.path.join(basepath, 'data/normalized_states.json')
ALIASES_PATH = os.path.join(basepath, 'data/tz_name_to_tz_name_aliases.json')
CA_STATE_TO_TZ_IDS_MAP_PATH =  os.path.join(basepath, 'data/ca_state_to_tz_ids.json')
CA_AREA_CODE_TO_STATE_MAP_PATH =  os.path.join(basepath, 'data/ca_area_code_to_state.json')
AU_STATE_TO_TZ_IDS_MAP_PATH =  os.path.join(basepath, 'data/au_state_to_tz_ids.json')
AU_AREA_CODE_TO_STATE_MAP_PATH =  os.path.join(basepath, 'data/au_area_code_to_state.json')


class JSONDawg(object):
    """ Converts a dictionary into a read-only BytesDAWG for performance and
    memory efficiency.
    """

    def __init__(self, doc):
        # transform the key-value pairs into a (key, value) list
        pairs = []
        for key, val in doc.iteritems():
            # convert complex objects into a string
            pairs.append((key, bytes(val)))
        self.data = dawg.BytesDAWG(pairs)

    def get(self, key):
        val = self.data.get(key)
        if val is not None:
            return json.loads(val[0])

    def __getitem__(self, key):
        val = self.data[key]
        if val is not None:
            return json.loads(val[0])


class TroutData(object):
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
        self._load_us_zipcode_data('us_zip_to_tz_ids', US_ZIPS_TO_TZ_IDS_MAP_PATH)
        self._load_data('tz_name_to_tz_ids', TZ_NAME_TO_TZ_IDS_MAP_PATH)
        self._load_data('offset_to_tz_ids', OFFSET_TO_TZ_IDS_MAP_PATH)
        self._load_data('normalized_states', STATES_PATH)
        self._load_data('tz_name_aliases', ALIASES_PATH)
        self._load_data('ca_state_to_tz_ids', CA_STATE_TO_TZ_IDS_MAP_PATH)
        self._load_data('ca_area_code_to_state', CA_AREA_CODE_TO_STATE_MAP_PATH)
        self._load_data('au_state_to_tz_ids', AU_STATE_TO_TZ_IDS_MAP_PATH)
        self._load_data('au_area_code_to_state', AU_AREA_CODE_TO_STATE_MAP_PATH)

        # convert string offsets into integers
        self.offset_to_tz_ids = dict((int(k), v) for k, v in self.offset_to_tz_ids.iteritems())

        # flatten the values of all tz name aliases (needed to identify which
        # filters don't need to be exact in tztrout.tz_ids_for_tz_name
        self.alias_list = reduce(operator.add, [v for v in self.tz_name_aliases.values()])

    def _load_data(self, name, path, dawgify=False):
        """ Helper method to load a data file. """
        if os.path.exists(path):
            with open(path, 'r') as file:
                data = json.loads(file.read())
                setattr(self, name, data)
        else:
            print "Data file is missing: %s" % path

    def _load_us_zipcode_data(self, name, path):
        if os.path.exists(path):
            with open(path, 'r') as file:
                data = pickle.loads(file.read())
                setattr(self, name, JSONDawg({single_k: v for k, v in data.items() for single_k in k}))
        else:
            print "Data file is missing: %s" % path

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
        zips = list(zcdb.find_zip())
        zips_len = len(zips)
        tz_ids_to_zips = defaultdict(list)
        for cnt, zip in enumerate(zips):
            ids = tuple(self._get_tz_identifiers_for_us_zipcode(zip))

            # apply the data exceptions
            exceptions = data_exceptions.get('zip:' + zip.zip) or data_exceptions.get('state:' + zip.state) or {}
            exceptions['include'] = exceptions.get('include', []) + data_exceptions['all'].get('include', []) if 'all' in data_exceptions else []
            exceptions['exclude'] = exceptions.get('exclude', []) + data_exceptions['all'].get('exclude', []) if 'all' in data_exceptions else []
            if exceptions:
                ids = tuple((set(ids) - set(exceptions['exclude'])) | set(exceptions['include']))

            tz_ids_to_zips[ids].append(zip.zip)

            stdout.write('\r%d/%d' % (cnt + 1, zips_len))
            stdout.flush()

        zips_to_tz_ids = {tuple(zips): json.dumps(ids) for ids, zips in tz_ids_to_zips.iteritems()}

        file = open(US_ZIPS_TO_TZ_IDS_MAP_PATH , 'w')
        file.write(pickle.dumps(zips_to_tz_ids))
        file.close()

    def generate_tz_name_to_tz_id_map(self):
        """ Generate the map of timezone names to time zone identifiers.
        """
        tz_name_ids = {}
        tzs_len = len(pytz.common_timezones)
        for cnt, id in enumerate(pytz.common_timezones):
            tz = pytz.timezone(id)
            tz_names = self._get_latest_tz_names(tz)

            # Australian tz names are resolved as EST, WST, etc., which is ok
            # for local usage, but conflicts with the more common US tz names
            # if we're thinking globally. Instead, we should use AWST, ACST,
            # AEST, etc.
            if id.startswith('Australia'):
                au_map = {
                    'WST': 'AWST',
                    'CST': 'ACST',
                    'EST': 'AEST',
                    'CWST': 'AWST',
                    'LHST': 'AEST'
                }
                tz_names = [au_map[tz_name] for tz_name in tz_names]

            # Include the aliases in the map, too
            for name in tz_names:
                tz_names.extend(self.tz_name_aliases.get(name, []))

            for name in tz_names:
                if name in tz_name_ids and id not in tz_name_ids[name]:
                    tz_name_ids[name].append(id)
                elif name not in tz_name_ids:
                    tz_name_ids[name] = [id]

            stdout.write('\r%d/%d' % (cnt + 1, tzs_len))
            stdout.flush()

        file = open(TZ_NAME_TO_TZ_IDS_MAP_PATH, 'w')
        file.write(json.dumps(tz_name_ids))
        file.close()

    def generate_offset_to_tz_id_map(self):
        """ Generate the map of UTC offsets to time zone identifiers.
        """
        offset_tz_ids = defaultdict(list)
        tzs_len = len(pytz.common_timezones)
        for cnt, id in enumerate(pytz.common_timezones):
            tz = pytz.timezone(id)
            offsets = self._get_latest_offsets(tz)
            for offset in offsets:
                offset_tz_ids[offset].append(id)

            stdout.write('\r%d/%d' % (cnt + 1, tzs_len))
            stdout.flush()

        file = open(OFFSET_TO_TZ_IDS_MAP_PATH, 'w')
        file.write(json.dumps(offset_tz_ids))
        file.close()

