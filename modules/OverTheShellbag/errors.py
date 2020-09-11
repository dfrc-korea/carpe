class ShellItemFormatError(Exception):
  def __init__(self, _error_message):
    self.error_type = "ShellItemFormatError"
    self.error_message = _error_message


class ExtensionBlockFormatError(Exception):
  def __init__(self, _error_message):
    self.error_type = "ExtensionBlockFormatError"
    self.error_message = _error_message


class WindowsPropertyFormatError(Exception):
  def __init__(self, _error_message):
    self.error_type = "WindowsPropertyFormatError"
    self.error_message = _error_message