# -*- coding: utf-8 -*-
"""
Flask-Locale
----


Some code is from Tornado.Locale
"""

import os
import re
import csv
import unicodedata

from flask import _request_ctx_stack, request
from speaklater import make_lazy_string

__all__ = ('Locale', 'refresh', 'translate', 'to_unicode', '_', 'do_translate')


def get_app():
    ctx = _request_ctx_stack.top
    if not ctx:
        return None
    return ctx.app


def to_unicode(value):
    """Converts a string argument to a unicode string.

    If the argument is already a unicode string or None, it is returned
    unchanged.  Otherwise it must be a byte string and is decoded as utf8.
    """
    if isinstance(value, unicode):
        return value
    assert isinstance(value, bytes)
    return value.decode("utf-8")


class Locale(object):
    """Central controller class that can be used to configure how
    Flask-Locale behaves.  Each application that wants to use Flask-Locale
    has to create, or run :meth:`init_app` on, an instance of this class
    after the configuration was initialized.
    """

    def __init__(self, app=None, default_locale='en_US', configure_jinja=True):
        self._default_locale = default_locale
        self._configure_jinja = configure_jinja
        self._supported_locales = frozenset(default_locale)
        self._translations = None
        self.db_loader_func = None
        self.locale_selector_func = None
        self.app = None
        if app:
            self.init_app(app)

    @staticmethod
    def refresh():
        refresh()

    def init_app(self, app):
        """Set up this instance for use with *app*, if no app was passed to
        the constructor.
        """
        self.app = app
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['locale'] = self

        app.config.setdefault('DEFAULT_LOCALE', self._default_locale)
        locale_path = os.path.join(app.root_path, 'translations')
        app.config.setdefault('LOCALE_PATH', locale_path)

        if self._configure_jinja:
            app.jinja_env.add_extension('jinja2.ext.i18n')
            app.jinja_env.install_gettext_callables(
                translate,
                translate,
                newstyle=True
            )

    def load_translations(self, directory):
        """Loads translations from CSV files having locale extension in a directory.

        Translations are strings with optional Python-style named placeholders
        (e.g., ``"My name is %(name)s"``) and their associated translations.

        The directory should have translation files of the form filename: LOCALE,
        e.g. common.es_GT. Translation files should have two or three columns: string,
        translation, and an optional plural indicator. Plural indicators should
        be one of ``"plural"`` or ``"singular"``. A given string can have both singular
        and plural forms. For example ``"%(name)s liked this"`` may have a
        different verb conjugation depending on whether %(name)s is one
        name or a list of names. There should be two rows in the CSV file for
        that string, one with plural indicator "singular", and one "plural".
        For strings with no verbs that would change on translation, simply
        use ``"unknown"`` or the empty string (or don't include the column at all).

        The file is read using the csv module in the default "excel" dialect.
        In this format there should not be spaces after the commas.

        Example translation es_LA.csv::

            "I love you","Te amo"

            "%(name)s liked this","A %(name)s les gust\u00f3 esto","plural"

            "%(name)s liked this","A %(name)s le gust\u00f3 esto","singular"
        """
        app = get_app()
        logger = app.logger
        _translations = {}

        if getattr(self, 'db_loader_func', None):
            trans = self.db_loader_func()
            for row in trans:
                locale = row[0]
                locale = unicodedata.normalize('NFKD', locale).encode('ascii', 'ignore')
                if locale not in _translations:
                    _translations[locale] = {}

                if not row or len(row) < 3:
                    continue
                plural = ('plural' if row[2] == False else 'unknown') or "unknown"
                row = [to_unicode(c).strip() for c in row[1:3]]
                english, translation = row[:2]
                english = unicodedata.normalize('NFKD', english).encode('ascii', 'ignore')
                if plural not in ("plural", "singular", "unknown"):
                    logger.error("Unrecognized plural '%s' indicator for %s", plural, english)
                    continue

                _translations[locale].setdefault(plural, {})[english] = translation
        else:
            for path in os.listdir(directory):
                locale, ext = path.split(".")
                if not re.match("[a-z]+(_[A-Z]+)?$", locale):
                    logger.error("Unrecognized locale %r (path: %s)", locale,
                                 os.path.join(directory, path))
                    continue
                full_path = os.path.join(directory, path)
                try:
                    # python 3: csv.reader requires a file open in text mode.
                    # Force utf8 to avoid dependence on $LANG environment variable.
                    f = open(full_path, "r", encoding="utf-8")
                except TypeError:
                    # python 2: files return byte strings, which are decoded below.
                    # Once we drop python 2.5, this could use io.open instead
                    # on both 2 and 3.
                    f = open(full_path, "r")

                if locale not in _translations:
                    _translations[locale] = {}

                for i, row in enumerate(csv.reader(f, delimiter=',', skipinitialspace=True)):
                    if not row or len(row) < 2:
                        continue
                    row = [to_unicode(c).strip() for c in row]
                    english, translation = row[:2]
                    if len(row) > 2:
                        plural = row[2] or "unknown"
                    else:
                        plural = "unknown"
                    if plural not in ("plural", "singular", "unknown"):
                        logger.error("Unrecognized plural indicator %r in %s line %d",
                                     plural, path, i + 1)
                        continue
                    _translations[locale].setdefault(plural, {})[english] = translation
                f.close()
        _supported_locales = frozenset(_translations.keys())
        self._supported_locales = _supported_locales
        self._translations = _translations

    def db_loader(self, f):
        """Registers a callback function for loading translations
        """
        assert not getattr(self, 'db_loader_func', None), 'a db_loader function is already registered'
        self.db_loader_func = f
        return f

    def localeselector(self, f):
        """Registers a callback function for locale selection.  The default
        behaves as if a function was registered that returns `None` all the
        time.  If `None` is returned, the locale falls back to the one from
        the configuration.

        This has to return the locale as string (eg: ``'de_AT'``, ``'en_US'``)
        """
        assert getattr(self, 'locale_selector_func', None) is None, 'a localeselector function is already registered'
        self.locale_selector_func = f
        return f

    def get_browser_locale(self):
        """Determines the user's locale from Accept-Language header.

        See http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.4
        """

        def get_loc_key(l, s):
            return s

        if "Accept-Language" in request.headers:
            languages = request.headers["Accept-Language"].split(",")
            locales = []
            for language in languages:
                parts = language.strip().split(";")
                if len(parts) > 1 and parts[1].startswith("q="):
                    try:
                        score = float(parts[1][2:])
                    except (ValueError, TypeError):
                        score = 0.0
                else:
                    score = 1.0
                locales.append((parts[0], score))
            if locales:
                # locales.sort(key=lambda(l, s): s, reverse=True)
                locales.sort(key=get_loc_key, reverse=True)
                codes = [l[0] for l in locales]
                return self.get_closest(*codes)
        app = get_app()
        return self.get_closest(app.config['DEFAULT_LOCALE'])

    def get_closest(self, *locale_codes):
        """Returns the closest match for the given locale code."""
        app = get_app()
        if self._translations is None:
            self.load_translations(app.config['LOCALE_PATH'])

        for code in locale_codes:
            if not code:
                continue
            code = code.replace("-", "_")
            parts = code.split("_")
            if code in self._supported_locales:
                return self.get(code)
            for c in self._supported_locales:
                if c.startswith(parts[0].lower()+'_'):
                    return self.get(c)
        return self.get(app.config['DEFAULT_LOCALE'])

    def get(self, code):
        """Returns the translate dict for the given locale code."""
        return self._translations.get(code, {})


def get_translation():
    """Returns the correct gettext translations that should be used for
    this request.  This will never fail and return a dummy translation
    object if used outside of the request or if a translation cannot be
    found.
    """
    app = get_app()
    if not app:
        return None
    locale_instance = app.extensions['locale']
    locale = None
    if getattr(locale_instance, 'locale_selector_func', None):
        rv = locale_instance.locale_selector_func()
        if rv is not None:
            locale = locale_instance.get_closest(rv)
    if locale is None:
        locale = locale_instance.get_browser_locale()
    return locale


def refresh():
    """Refreshes the cached locale information.  This can be used to switch
    a translation between a request and if you want the changes to take place
    immediately, not just with the next request::

        user.locale = request.form['locale']
        refresh()
        flash(translate('Language was changed'))

    Without that refresh, the :func:`~flask.flash` function would probably
    return English text and a now German page.
    """
    app = get_app()
    if not app:
        return None
    app.extensions['locale']._translations = None


def translate(message, **variables):
    return make_lazy_string(do_translate, message, **variables)


_ = translate


def do_translate(message, plural_message=None, count=None):
    """Returns the translation for the given message for this locale.

    If plural_message is given, you must also provide count. We return
    plural_message when count != 1, and we return the singular form
    for the given message when count == 1.
    """
    translation = get_translation()
    if plural_message is not None:
        assert count
        if count != 1:
            message = plural_message
            message_dict = translation.get("plural", {})
        else:
            message_dict = translation.get("singular", {})
    else:
        message_dict = translation.get("singular", None)
        if message_dict is None:
            message_dict = translation.get("unknown", {})
    return str(message_dict.get(message, message))
