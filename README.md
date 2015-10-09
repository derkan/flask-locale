# Flask-Locale

Implements i18n and l10n support for Flask.  This is based on the old [Flask-Locale](http://github.com/whtsky/whtsky-locale/) extension. Uses files or database to get translations.

You can use this extension to translate your applications really easily. No babel preperation is needed. Just put your English text and its translation in a file.

## Install

```sh
pip install Flask-Locale
```

## Quick Start
- For very quick test look at `demo` directory.

- Create a directory `translations` at app root. 
- Create file `translations/tr_TR.csv` with this content:

```csv
"Hello %(name)s","Merhaba %(name)s"
"Hello","Merhaba"
```
- Create `templates` directory at app root.

- Create `locale.html` file with this content:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Flask-Locale</title>
</head>
<body>
 <h2>Translate with parameters in template</h2>
 {{ _('Hello %(name)s', name=name) }}
 <br>
 <h2>Translated in Python Code:</h2>
 {{ py_translated }}
</body>
</html>
```
-- Create your application main file `demo.py`:

```py
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

```

- Run yout app:

```sh
python demo.py
```

- Now access your app: `http://127.0.0.1:5000/`

## Usage

### Loading translations from a file:
Loads translations from CSV files having locale extension in a directory. File should be `utf-8` encoded.

Translations are strings with optional Python-style named placeholders (e.g., ``"My name is %(name)s"``) and their associated translations.

The directory should have translation files of the form filename: LOCALE, e.g.  tr_TR. 

Translation files should have two or three columns: string, translation, and an optional plural indicator. Plural indicators should be one of ``"plural"`` or ``"singular"``. 

A given string can have both singular and plural forms. For example ``"%(name)s liked this"`` may have a different verb conjugation depending on whether %(name)s is one name or a list of names. There should be two rows in the CSV file for that string, one with plural indicator "singular", and one "plural".

For strings with no verbs that would change on translation, simply
use ``"unknown"`` or the empty string (or don't include the column at all).

The file is read using the csv module in the default "excel" dialect.
In this format there should not be spaces after the commas.

Example translation tr_TR.csv::

```
"I love you","Seni seviyorum"
"%(name)s liked these","A %(name)s bunları sevdi","plural"
"%(name)s liked this","A %(name)s bunu sevdi","singular"
```

### Loading translations from database:

```py
@locale.db_loader
def get_translations():
    """Translations selector for db"""
        sql = select(
            [Locale.c.code, TranslationKey.c.name, Translation.c.translated, Translation.c.singular],
            from_obj=[Locale.join(Translation).join(TranslationKey)])
        q = db.session.execute(sql)
        data = q.fetchall()
        q.close()
    return list(data)
```

### Reloading translations

When user's locale is changed, call `refresh()` method:

```py
user.locale = request.form['locale']
locale.refresh()
flash(translate('Language was changed'))
```

### Translate Functions

`translate()` (or its alias `_()`) method does a lazy translation, that means its actual translate function is called when you access it. So you can use translate functions in your forms before Flask-Locale is initialized.


```py
from flask.ext.wtf import Form
from wtforms.fields import TextField, PasswordField
from wtforms.validators import Required, Email
from extensions import _

class EmailPasswordForm(Form):
    email = TextField(_('Email'), validators=[Required(), Email()])
    password = PasswordField(_('Password'), validators=[Required()])
```

If you want immediate translation, use `do_translate` method.
