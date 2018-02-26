"""
Flask-Locale
-----------

Adds i18n/l10n support to Flask applications.
"""
from setuptools import setup

setup(
    name='Flask-Locale',
    version='1.0.3',
    url='http://github.com/derkan/flask-locale',
    license='BSD',
    author='Erkan Durmus',
    author_email='derkan@gmail.com',
    description='Adds i18n/l10n support to Flask applications easily. Uses CSV files(or database) to load translations.',
    long_description=open('README.rst').read(),
    packages=['flask_locale'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask',
        'speaklater3'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
