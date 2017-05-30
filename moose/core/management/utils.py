from __future__ import unicode_literals

from moose.utils.crypto import get_random_string

def get_random_secret_key():
    """
    Return a 50 character random string usable as a SECRET_KEY setting value.
    """
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    return get_random_string(50, chars)


def handle_extensions(extensions):
    """
    Organizes multiple extensions that are separated with commas or passed by
    using --extension/-e multiple times.

    For example: running 'moose-admin makemessages -e js,txt -e xhtml -a'
    would result in an extension list: ['.js', '.txt', '.xhtml']

    >>> handle_extensions(['.html', 'html,js,py,py,py,.py', 'py,.py'])
    {'.html', '.js', '.py'}
    >>> handle_extensions(['.html, txt,.tpl'])
    {'.html', '.tpl', '.txt'}
    """
    ext_list = []
    for ext in extensions:
        ext_list.extend(ext.replace(' ', '').split(','))
    for i, ext in enumerate(ext_list):
        if not ext.startswith('.'):
            ext_list[i] = '.%s' % ext_list[i]
    return set(ext_list)