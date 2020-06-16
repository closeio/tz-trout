import json
import os
import urllib.request
from io import BytesIO
from zipfile import ZipFile

# We download our US Zipcode data from Geonames.org and then store that data
# as an array of dicitionaries in memory
US_ZIPCODE_DATA_DOWNLOAD_URL = (
    'https://download.geonames.org/export/zip/US.zip'
)
US_ZIPCODE_TXT_FILE_NAME = 'US.txt'

basepath = os.path.dirname(os.path.abspath(__file__))
US_ZIPCODE_DATA_PATH = os.path.join(
    basepath, 'tztrout/data/us_zipcode_data.json'
)


def _get_latest_us_zipcode_data():
    """Download the latest Geonames.org US Zipcode data zip file
    and extract the US zipcode information from a txt file located
    inside the downloaded zip.
    """
    url = urllib.request.urlopen(US_ZIPCODE_DATA_DOWNLOAD_URL)
    with ZipFile(BytesIO(url.read())) as us_zipcode_zip_file:
        return us_zipcode_zip_file.open(US_ZIPCODE_TXT_FILE_NAME).readlines()


def generate_us_zipcode_data():
    """Generate a list of US zipcode data from the txt file in the latest
    Geonames.org database and save it as a JSON file.
    """
    us_zipcode_data = []
    us_zipcode_txt_file_data = _get_latest_us_zipcode_data()
    for line in us_zipcode_txt_file_data:
        zip = line.decode().split('\t')
        # The order of fields is documented in the readme file of the
        # geonames download.
        us_zipcode_data.append(
            {
                'zip': zip[1],
                'city': zip[2],
                'state': zip[4],
                'latitude': zip[9],
                'longitude': zip[10],
            }
        )

    with open(US_ZIPCODE_DATA_PATH, 'w') as f:
        json.dump(
            us_zipcode_data,
            f,
            indent=2,
            sort_keys=True,
            separators=(',', ': '),
        )


if __name__ == '__main__':
    generate_us_zipcode_data()
