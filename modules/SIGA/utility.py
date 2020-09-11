# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from datetime import datetime, timezone, timedelta

EPOCH_AS_FILETIME = 116444736000000000  # January 1, 1970 as MS file time
HUNDREDS_OF_NANOSECONDS = 10000000


def filetime_to_dt(ft):
    """Converts a Microsoft filetime number to a Python datetime. The new
    datetime object is time zone-naive but is equivalent to tzinfo=utc.
    >>> filetime_to_dt(116444736000000000)
    datetime.datetime(1970, 1, 1, 0, 0)
    >>> filetime_to_dt(128930364000000000)
    datetime.datetime(2009, 7, 25, 23, 0)
    """

    KST = timezone(timedelta(hours=9))
    return (datetime.utcfromtimestamp((ft - EPOCH_AS_FILETIME) / HUNDREDS_OF_NANOSECONDS).replace(tzinfo=KST) + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S %Z')

class Stack:
  def __init__(self):
    self.items = []
    self.max = 3

  def push(self, item):
    self.items.append(item)

  def pop(self):
    self.items.pop()

  def print_stack(self):
    print(self.items)

  def top(self):
    return self.items[len(self.items) - 1]

  def is_empty(self):
    return self.items == []

  def size(self):
    return len(self.items)
