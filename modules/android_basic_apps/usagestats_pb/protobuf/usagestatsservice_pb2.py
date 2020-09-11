# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: usagestatsservice.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import modules.android_basic_apps.usagestats_pb.protobuf.configuration_pb2 as configuration__pb2
import modules.android_basic_apps.usagestats_pb.protobuf.privacy_pb2 as privacy__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='usagestatsservice.proto',
  package='com.android.server.usage',
  syntax='proto2',
  serialized_options=_b('P\001'),
  serialized_pb=_b('\n\x17usagestatsservice.proto\x12\x18\x63om.android.server.usage\x1a\x13\x63onfiguration.proto\x1a\rprivacy.proto\"\x87\x0f\n\x12IntervalStatsProto\x12\x13\n\x0b\x65nd_time_ms\x18\x01 \x01(\x03\x12K\n\nstringpool\x18\x02 \x01(\x0b\x32\x37.com.android.server.usage.IntervalStatsProto.StringPool\x12\x15\n\rmajor_version\x18\x03 \x01(\x05\x12\x15\n\rminor_version\x18\x04 \x01(\x05\x12N\n\x0binteractive\x18\n \x01(\x0b\x32\x39.com.android.server.usage.IntervalStatsProto.CountAndTime\x12R\n\x0fnon_interactive\x18\x0b \x01(\x0b\x32\x39.com.android.server.usage.IntervalStatsProto.CountAndTime\x12Q\n\x0ekeyguard_shown\x18\x0c \x01(\x0b\x32\x39.com.android.server.usage.IntervalStatsProto.CountAndTime\x12R\n\x0fkeyguard_hidden\x18\r \x01(\x0b\x32\x39.com.android.server.usage.IntervalStatsProto.CountAndTime\x12I\n\x08packages\x18\x14 \x03(\x0b\x32\x37.com.android.server.usage.IntervalStatsProto.UsageStats\x12R\n\x0e\x63onfigurations\x18\x15 \x03(\x0b\x32:.com.android.server.usage.IntervalStatsProto.Configuration\x12\x45\n\tevent_log\x18\x16 \x03(\x0b\x32\x32.com.android.server.usage.IntervalStatsProto.Event\x1a+\n\nStringPool\x12\x0c\n\x04size\x18\x01 \x01(\x05\x12\x0f\n\x07strings\x18\x02 \x03(\t\x1a.\n\x0c\x43ountAndTime\x12\r\n\x05\x63ount\x18\x01 \x01(\x05\x12\x0f\n\x07time_ms\x18\x02 \x01(\x03\x1a\xb4\x04\n\nUsageStats\x12\x0f\n\x07package\x18\x01 \x01(\t\x12\x15\n\rpackage_index\x18\x02 \x01(\x05\x12\x1b\n\x13last_time_active_ms\x18\x03 \x01(\x03\x12\x1c\n\x14total_time_active_ms\x18\x04 \x01(\x03\x12\x12\n\nlast_event\x18\x05 \x01(\x05\x12\x18\n\x10\x61pp_launch_count\x18\x06 \x01(\x05\x12^\n\x0f\x63hooser_actions\x18\x07 \x03(\x0b\x32\x45.com.android.server.usage.IntervalStatsProto.UsageStats.ChooserAction\x12!\n\x19last_time_service_used_ms\x18\x08 \x01(\x03\x12\"\n\x1atotal_time_service_used_ms\x18\t \x01(\x03\x12\x1c\n\x14last_time_visible_ms\x18\n \x01(\x03\x12\x1d\n\x15total_time_visible_ms\x18\x0b \x01(\x03\x1a\xb0\x01\n\rChooserAction\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x63\n\x06\x63ounts\x18\x03 \x03(\x0b\x32S.com.android.server.usage.IntervalStatsProto.UsageStats.ChooserAction.CategoryCount\x1a,\n\rCategoryCount\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05\x63ount\x18\x03 \x01(\x05\x1a\x9e\x01\n\rConfiguration\x12\x33\n\x06\x63onfig\x18\x01 \x01(\x0b\x32#.android.content.ConfigurationProto\x12\x1b\n\x13last_time_active_ms\x18\x02 \x01(\x03\x12\x1c\n\x14total_time_active_ms\x18\x03 \x01(\x03\x12\r\n\x05\x63ount\x18\x04 \x01(\x05\x12\x0e\n\x06\x61\x63tive\x18\x05 \x01(\x08\x1a\xfa\x02\n\x05\x45vent\x12\x0f\n\x07package\x18\x01 \x01(\t\x12\x15\n\rpackage_index\x18\x02 \x01(\x05\x12\r\n\x05\x63lass\x18\x03 \x01(\t\x12\x13\n\x0b\x63lass_index\x18\x04 \x01(\x05\x12\x0f\n\x07time_ms\x18\x05 \x01(\x03\x12\r\n\x05\x66lags\x18\x06 \x01(\x05\x12\x0c\n\x04type\x18\x07 \x01(\x05\x12\x33\n\x06\x63onfig\x18\x08 \x01(\x0b\x32#.android.content.ConfigurationProto\x12\x13\n\x0bshortcut_id\x18\t \x01(\t\x12\x16\n\x0estandby_bucket\x18\x0b \x01(\x05\x12\x1c\n\x14notification_channel\x18\x0c \x01(\t\x12\"\n\x1anotification_channel_index\x18\r \x01(\x05\x12\x13\n\x0binstance_id\x18\x0e \x01(\x05\x12\x1f\n\x17task_root_package_index\x18\x0f \x01(\x05\x12\x1d\n\x15task_root_class_index\x18\x10 \x01(\x05\x42\x02P\x01')
  ,
  dependencies=[configuration__pb2.DESCRIPTOR,privacy__pb2.DESCRIPTOR,])




_INTERVALSTATSPROTO_STRINGPOOL = _descriptor.Descriptor(
  name='StringPool',
  full_name='com.android.server.usage.IntervalStatsProto.StringPool',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='size', full_name='com.android.server.usage.IntervalStatsProto.StringPool.size', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='strings', full_name='com.android.server.usage.IntervalStatsProto.StringPool.strings', index=1,
      number=2, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=817,
  serialized_end=860,
)

_INTERVALSTATSPROTO_COUNTANDTIME = _descriptor.Descriptor(
  name='CountAndTime',
  full_name='com.android.server.usage.IntervalStatsProto.CountAndTime',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='count', full_name='com.android.server.usage.IntervalStatsProto.CountAndTime.count', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='time_ms', full_name='com.android.server.usage.IntervalStatsProto.CountAndTime.time_ms', index=1,
      number=2, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=862,
  serialized_end=908,
)

_INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION_CATEGORYCOUNT = _descriptor.Descriptor(
  name='CategoryCount',
  full_name='com.android.server.usage.IntervalStatsProto.UsageStats.ChooserAction.CategoryCount',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.ChooserAction.CategoryCount.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='count', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.ChooserAction.CategoryCount.count', index=1,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1431,
  serialized_end=1475,
)

_INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION = _descriptor.Descriptor(
  name='ChooserAction',
  full_name='com.android.server.usage.IntervalStatsProto.UsageStats.ChooserAction',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.ChooserAction.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='counts', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.ChooserAction.counts', index=1,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION_CATEGORYCOUNT, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1299,
  serialized_end=1475,
)

_INTERVALSTATSPROTO_USAGESTATS = _descriptor.Descriptor(
  name='UsageStats',
  full_name='com.android.server.usage.IntervalStatsProto.UsageStats',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='package', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.package', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='package_index', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.package_index', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='last_time_active_ms', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.last_time_active_ms', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='total_time_active_ms', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.total_time_active_ms', index=3,
      number=4, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='last_event', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.last_event', index=4,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='app_launch_count', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.app_launch_count', index=5,
      number=6, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='chooser_actions', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.chooser_actions', index=6,
      number=7, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='last_time_service_used_ms', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.last_time_service_used_ms', index=7,
      number=8, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='total_time_service_used_ms', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.total_time_service_used_ms', index=8,
      number=9, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='last_time_visible_ms', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.last_time_visible_ms', index=9,
      number=10, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='total_time_visible_ms', full_name='com.android.server.usage.IntervalStatsProto.UsageStats.total_time_visible_ms', index=10,
      number=11, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=911,
  serialized_end=1475,
)

_INTERVALSTATSPROTO_CONFIGURATION = _descriptor.Descriptor(
  name='Configuration',
  full_name='com.android.server.usage.IntervalStatsProto.Configuration',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='config', full_name='com.android.server.usage.IntervalStatsProto.Configuration.config', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='last_time_active_ms', full_name='com.android.server.usage.IntervalStatsProto.Configuration.last_time_active_ms', index=1,
      number=2, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='total_time_active_ms', full_name='com.android.server.usage.IntervalStatsProto.Configuration.total_time_active_ms', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='count', full_name='com.android.server.usage.IntervalStatsProto.Configuration.count', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='active', full_name='com.android.server.usage.IntervalStatsProto.Configuration.active', index=4,
      number=5, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1478,
  serialized_end=1636,
)

_INTERVALSTATSPROTO_EVENT = _descriptor.Descriptor(
  name='Event',
  full_name='com.android.server.usage.IntervalStatsProto.Event',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='package', full_name='com.android.server.usage.IntervalStatsProto.Event.package', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='package_index', full_name='com.android.server.usage.IntervalStatsProto.Event.package_index', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='class', full_name='com.android.server.usage.IntervalStatsProto.Event.class', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='class_index', full_name='com.android.server.usage.IntervalStatsProto.Event.class_index', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='time_ms', full_name='com.android.server.usage.IntervalStatsProto.Event.time_ms', index=4,
      number=5, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='flags', full_name='com.android.server.usage.IntervalStatsProto.Event.flags', index=5,
      number=6, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='type', full_name='com.android.server.usage.IntervalStatsProto.Event.type', index=6,
      number=7, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='config', full_name='com.android.server.usage.IntervalStatsProto.Event.config', index=7,
      number=8, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='shortcut_id', full_name='com.android.server.usage.IntervalStatsProto.Event.shortcut_id', index=8,
      number=9, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='standby_bucket', full_name='com.android.server.usage.IntervalStatsProto.Event.standby_bucket', index=9,
      number=11, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='notification_channel', full_name='com.android.server.usage.IntervalStatsProto.Event.notification_channel', index=10,
      number=12, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='notification_channel_index', full_name='com.android.server.usage.IntervalStatsProto.Event.notification_channel_index', index=11,
      number=13, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='instance_id', full_name='com.android.server.usage.IntervalStatsProto.Event.instance_id', index=12,
      number=14, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='task_root_package_index', full_name='com.android.server.usage.IntervalStatsProto.Event.task_root_package_index', index=13,
      number=15, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='task_root_class_index', full_name='com.android.server.usage.IntervalStatsProto.Event.task_root_class_index', index=14,
      number=16, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1639,
  serialized_end=2017,
)

_INTERVALSTATSPROTO = _descriptor.Descriptor(
  name='IntervalStatsProto',
  full_name='com.android.server.usage.IntervalStatsProto',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='end_time_ms', full_name='com.android.server.usage.IntervalStatsProto.end_time_ms', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='stringpool', full_name='com.android.server.usage.IntervalStatsProto.stringpool', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='major_version', full_name='com.android.server.usage.IntervalStatsProto.major_version', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='minor_version', full_name='com.android.server.usage.IntervalStatsProto.minor_version', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='interactive', full_name='com.android.server.usage.IntervalStatsProto.interactive', index=4,
      number=10, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='non_interactive', full_name='com.android.server.usage.IntervalStatsProto.non_interactive', index=5,
      number=11, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='keyguard_shown', full_name='com.android.server.usage.IntervalStatsProto.keyguard_shown', index=6,
      number=12, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='keyguard_hidden', full_name='com.android.server.usage.IntervalStatsProto.keyguard_hidden', index=7,
      number=13, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='packages', full_name='com.android.server.usage.IntervalStatsProto.packages', index=8,
      number=20, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='configurations', full_name='com.android.server.usage.IntervalStatsProto.configurations', index=9,
      number=21, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='event_log', full_name='com.android.server.usage.IntervalStatsProto.event_log', index=10,
      number=22, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_INTERVALSTATSPROTO_STRINGPOOL, _INTERVALSTATSPROTO_COUNTANDTIME, _INTERVALSTATSPROTO_USAGESTATS, _INTERVALSTATSPROTO_CONFIGURATION, _INTERVALSTATSPROTO_EVENT, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=90,
  serialized_end=2017,
)

_INTERVALSTATSPROTO_STRINGPOOL.containing_type = _INTERVALSTATSPROTO
_INTERVALSTATSPROTO_COUNTANDTIME.containing_type = _INTERVALSTATSPROTO
_INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION_CATEGORYCOUNT.containing_type = _INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION
_INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION.fields_by_name['counts'].message_type = _INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION_CATEGORYCOUNT
_INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION.containing_type = _INTERVALSTATSPROTO_USAGESTATS
_INTERVALSTATSPROTO_USAGESTATS.fields_by_name['chooser_actions'].message_type = _INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION
_INTERVALSTATSPROTO_USAGESTATS.containing_type = _INTERVALSTATSPROTO
_INTERVALSTATSPROTO_CONFIGURATION.fields_by_name['config'].message_type = configuration__pb2._CONFIGURATIONPROTO
_INTERVALSTATSPROTO_CONFIGURATION.containing_type = _INTERVALSTATSPROTO
_INTERVALSTATSPROTO_EVENT.fields_by_name['config'].message_type = configuration__pb2._CONFIGURATIONPROTO
_INTERVALSTATSPROTO_EVENT.containing_type = _INTERVALSTATSPROTO
_INTERVALSTATSPROTO.fields_by_name['stringpool'].message_type = _INTERVALSTATSPROTO_STRINGPOOL
_INTERVALSTATSPROTO.fields_by_name['interactive'].message_type = _INTERVALSTATSPROTO_COUNTANDTIME
_INTERVALSTATSPROTO.fields_by_name['non_interactive'].message_type = _INTERVALSTATSPROTO_COUNTANDTIME
_INTERVALSTATSPROTO.fields_by_name['keyguard_shown'].message_type = _INTERVALSTATSPROTO_COUNTANDTIME
_INTERVALSTATSPROTO.fields_by_name['keyguard_hidden'].message_type = _INTERVALSTATSPROTO_COUNTANDTIME
_INTERVALSTATSPROTO.fields_by_name['packages'].message_type = _INTERVALSTATSPROTO_USAGESTATS
_INTERVALSTATSPROTO.fields_by_name['configurations'].message_type = _INTERVALSTATSPROTO_CONFIGURATION
_INTERVALSTATSPROTO.fields_by_name['event_log'].message_type = _INTERVALSTATSPROTO_EVENT
DESCRIPTOR.message_types_by_name['IntervalStatsProto'] = _INTERVALSTATSPROTO
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

IntervalStatsProto = _reflection.GeneratedProtocolMessageType('IntervalStatsProto', (_message.Message,), dict(

  StringPool = _reflection.GeneratedProtocolMessageType('StringPool', (_message.Message,), dict(
    DESCRIPTOR = _INTERVALSTATSPROTO_STRINGPOOL,
    __module__ = 'usagestatsservice_pb2'
    # @@protoc_insertion_point(class_scope:com.android.server.usage.IntervalStatsProto.StringPool)
    ))
  ,

  CountAndTime = _reflection.GeneratedProtocolMessageType('CountAndTime', (_message.Message,), dict(
    DESCRIPTOR = _INTERVALSTATSPROTO_COUNTANDTIME,
    __module__ = 'usagestatsservice_pb2'
    # @@protoc_insertion_point(class_scope:com.android.server.usage.IntervalStatsProto.CountAndTime)
    ))
  ,

  UsageStats = _reflection.GeneratedProtocolMessageType('UsageStats', (_message.Message,), dict(

    ChooserAction = _reflection.GeneratedProtocolMessageType('ChooserAction', (_message.Message,), dict(

      CategoryCount = _reflection.GeneratedProtocolMessageType('CategoryCount', (_message.Message,), dict(
        DESCRIPTOR = _INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION_CATEGORYCOUNT,
        __module__ = 'usagestatsservice_pb2'
        # @@protoc_insertion_point(class_scope:com.android.server.usage.IntervalStatsProto.UsageStats.ChooserAction.CategoryCount)
        ))
      ,
      DESCRIPTOR = _INTERVALSTATSPROTO_USAGESTATS_CHOOSERACTION,
      __module__ = 'usagestatsservice_pb2'
      # @@protoc_insertion_point(class_scope:com.android.server.usage.IntervalStatsProto.UsageStats.ChooserAction)
      ))
    ,
    DESCRIPTOR = _INTERVALSTATSPROTO_USAGESTATS,
    __module__ = 'usagestatsservice_pb2'
    # @@protoc_insertion_point(class_scope:com.android.server.usage.IntervalStatsProto.UsageStats)
    ))
  ,

  Configuration = _reflection.GeneratedProtocolMessageType('Configuration', (_message.Message,), dict(
    DESCRIPTOR = _INTERVALSTATSPROTO_CONFIGURATION,
    __module__ = 'usagestatsservice_pb2'
    # @@protoc_insertion_point(class_scope:com.android.server.usage.IntervalStatsProto.Configuration)
    ))
  ,

  Event = _reflection.GeneratedProtocolMessageType('Event', (_message.Message,), dict(
    DESCRIPTOR = _INTERVALSTATSPROTO_EVENT,
    __module__ = 'usagestatsservice_pb2'
    # @@protoc_insertion_point(class_scope:com.android.server.usage.IntervalStatsProto.Event)
    ))
  ,
  DESCRIPTOR = _INTERVALSTATSPROTO,
  __module__ = 'usagestatsservice_pb2'
  # @@protoc_insertion_point(class_scope:com.android.server.usage.IntervalStatsProto)
  ))
_sym_db.RegisterMessage(IntervalStatsProto)
_sym_db.RegisterMessage(IntervalStatsProto.StringPool)
_sym_db.RegisterMessage(IntervalStatsProto.CountAndTime)
_sym_db.RegisterMessage(IntervalStatsProto.UsageStats)
_sym_db.RegisterMessage(IntervalStatsProto.UsageStats.ChooserAction)
_sym_db.RegisterMessage(IntervalStatsProto.UsageStats.ChooserAction.CategoryCount)
_sym_db.RegisterMessage(IntervalStatsProto.Configuration)
_sym_db.RegisterMessage(IntervalStatsProto.Event)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
