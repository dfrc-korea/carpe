# -*- coding: utf-8 -*-

from utility import errors
from tools import logger

import pytz
import datetime


class CaseManager(object):

    def __init__(self):
        super(CaseManager, self).__init__()
        self.case_id = None
        self.evidence_id = None
        self.list_timezones = False
        self._time_zone = pytz.UTC
        self._investigator_info = {}

    def AddInvestigatorInformation(self, investigator_info):
        for key, value in investigator_info.items():
            name = key

            if name in self._investigator_info:
                raise KeyError('Investigator Info: {0:s} already exists.'.format(key))

            self._investigator_info[name] = value

    def GetInvestigatorInformation(self, name):
        name = name
        return self._environment_variables.get(name, None)

    def GetInvestigatorInformations(self):
        return self._investigator_info.values()

    def timezone(self):
        return self._time_zone

    def SetTimezone(self, timezone):
        if not timezone:
            return
        try:
            self._time_zone = pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            raise ValueError('Unsupported timezone: {0:s}'.format(timezone))

    def AddTimeZoneOption(self, argument_group):
        """Adds the time zone option to the argument group.

        Args:
          argument_group (argparse._ArgumentGroup): argparse argument group.
        """
        # Note the default here is None so we can determine if the time zone option was set.
        argument_group.add_argument(
            '-z', '--zone', '--timezone', dest='timezone', action='store',
            type=str, default='UTC', help=(
                'explicitly define the timezone. Typically the timezone is '
                'determined automatically where possible otherwise it will '
                'default to UTC. Use "-z list" to see a list of available '
                'timezones.'))

    def _ParseTimezoneOption(self, options):
        time_zone_string = self.ParseStringOption(options, 'timezone')
        if isinstance(time_zone_string, (str, )):
            if time_zone_string.lower() == 'list':
                self.list_timezones = True
            elif time_zone_string:
                try:
                    pytz.timezone(time_zone_string)
                except pytz.UnknownTimeZoneError:
                    raise errors.BadConfigOption(
                        'Unknown time zone: {0:s}'.format(time_zone_string))

                self._time_zone = time_zone_string

    def add_extract_option(self, argument_group):
        argument_group.add_argument(
            '-e', '--extract', action='store', dest='extract_path', type=str,
            default=None, help=(
                'Enter your file path to extract.'
            )
        )

        argument_group.add_argument(
            '-p', '--par_num', action='store', dest='par_num', type=str,
            default=None, help=(
                'Enter your partition number to extract.'
            )
        )

    def add_carve_option(self, argument_group):
        argument_group.add_argument(
            '--sector', action='store', dest='sector_size', type=int,
            default=512, help=(
                'Enter your sector size of image to carve.'
            )
        )

        argument_group.add_argument(
            '--cluster', action='store', dest='cluster_size', type=int,
            default=4096, help=(
                'Enter your cluster size of image to carve.'
            )
        )

    def ListTimeZones(self):
        """Lists the timezones."""
        max_length = 0
        for timezone_name in pytz.all_timezones:
            if len(timezone_name) > max_length:
                max_length = len(timezone_name)

        utc_date_time = datetime.datetime.utcnow()

        print('{0:20}\t{1:s}'.format('TimezoneUTC', 'Offset'))
        for timezone_name in pytz.all_timezones:
            try:
                local_timezone = pytz.timezone(timezone_name)
            except AssertionError as exception:
                logger.error((
                     'Unable to determine information about timezone: {0:s} with '
                     'error: {1!s}').format(timezone_name, exception))
                continue

            local_date_string = '{0!s}'.format(
                local_timezone.localize(utc_date_time))
            if '+' in local_date_string:
                _, _, diff = local_date_string.rpartition('+')
                diff_string = '+{0:s}'.format(diff)
            else:
                _, _, diff = local_date_string.rpartition('-')
                diff_string = '-{0:s}'.format(diff)

            print('{0:20}\t{1:s}'.format(timezone_name, diff_string))
