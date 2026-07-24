from setuptools import setup

# Temporary integration pin; use a released version before publishing.
NATIVE_PHONENUMBERS = (
    "closeio-phonenumbers @ "
    "https://github.com/closeio/libphonenumber-python/archive/"
    "a4ad9f9802a7e4305649b46972d8c8152fd06751.zip"
    ' ; python_version == "3.12"'
    ' and implementation_name == "cpython"'
    ' and platform_system == "Linux"'
    ' and (platform_machine == "x86_64" or platform_machine == "aarch64")'
)
PURE_PYTHON_PHONENUMBERS = (
    "phonenumbers>=8.3.0"
    ' ; python_version != "3.12"'
    ' or implementation_name != "cpython"'
    ' or platform_system != "Linux"'
    ' or (platform_machine != "x86_64" and platform_machine != "aarch64")'
)

with open("README.md", encoding="utf-8") as file:
    long_description = file.read()

setup(
    name="tz-trout",
    version="1.2.0",
    url="http://github.com/closeio/tz-trout",
    license="MIT",
    author="Close.io",
    author_email="engineering@close.io",
    maintainer="Close.io",
    maintainer_email="engineering@close.io",
    description="Helps you figure out the time zone based on an address or a phone number.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    platforms="any",
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    packages=["tztrout"],
    package_data={"tztrout": ["data/*"]},
    python_requires=">=3.10",
    install_requires=[
        NATIVE_PHONENUMBERS,
        PURE_PYTHON_PHONENUMBERS,
        "python-dateutil",
        "pytz",
    ],
    extras_require={"dev": ["timezonefinder"]},
    tests_require=["mock", "pytest"],
)
