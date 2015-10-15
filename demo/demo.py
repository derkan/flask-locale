# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, g, session, redirect, current_app
from flask_locale import Locale, _

app = Flask(__name__)
# DEFAULT_LOCALE is the language used for keys ins translation files:
app.config['DEFAULT_LOCALE'] = 'en_US'
app.config['LOCALE_PATH'] = 'translations'
app.config['SECRET_KEY'] = 'translations****'

locale = Locale(app)


@locale.localeselector
def get_locale():
    # if a user is logged in, use the locale from the session
    # define a default value instead of None to set it to specific locale if not setting is found.
    locale_code = session.get('locale', None)
    if locale_code is not None:
        current_app.logger.info("Locale is: %s" % locale_code)
        return locale_code

    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support tr/fr/en in this
    # example.  The best match wins.
    locale_code = request.accept_languages.best_match(['tr_TR', 'fr_FR', 'en_US'])
    current_app.logger.info("Locale match: %s" % locale_code)
    return locale_code


@app.route("/")
def index():
    # How we do translation in python code:
    py_translated = _('Hello')
    # How we do translation in template:
    return render_template('locale.html', name='Erkan', py_translated=py_translated)


@app.route("/locale")
def change_locale():
    new_locale = request.args.get('locale', None)
    session['locale'] = new_locale
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
