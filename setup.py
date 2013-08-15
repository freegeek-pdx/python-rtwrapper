from setuptools import setup, find_packages
setup(
    name = "request-tracker",
    version = "0.1.1",
    packages = ['request_tracker'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['requests>=0.8'],

    package_data = {
        '': ['*.txt', '*.rst', '*.example'],
    },

    # metadata for upload to PyPI
    author = "Paul Munday",
    author_email = "paulm@freegeek.org",
    description = "This is a package for working with the request tracker API",
    license = "GPLv3 or later",
    keywords = "rt request tracker REST API",
    url = "http://tsbackup/",   # project home page, if any
    long_description = """request-tracker.py is a wrapper around rt.py a python module for the request tracker REST API. It provides friendlier functions that are more specific to Free Geek Tech Supports work flow."""
)
