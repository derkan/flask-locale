# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, g
from flask_locale import Locale, _

app = Flask(__name__)
app.config['DEFAULT_LOCALE'] = 'tr_TR'
app.config['LOCALE_PATH'] = 'translations'

locale = Locale(app)


@locale.localeselector
def get_locale():
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support tr/fr/en in this
    # example.  The best match wins.
    return request.accept_languages.best_match(['tr_TR', 'fr_FR', 'en_US'])


@app.route("/")
def index():
    # How we do translation in python code:
    py_translated = _('Hello')
    # How we do translation in template:
    return render_template('locale.html', name='Erkan', py_translated=py_translated)


if __name__ == '__main__':
    app.run(debug=True)
