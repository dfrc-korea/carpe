# -*- coding: utf-8 -*-
"""This file contains the error classes."""


class Error(Exception):
    """Base error class."""

class UnableToParseFile(Error):
    """Raised when a parser is not designed to parse a file."""
