#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author:    Seonho Lee
@contact:   horensic@gmail.com
"""

import datetime

# Log Level
LOG_OFF = 0x0
LOG_FATAL = 0x1
LOG_ERROR = 0x2
LOG_WARN = 0x4
LOG_INFO = 0x8
LOG_DEBUG = 0x10
LOG_TRACE = 0x20
LOG_ALL = 0xFF

# Log Message
LOG_MSG = {
    0x1: '[FATAL]',
    0x2: '[ERROR]',
    0x4: '[WARNING]',
    0x8: '[INFO]',
    0x10: '[DEBUG]',
    0x20: '[TRACE]'
}


class CarpeLog:

    MSG_FMT = "{ts} [{lv}] {m}"

    def __init__(self, name, level=LOG_INFO):
        self.name = name
        self.level = level

        self._stream_handle = True
        self._file_handle = None

    def __repr__(self):
        return "<Carpe Logger: {}>".format(self.name)

    def add_handle(self):
        raise NotImplementedError

    def stream_print(self, log_msg):
        if self._stream_handle:
            print(log_msg)
        if self._file_handle:
            raise NotImplementedError

    @staticmethod
    def _timestamp():
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def fatal(self, msg):
        if (self.level & LOG_FATAL) == LOG_FATAL:
            timestamp = self._timestamp()
            log_msg = self.MSG_FMT.format(ts=timestamp, lv="FATAL", m=msg)
            self.stream_print(log_msg)

    def error(self, msg):
        if (self.level & LOG_ERROR) == LOG_ERROR:
            timestamp = self._timestamp()
            log_msg = self.MSG_FMT.format(ts=timestamp, lv="ERROR", m=msg)
            self.stream_print(log_msg)

    def warn(self, msg):
        if (self.level & LOG_WARN) == LOG_WARN:
            timestamp = self._timestamp()
            log_msg = self.MSG_FMT.format(ts=timestamp, lv="WARN", m=msg)
            self.stream_print(log_msg)

    def info(self, msg):
        if (self.level & LOG_INFO) == LOG_INFO:
            timestamp = self._timestamp()
            log_msg = self.MSG_FMT.format(ts=timestamp, lv="INFO", m=msg)
            self.stream_print(log_msg)

    def debug(self, msg):
        if (self.level & LOG_DEBUG) == LOG_DEBUG:
            timestamp = self._timestamp()
            log_msg = self.MSG_FMT.format(ts=timestamp, lv="DEBUG", m=msg)
            self.stream_print(log_msg)

    def trace(self, msg):
        if (self.level & LOG_TRACE) == LOG_TRACE:
            timestamp = self._timestamp()
            log_msg = self.MSG_FMT.format(ts=timestamp, lv="TRACE", m=msg)
            self.stream_print(log_msg)
