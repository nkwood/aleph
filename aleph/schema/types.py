import re

from aleph.data.validate import is_partial_date
from aleph.data.parse import parse_phone, parse_country, parse_email
from aleph.data.parse import parse_date
from aleph.data.keys import make_fingerprint
from aleph.text import string_value, collapse_spaces, latinize_text
from aleph.util import ensure_list


class StringProperty(object):
    index_invert = None

    def __init__(self):
        self.name = type(self).__name__.lower().replace('property', '')

    def clean(self, value, record, config):
        value = string_value(value)
        if value is not None:
            return collapse_spaces(value)

    def normalize(self, values):
        results = set()
        for value in values:
            results.update(ensure_list(self.normalize_value(value)))
        return results

    def normalize_value(self, value):
        return self.clean(value, {}, {})

    def fingerprint(self, values):
        return []


class NameProperty(StringProperty):
    index_invert = 'names'

    def normalize_value(self, value):
        value = collapse_spaces(value)
        return value, latinize_text(value)

    def fingerprint(self, values):
        # TODO: this should not be a property thing, so that fp's can include
        # dates etx.
        fingerprints = []
        for value in values:
            fingerprints.append(make_fingerprint(value))
        return [fp for fp in fingerprints if fp is not None]


class URLProperty(StringProperty):
    index_invert = None


class DateProperty(StringProperty):
    index_invert = 'dates'

    def clean(self, value, record, config):
        value = super(DateProperty, self).clean(value, record, config)
        return parse_date(value, date_format=config.get('format'))

    def normalize_value(self, value):
        if is_partial_date(value):
            return value


class CountryProperty(StringProperty):
    index_invert = 'countries'

    def clean(self, value, record, config):
        value = super(CountryProperty, self).clean(value, record, config)
        return parse_country(value) or value

    def normalize_value(self, value):
        return parse_country(value)


class AddressProperty(StringProperty):
    index_invert = 'addresses'

    def normalize_value(self, value):
        return make_fingerprint(value)


class PhoneProperty(StringProperty):
    index_invert = 'phones'

    def clean(self, value, record, config):
        value = super(PhoneProperty, self).clean(value, record, config)
        number = parse_phone(value, config.get('country'))
        return number or value


class EmailProperty(StringProperty):
    index_invert = 'emails'

    def clean(self, value, record, config):
        value = super(EmailProperty, self).clean(value, record, config)
        return parse_email(value) or value

    def normalize_value(self, value):
        return parse_email(value)


class IdentiferProperty(StringProperty):
    index_invert = 'identifiers'
    clean_re = re.compile('[^a-zA-Z0-9]*')

    def normalize_value(self, value):
        value = string_value(value)
        if value is not None:
            value = self.clean_re.sub('', value).upper()
            return string_value(value)


def resolve_type(name):
    """Look up a configerty type by name."""
    types = {
        'string': StringProperty,
        'name': NameProperty,
        'date': DateProperty,
        'country': CountryProperty,
        'address': AddressProperty,
        'phone': PhoneProperty,
        'email': EmailProperty,
        'url': URLProperty,
        'uri': URLProperty,
        'identifier': IdentiferProperty
    }
    type_ = types.get(name.strip().lower())
    if type_ is None:
        raise TypeError("No such type: %s" % name)
    return type_
