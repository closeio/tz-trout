from setuptools import setup

setup(
    name='tz-trout',
    version='0.1.3',
    url='http://github.com/closeio/tz-trout',
    license='MIT',
    author='Close.io',
    author_email='engineering@close.io',
    maintainer='Close.io',
    maintainer_email='engineering@close.io',
    description='Helps you figure out the time zone based on an address or a phone number.',
    platforms='any',
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
    ],
    packages=[
        'tztrout',
    ],
    package_data={
        'tztrout': ['data/*']
    },
    install_requires=[
        'dawg',
        'phonenumbers',
        'python-dateutil',
        'pytz',
        'pyzipcode',
    ],
    test_suite='tests',
    tests_require=['mock'],
)
