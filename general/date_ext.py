import datetime
import locale

def weekdays(locale_ = 'en_US.utf8'):
    if locale_:
        old_locale = locale.getlocale()
        locale.setlocale(locale.LC_ALL, locale_)
    v = tuple([datetime.date(2001, 1, i).strftime('%A') for i in range(1,8)])
    if locale_:
        locale.setlocale(locale.LC_ALL, old_locale)
    return v


def date_to_long_form_string(dt, locale_ = 'en_US.utf8'):
    '''dt should be a datetime.date object.'''
    if locale_:
        old_locale = locale.getlocale()
        locale.setlocale(locale.LC_ALL, locale_)
    v = dt.strftime("%A %B %d %Y")
    if locale_:
        locale.setlocale(locale.LC_ALL, old_locale)
    return v


