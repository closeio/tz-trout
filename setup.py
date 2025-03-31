from setuptools import setup

with open("README.md", encoding="utf-8") as file:
    long_description = file.read()

setup(
    name='tz-trout',
    version='1.0.5',
    url='http://github.com/closeio/tz-trout',
    license='MIT',
    author='Close.io',
    author_email='engineering@close.io',
    maintainer='Close.io',
    maintainer_email='engineering@close.io',
    description='Helps you figure out the time zone based on an address or a phone number.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    platforms='any',
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    packages=['tztrout'],
    package_data={'tztrout': ['data/*']},
    python_requires='>=3.8',
    install_requires=['phonenumbers>=8.3.0', 'python-dateutil', 'pytz'],
    extras_require={'dev': ['timezonefinder']},
    tests_require=['mock', 'pytest'],
)
