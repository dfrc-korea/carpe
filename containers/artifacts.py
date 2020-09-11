# -*- coding: utf-8 -*-

from containers import interface

class ArtifactAttributeContainer(interface.AttributeContainer):
  """Base class to represent an artifact attribute container."""


class EnvironmentVariableArtifact(ArtifactAttributeContainer):
  """Environment variable artifact attribute container.

  Also see:
    https://en.wikipedia.org/wiki/Environment_variable

  Attributes:
    case_sensitive (bool): True if environment variable name is case sensitive.
    name (str): environment variable name such as "SystemRoot" as in
        "%SystemRoot%" or "HOME" as in "$HOME".
    value (str): environment variable value such as "C:\\Windows" or
        "/home/user".
  """
  CONTAINER_TYPE = 'environment_variable'

  def __init__(self, case_sensitive=True, name=None, value=None):
    """Initializes an environment variable artifact.

    Args:
      case_sensitive (Optional[bool]): True if environment variable name
          is case sensitive.
      name (Optional[str]): environment variable name.
      value (Optional[str]): environment variable value.
    """
    super(EnvironmentVariableArtifact, self).__init__()
    self.case_sensitive = case_sensitive
    self.name = name
    self.value = value

class TimeZoneArtifact(ArtifactAttributeContainer):
  """Time zone artifact attribute container.

  Attributes:
    name (str): name describing the time zone for example Greenwich Standard
        Time.
  """
  CONTAINER_TYPE = 'time_zone'

  def __init__(self, name=None):
    """Initializes a time zone artifact.

    Args:
      name (Optional[str]): name describing the time zone for example Greenwich
          Standard Time.
    """
    super(TimeZoneArtifact, self).__init__()
    self.name = name

class HostnameArtifact(ArtifactAttributeContainer):
  """Hostname artifact attribute container.

  Also see:
    https://en.wikipedia.org/wiki/Hostname
    Cybox / Stix Hostname Object

  Attributes:
    name (str): name of the host according to the naming schema.
    schema (str): naming schema such as "DNS", "NIS", "SMB/NetBIOS".
  """
  CONTAINER_TYPE = 'hostname'

  def __init__(self, name=None, schema='DNS'):
    """Initializes a hostname artifact.

    Args:
      name (Optional[str]): name of the host according to the naming schema.
      schema (Optional[str]): naming schema.
    """
    super(HostnameArtifact, self).__init__()
    self.name = name
    self.schema = schema

class UserAccountArtifact(ArtifactAttributeContainer):
  """User account artifact attribute container.

  Also see:
    Cybox / Stix User Account Object

  Attributes:
    full_name (str): name describing the user.
    group_identifier (str): identifier of the primary group the user is part of.
    identifier (str): user identifier.
    user_directory (str): path of the user (or home or profile) directory.
    username (str): name uniquely identifying the user.
  """
  CONTAINER_TYPE = 'user_account'

  def __init__(
      self, full_name=None, group_identifier=None, identifier=None,
      path_separator='/', user_directory=None, username=None):
    """Initializes a user account artifact.

    Args:
      full_name (Optional[str]): name describing the user.
      group_identifier (Optional[str]): identifier of the primary group
          the user is part of.
      identifier (Optional[str]): user identifier.
      path_separator (Optional[str]): path segment separator.
      user_directory (Optional[str]): path of the user (or home or profile)
          directory.
      username (Optional[str]): name uniquely identifying the user.
    """
    super(UserAccountArtifact, self).__init__()
    self._path_separator = path_separator
    self.full_name = full_name
    self.group_identifier = group_identifier
    self.identifier = identifier
    # TODO: add shell.
    self.user_directory = user_directory
    self.username = username

  def GetUserDirectoryPathSegments(self):
    """Retrieves the path segments of the user directory.

    Returns:
      list[str]: path segments of the user directory or an empty list if no
          user directory is set.
    """
    if not self.user_directory:
      return []
    return self.user_directory.split(self._path_separator)