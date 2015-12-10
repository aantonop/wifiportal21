#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='wifiportal21',
    version = "0.1",
    packages=['wifiportal21'],
    package_data={'wifiportal21': ['templates/*','static/*']},
    include_package_data=True,
    license='http://opensource.org/licenses/MIT',
    author='Andreas M. Antonopoulos',
    url='http://antonopoulos.com',
    author_email='andreas@antonopoulos.com',
    description='A WiFi-for-bitcoin captive portal and authentication server for use with wifidog hotspots',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'two1',
        'flask',
        'qrcode',
        'flask_sqlalchemy',
    ],
    entry_points={
        'console_scripts': [
            'wifiportal21=wifiportal21.auth_server:run_server',
        ],
    },
)
