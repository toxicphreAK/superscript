import re


class Version:
    def __init__(self, *args, **kwargs):
        default_version = {
            'major': 0,
            'minor': 0,
            'fix': 0
        }
        if len(args) == 1:
            default_version = self.convert_versionstring(args[0])
        self.major = kwargs.get('major', default_version['major'])
        self.minor = kwargs.get('minor', default_version['minor'])
        self.fix = kwargs.get('fix', default_version['fix'])

    def get_versionstring(self):
        return "v{}.{}.{}".format(self.major, self.minor, self.fix)

    def next_major(self):
        return int(self.major) + 1

    def next_minor(self):
        return int(self.minor) + 1

    def next_fix(self):
        return int(self.fix) + 1

    @staticmethod
    def convert_versionstring(versionstring):
        versionstring_regex = re.compile("[vV]?(?P<major>[0-9]+)[.,-_]?(?P<minor>[0-9]*)[.,-_]?(?P<fix>[0-9]*)")
        version_match = versionstring_regex.match(versionstring.strip())
        if not version_match:
            # TODO: handle error in regex and print versionstring
            #  with the info that this version conversion is not supported at the moment
            pass
        version = {
            'major': 0,
            'minor': 0,
            'fix': 0
        }
        if version_match.group('major'):
            version['major'] = int(version_match.group('major'))
            if version_match.group('minor'):
                version['minor'] = int(version_match.group('minor'))
                if version_match.group('fix'):
                    version['fix'] = int(version_match.group('fix'))
        return version
