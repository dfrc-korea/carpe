# -*- coding: utf-8 -*-
# !/usr/bin/python3

import os
import sys
import binascii
import shutil
import pickle
import time
import pandas as pd
import argparse

from multiprocessing import Process, Queue, Lock, Semaphore
from moduleInterface.defines import ModuleConstant
from moduleInterface.defines import Offset_Info
from moduleInterface.interface import ModuleComponentInterface
from moduleInterface.interface import MemFrameTool
from moduleInterface.actuator import Actuator
from structureReader import structureReader as sr

from .fica_defines import C_defy
from .fica_defines import _C_defy

sys.path.append(os.path.abspath(os.path.dirname(__file__)) + os.sep + "Code")


class FiCA(Process, ModuleComponentInterface, C_defy):
    Instruction = C_defy.WorkLoad
    CASE = {
        "name": None,
        "uid": None,
        "path": None,
        "out": None,
        "off_start": 0,
        "off_end": 0,
        "size": 0,
        "cluster": 4096,
        "sector": 512,
        "fp": None,
        "hit": dict(),
        "mem_frame": pd.DataFrame(columns=C_defy.MemSchema.default_columns.keys()),
        "tape": pd.DataFrame(columns=C_defy.MemSchema.default_columns.keys()),
        "extract": True,
        "encode": "utf-8",
        "export": True,
        "perf": 0
    }

    def __init__(self, debug=False, out=None, log_buffer=0x409600, queue=None, lock=None, ulock=None):
        super().__init__()
        Process.__init__(self)
        self.__return = C_defy.Return
        self.__actuator_tree = {"cc": [
            Actuator(),
            os.path.abspath(os.path.dirname(__file__)) + os.sep + "config.txt",
            os.path.abspath(os.path.dirname(__file__)) + os.sep + "config.txt"]}
        self.case = FiCA.CASE.copy()
        self.debug = debug
        self.log_buffer = log_buffer
        self.timeout = None
        self.__lp = None
        self.__out = out
        self.queue = queue
        self.__open = False

        if lock is None:
            self.lock = lock
        else:
            self.lock = Lock()
        if ulock is None:
            self.ulock = Lock()
        else:
            self.ulock = ulock

        if type(self.__out) == str:
            self.__stdout = os.path.abspath(os.path.dirname(__file__)) + os.sep + self.__out
            self.__stdout_old = self.__stdout + ".old"
            self.__out = True
        else:
            self.__out = False

        self.__log_open()

        self.__count_vector = [0, 0]
        self.__block_param = [C_defy.Return.EVOID, C_defy.Return.EVOID, C_defy.Return.EVOID, 0]
        self.__block_counter = [0, 0]
        self.__int_mem = list()
        self.__nounce = 0

    def __del__(self):
        try:
            if self.__lp is not None:
                self.__lp.close()
        except:
            pass

    def __str__(self):
        print("Carving Manager")

    def __log_open(self):
        if self.__out:
            if os.path.exists(self.__stdout):
                if os.path.getsize(self.__stdout) < self.log_buffer:
                    self.__lp = open(self.__stdout, 'a+')
                    return
                else:
                    try:
                        shutil.move(self.__stdout, self.__stdout_old)
                    except:
                        self.__out = False
                        return
            self.__lp = open(self.__stdout, 'w')
            self.__log_write("INFO", "Main::Initiate carving plugin log.", always=True)
        else:
            self.__lp = None

    def __log_write(self, level, context, always=False, init=False):
        if (self.debug == True or always == True) and self.__lp is None:
            print("[{0}] At:{1} Text:{2}".format(level, time.ctime(), context))
        elif (self.debug == True or always == True) and (self.__lp is not None and init == True):
            self.__lp.close()
            self.__log_open()
        elif (self.debug == True or always == True) and self.__lp is not None:
            try:
                self.__lp.write("[{0}]::At::{1}::Text::{2}\n".format(level, time.ctime(), context))
                self.__lp.flush()
            except:
                self.__lp == None

    def ___load_module(self, actuator, default, config):
        self.__log_write("INFO", "Loader::Start to module load...", always=True)
        if not actuator.loadModuleClassAs("module_config", "ModuleConfiguration", "config"):
            self.__log_write("ERR_", "Loader::[module_config] module is not loaded. system exit.", always=True)
            return False
        actuator.open("config", 2, Lock())
        actuator.set("config", ModuleConstant.FILE_ATTRIBUTE, ModuleConstant.CONFIG_FILE)
        actuator.call("config", ModuleConstant.DESCRIPTION, "Carving Module List")
        actuator.call("config", ModuleConstant.INIT, config)
        module_list = actuator.call("config", ModuleConstant.GETALL, None).values()
        self.__log_write("INFO", "Loader::[module_config] Read module list from {0}.".format(config), always=True)
        if len(module_list) == 0:
            self.__log_write("INFO", "Loader::[module_config] No module to import.", always=True)
            return False
        for i in module_list:
            i = i.split(",")
            if len(i) != 3:
                continue
            res = actuator.loadModuleClassAs(i[0], i[1], i[2])
            self.__log_write("INFO", "Loader::loading module _result [{0:>2}] name [{1:<16}]".format(res, i[0]),
                             always=True)
            if res == False:
                self.__log_write("WARN", "Loader::[{0:<16}] module is not loaded.".format(i[0]), always=True)
        self.__log_write("INFO", "Loader::Completed.", always=True)
        return True

    def __load_module(self, actuator_name):
        actuator = self.__actuator_tree.get(actuator_name)
        if type(actuator) == list and type(actuator[0]) == Actuator:
            actuator[0].clear()
            actuator[0].init()
            return self.___load_module(*actuator)
        return False

    def __call_sub_module(self, actuator, request, start, end, cluster, command=None, parameter=None):
        actuator.set(request, ModuleConstant.FILE_ATTRIBUTE, self.case.get("path"))  # File to carve
        actuator.set(request, ModuleConstant.IMAGE_BASE, start)  # Set offset of the file base
        actuator.set(request, ModuleConstant.IMAGE_LAST, end)
        actuator.set(request, ModuleConstant.CLUSTER_SIZE, cluster)
        actuator.set(request, ModuleConstant.ENCODE, self.case.get("encode", "utf-8"))
        return actuator.call(request, command, parameter, self.debug)

    def __call_plugin_module(self, actuator_name, parameter):
        actuator = self.__actuator_tree.get(actuator_name)
        if actuator == None:
            return C_defy.Return.EVOID

        if isinstance(parameter, dict):
            host = parameter.get("host")
            prm = parameter.get("parameter")
            cmd = parameter.get("command")
            for k, v in parameter.items():
                if k == "host":
                    continue
                elif k == "parameter":
                    continue
                elif k == "command":
                    continue
                actuator[0].set(host, k, v)
            return actuator[0].call(host, cmd, prm, self.debug)

    def __attach_actuator(self, actuator_name, default, config):
        actuator = self.__actuator_tree.get(actuator_name)
        if actuator != None:
            if type(actuator[0]) == Actuator:
                actuator[0].clear()
                actuator[0].init()
        else:
            self.__actuator_tree.update({actuator_name: [Actuator(), default, config]})
        return True

    def __detach_actuator(self, actuator_name):
        actuator = self.__actuator_tree.get(actuator_name)
        if actuator != None:
            if type(actuator[0]) == Actuator:
                actuator[0].clear()
                actuator[0].init()
                self.__actuator_tree.pop(actuator_name)
                del actuator[0]
        return True

    def __set_perf_counter(self):
        self.__nounce = time.time()

    def __check_perf_counter(self):
        return time.time() - self.__nounce

    def __file_open(self, remove):
        if not os.path.isfile(self.case.get("path", "")):
            return C_defy.Return.EINVAL_FILE
        self.case.update({"size": os.path.getsize(self.case.get("path"))})
        self.case.update({"fp": sr.StructureReader()})
        self.case.get("fp").get_file_handle(self.case.get("path", ""), 0, 1)
        if os.path.exists(self.case.get("out", "")) and remove == True:
            self.__log_write("DBG_", "Extract::clear the current workspace:{0}".format(self.case.get("out")))
            try:
                shutil.rmtree(self.case.get("out"))
            except:
                self.__log_write("ERR_", "Extract::cannot cleanup working directory {0}.".format(self.case.get("out")))
                return C_defy.Return.EVOID
        return C_defy.Return.SUCCESS

    def __file_close(self):
        handle = self.case.get("fp")
        if handle != None:
            handle.cleanup()
        self.case.update({"fp": None})
        self.case.update({"size": 0})
        del handle  # Return resource

    def __cleanup_case(self):
        self.__file_close()
        frame = self.case.get("mem_frame", pd.DataFrame())
        if frame.empty:
            frame = frame.iloc[0:0]
            self.case.update({"mem_frame": frame})

        self.__open = False
        self.case = FiCA.CASE.copy()

    def __create_case(self, case):
        self.__cleanup_case()
        _klist = self.case.keys()
        if isinstance(case, dict):
            for k, v in case.items():
                if k in _klist: self.case.update({k: v})
            self.__open = True

    def __scan(self, handle, offset, block_size, size=0):
        signature = None
        buffer = handle.bread_raw(offset, block_size, os.SEEK_SET)
        if buffer is None:
            return [offset, signature, 0, 0, None, None, None, 0, None]

        for key in C_defy.SIGNATURE.CSIG:
            temp = C_defy.SIGNATURE.CSIG[key]
            if binascii.b2a_hex(buffer[temp[1]:temp[2]]) == temp[0]:
                signature = key
                # 특정 파일포맷에 대한 추가 검증 알고리즘
                """
                if key=='aac' or key=='aac_1' :
                    if binascii.b2a_hex(buffer[7:8])!=b'21':
                        signature = None
                        continue
                else:break
                """
                break
        return [offset, signature, 0, 0, None, None, None, 0, None]

    def __scan_signature(self):
        # A list is much faster than Dataframe or Database when appending continuous serial works.
        try:
            start = int(self.case.get("off_start", 0))
            block_size = int(self.case.get("cluster", 0))
            if block_size == 0:
                return C_defy.Return.EVOID
        except:
            return C_defy.Return.EVOID

        handle = self.case.get("fp")
        size = self.case.get("off_end", 0) - start
        if size <= 0:
            size = self.case.get("size") - start

        if size <= 0:
            return C_defy.Return.EVOID

        crafted = list()

        while start < size:
            result = self.__scan(handle, start, block_size)
            if result[1] is not None:
                crafted.append(result)
            start += block_size
        self.case.update({"mem_frame": crafted})
        return C_defy.Return.SUCCESS

    def __scan_signature_lbl(self):
        self.__int_mem = list()
        self.__block_param = [C_defy.Return.EVOID, C_defy.Return.EVOID, C_defy.Return.EVOID, 0]
        # A list is much faster than Dataframe or Database when appending continuous serial works.
        try:
            start = int(self.case.get("off_start", 0))
            block_size = int(self.case.get("cluster", 4096))
            if block_size == 0:
                return C_defy.Return.EVOID
        except:
            return C_defy.Return.EVOID

        handle = self.case.get("fp")
        size = self.case.get("off_end", 0) - start
        if size <= 0:
            size = self.case.get("size") - start

        if size <= 0:
            return C_defy.Return.EVOID
        self.__block_param = [handle, start, block_size, size]
        self.__block_counter = [int(size / block_size), 0]

        return C_defy.Return.SUCCESS

    def ___scan_signature_lbl(self):
        if self.__count_vector[0] < 2:
            if self.__block_param[1] >= self.__block_param[3]:
                return C_defy.Return.EVOID

            result = self.__scan(*self.__block_param)
            if result[1] != None:
                self.__int_mem.append(result)
            self.__block_param[1] += self.__block_param[2]
            self.__block_counter[1] += 1
        else:
            inline = 0
            while inline < self.__count_vector[0]:
                if self.__block_param[1] >= self.__block_param[3]:
                    return C_defy.Return.EVOID

                result = self.__scan(*self.__block_param)
                if result[1] != None:
                    self.__int_mem.append(result)
                self.__block_param[1] += self.__block_param[2]
                self.__block_counter[1] += 1
                inline += 1
        return self.__block_counter[1]

    def __filter_unextracted(self):
        return MemFrameTool.drop(self.case.get("mem_frame", pd.DataFrame(C_defy.MemSchema.default_columns.keys())),
                                 "flag", Offset_Info.EXTRACTED, "less")

    def set_token(self, count):
        if type(count) == int and count >= 0:
            self.__count_vector[0] = count

    def __cc_carving(self):

        cur_off_t = C_defy.MemSchema.default_columns.get("offset", 0)
        sig_off_t = C_defy.MemSchema.default_columns.get("signature", 1)
        nxt_off_t = C_defy.MemSchema.default_columns.get("next_offset", 2)
        flg_off_t = C_defy.MemSchema.default_columns.get("flag", 3)
        # prop_off_t  = C_defy.MemSchema.default_columns.get("property",4)
        off_info_t = C_defy.MemSchema.default_columns.get("offset_info", -1)
        file_name_t = C_defy.MemSchema.default_columns.get("file_name", 6)
        file_size_t = C_defy.MemSchema.default_columns.get("file_size", 7)
        file_path_t = C_defy.MemSchema.default_columns.get("file_path", 8)
        singular = Offset_Info.VALID | Offset_Info.UNIT

        frame = self.case.get("mem_frame", [])
        length = len(frame) - 1
        for i, v in enumerate(frame):
            if i == length:
                frame[i][nxt_off_t] = self.case.get("size")
            else:
                try:
                    frame[i][nxt_off_t] = frame[i + 1][cur_off_t]
                except:
                    self.__log_write("ERR", "Carving::Exceed length of the frame. Quit current task.", always=True)
                    self.case.update({"mem_frame": pd.DataFrame.from_records(frame,
                                                                             columns=C_defy.MemSchema.default_columns.keys())})
                    return C_defy.Return.EIOCTL

            off_t = self.__get_off_t(*frame[i])
            frame[i][flg_off_t] = off_t.header()[2]

            frame[i][file_name_t] = str(hex(frame[i][cur_off_t])) + '.' + frame[i][sig_off_t]
            frame[i][file_size_t] = frame[i][nxt_off_t] - frame[i][cur_off_t]

            if off_t.len > 0:
                frame[i][off_info_t] = pickle.dumps(off_t.contents)
                if self.case.get("extract", True) and (frame[i][flg_off_t] & singular == singular):
                    ret = self.__extractor(off_t)
                    if type(ret) != int:
                        frame[i][flg_off_t] |= Offset_Info.EXTRACTED
                    frame[i][file_path_t] = ret[0]
            else:
                frame[i][file_path_t] = None

        self.case.update(
            {"mem_frame": pd.DataFrame.from_records(frame, columns=C_defy.MemSchema.default_columns.keys())})
        return C_defy.Return.SUCCESS

    def __cc_carving_interactive(self):
        if self.__count_vector[0] > 0:
            cur_off_t = C_defy.MemSchema.default_columns.get("offset", 0)
            nxt_off_t = C_defy.MemSchema.default_columns.get("next_offset", 2)
            flg_off_t = C_defy.MemSchema.default_columns.get("flag", 3)
            off_info_t = C_defy.MemSchema.default_columns.get("offset_info", -1)
            singular = Offset_Info.VALID | Offset_Info.UNIT
            frame = self.case.get("mem_frame", [])
            length = len(frame) - 1

            i, j = self.__count_vector[1], 0
            while j < self.__count_vector[0]:
                if i == length:
                    frame[i][nxt_off_t] = self.case.get("size")
                    off_t = self.__get_off_t(*frame[i])
                    frame[i][flg_off_t] = off_t.header()[2]

                    if off_t.len > 0:
                        frame[i][off_info_t] = pickle.dumps(off_t.contents)
                        if self.case.get("extract", True) and (frame[i][flg_off_t] & singular == singular):
                            ret = self.__extractor(off_t)
                            if type(ret) != int:
                                frame[i][flg_off_t] |= Offset_Info.EXTRACTED

                    self.case.update({"mem_frame": pd.DataFrame.from_records(frame,
                                                                             columns=C_defy.MemSchema.default_columns.keys())})
                    return C_defy.Return.SUCCESS, 100

                try:
                    frame[i][nxt_off_t] = frame[i + 1][cur_off_t]
                except:
                    self.__log_write("ERR", "Carving::Exceed length of the frame. Quit current task.", always=True)
                    self.case.update({"mem_frame": pd.DataFrame.from_records(frame,
                                                                             columns=C_defy.MemSchema.default_columns.keys())})
                    return C_defy.Return.SUCCESS, int(self.__count_vector[1] / length * 100)

                off_t = self.__get_off_t(*frame[i])
                frame[i][flg_off_t] = off_t.header()[2]

                if off_t.len > 0:
                    frame[i][off_info_t] = pickle.dumps(off_t.contents)
                    if self.case.get("extract", True) and (frame[i][flg_off_t] & singular == singular):
                        ret = self.__extractor(off_t)
                        if type(ret) != int:
                            frame[i][flg_off_t] |= Offset_Info.EXTRACTED
                i += 1
                j += 1
            self.__count_vector[1] = i
            self.case.update({"mem_frame": frame})
            return C_defy.Return.EVOID, int(self.__count_vector[1] / length * 100)
        else:
            return self.__cc_carving(), 100

    def __cc_recarving(self):
        frame = self.case.get("mem_frame", pd.DataFrame(C_defy.MemSchema.default_columns.keys()))
        if frame.empty:
            return
        sig_off_t = C_defy.MemSchema.default_columns.get("signature", 1)
        flg_off_t = C_defy.MemSchema.default_columns.get("flag", 3)
        off_info_t = C_defy.MemSchema.default_columns.get("offset_info", -1)
        singular = Offset_Info.VALID | Offset_Info.UNIT

        for i in frame.index:
            if frame.loc[i][off_info_t] == None:
                continue
            off_t = Offset_Info()
            off_t.__contents = pickle.loads(frame.at[i, "offset_info"])
            off_t.signature = frame.loc[i][sig_off_t]
            off_t.name = off_t.signature
            off_t.size = len(off_t.__contents)
            if frame.loc[i][flg_off_t] & Offset_Info.EXTRACTED:
                frame.at[i, "flag"] -= Offset_Info.EXTRACTED

            if self.case.get("extract", True) and (frame.at[i, "flag"] & singular == singular):
                ret = self.__extractor(off_t)
                if type(ret) != int:
                    frame.at[i, "flag"] |= Offset_Info.EXTRACTED

    def __carving_mergeable(self, frame=None, target=None, flag=0):
        if type(frame) != pd.core.frame.DataFrame:
            frame = self.case.get("mem_frame", pd.DataFrame(C_defy.MemSchema.default_columns.keys()))
        if frame.empty: return
        groupable_mergeable = flag
        flg_off_t = C_defy.MemSchema.default_columns.get("flag", 3)
        if target == None:
            for k, v in C_defy.SIGNATURE.CSIG.items():
                if v[-1] != _C_defy.CATEGORY.RECORD:
                    continue
                _iframe = MemFrameTool.contains(frame, "signature", k, True)
                _iframe = MemFrameTool.drop(_iframe, "flag", groupable_mergeable, "equal")
                if _iframe.empty:
                    continue
                _iframe = _iframe.sort_values(by=["offset"])
                off_t = Offset_Info()
                off_t.signature = k
                off_t.name = k
                for i in _iframe.index:
                    _data = pickle.loads(_iframe.loc[i]["offset_info"])
                    frame.at[i, "flag"] = (frame.loc[i][flg_off_t] | Offset_Info.EXTRACTED)
                    for j in _data: off_t.append(*j)
                if (self.case.get("extract", True)):
                    self.__extractor(off_t)
            return
        else:
            off_t = Offset_Info()
            v = C_defy.SIGNATURE.CSIG.get(target)
            if v is None:
                return off_t
            _iframe = MemFrameTool.contains(frame, "signature", k, True)
            _iframe = MemFrameTool.drop(_iframe, "flag", groupable_mergeable, "equal")
            if _iframe.empty:
                return off_t
            _iframe = _iframe.sort_values(by=["offset"])
            off_t.signature = k
            off_t.name = k
            for i in _iframe.index:
                _data = pickle.loads(_iframe.loc[i]["offset_info"])
                frame.at[i, "flag"] = (frame.loc[i][flg_off_t] | Offset_Info.EXTRACTED)
                for j in _data: off_t.append(*j)
            if (self.case.get("extract", True)): self.__extractor(off_t)
            return off_t

    def __get_off_t(self, *value):
        extension = value[1]
        if ('_' in value[1]):
            extension = value[1].split('_', 1)[0]

        hit_count = self.case.get("hit").get(extension, None)
        if (hit_count == None):
            self.case.get("hit").update({extension: [1, 0]})
            hit_count = [1, 0]
        else:
            self.case.get("hit").update({extension: [hit_count[0] + 1, hit_count[1]]})
            hit_count = [hit_count[0] + 1, hit_count[1]]

        off_t = self.__call_sub_module(
            actuator=self.__actuator_tree.get("cc")[0],
            request=extension,
            start=value[0],
            end=value[2],
            cluster=self.case.get("cluster"),
            command=None,
            parameter=C_defy.SIGNATURE.CSIG.get(value[1])[-1])

        if (type(off_t) != Offset_Info):
            return Offset_Info()

        if (off_t.len > 0 and (off_t.header()[2] & Offset_Info.VALID) == 0):
            self.__log_write("ERR_",
                             "Extract:: Between {0} and {1}. This error reported at this module: {2}".format(value[0],
                                                                                                             value[2],
                                                                                                             extension))

        if off_t.len > 0 and (off_t.header()[2] & Offset_Info.VALID):
            hit_count = [hit_count[0], hit_count[1] + 1]
            self.case.get("hit").update({extension: hit_count})

        return off_t

    def __extractor(self, off_t):
        if off_t.size == 0:
            return 0

        _path = C_defy.SIGNATURE.CSIG.get(off_t.signature, (0, 0, 0, None, 0, 0))[3]
        if _path is None:
            return 0
        if off_t.flag not in (False, None) and type(off_t.flag) == str:
            if 1 < len(off_t.flag) < 256:
                if off_t.flag.find('\\') != -1:
                    root = self.case.get("out") + off_t.flag[off_t.flag.find('\\'):] + os.sep
                else:
                    root = self.case.get("out") + os.sep + off_t.flag + os.sep
            else:
                root = self.case.get("out") + os.sep + _path + os.sep
        else:
            root = self.case.get("out") + os.sep + _path + os.sep

        fname = root + str(hex(off_t.header()[0])) + "." + off_t.name
        sector = self.case.get("sector", 0x200)
        handle = self.case.get("fp")
        wrtn = 0

        if not os.path.exists(root):
            os.makedirs(root)

        try:
            fd = open(fname, 'wb')
        except:
            self.__log_write("ERR_", "Extract::an error while creating file:{0}.".format(fname))
            return C_defy.Return.EINVAL_FILE

        for i in off_t.contents:
            size = abs(i[1] - i[0])
            handle.bgoto(i[0], os.SEEK_SET)

            while size > 0:
                if size < sector:
                    data = handle.bread_raw(0, size)
                    wrtn += fd.write(data)
                    size -= size
                    continue
                data = handle.bread_raw(0, sector)
                wrtn += fd.write(data)
                size -= sector

        fd.close()
        self.__log_write("DBG_", "Extract::type:{0} name:{1}: copied:{2} bytes".format(off_t.signature, fname, wrtn))

        return fname, wrtn

    def __save_cc_carving(self, frame=None):
        root = self.case.get("out") + os.sep + ".cache"
        if str(type(frame)) == "<class 'NoneType'>":
            frame = self.case.get("mem_frame")
            if type(frame) == pd.core.frame.DataFrame:
                if os.path.exists(root):
                    try:
                        shutil.rmtree(root)
                        os.makedirs(root)
                    except:
                        self.__log_write("INFO", "SAVE::Permission denied.", always=True)
                        return
                else:
                    os.makedirs(root)
                if frame.empty is False:
                    frame.to_pickle("{0}{1}{2}".format(root, os.sep, "cc_cache.bin"))
                    # frame.to_csv("{0}{1}{2}".format(root,os.sep,"cc_cache.csv"))
        elif type(frame) == pd.core.frame.DataFrame:
            if frame.empty is False:
                frame.to_pickle("{0}{1}{2}".format(root, os.sep, "cc_cache.bin"))
            # frame.to_csv("{0}{1}{2}".format(root,os.sep,"cc_cache.csv"))

    def __save_cc_carving_tape(self, frame=None):
        root = self.case.get("out") + os.sep + ".cache"
        if str(type(frame)) == "<class 'NoneType'>":
            frame = self.case.get("tape")
            if type(frame) == pd.core.frame.DataFrame:
                if not frame.empty:
                    frame.to_pickle("{0}{1}{2}".format(root, os.sep, "cc_cache_tape.bin"))
                    # frame.to_csv("{0}{1}{2}".format(root,os.sep,"cc_cache_tape.csv"))
        elif type(frame) == pd.core.frame.DataFrame:
            if not frame.empty:
                frame.to_pickle("{0}{1}{2}".format(root, os.sep, "cc_cache_tape.bin"))
            # frame.to_csv("{0}{1}{2}".format(root,os.sep,"cc_cache_tape.csv"))

    def __load_cc_carving(self):
        root = self.case.get("out") + os.sep + ".cache"
        try:
            self.case.update({"mem_frame": pd.read_pickle("{0}{1}{2}".format(root, os.sep, "cc_cache.bin"))})
            return C_defy.Return.SUCCESS
        except:
            return C_defy.Return.EINVAL_FILE

    def __load_cc_carving_tape(self, option=0):
        root = self.case.get("out") + os.sep + ".cache"
        if option == 0:
            try:
                self.case.update({"tape": pd.read_pickle("{0}{1}{2}".format(root, os.sep, "cc_cache_tape.bin"))})
                return C_defy.Return.SUCCESS
            except:
                return C_defy.Return.EINVAL_FILE
        else:
            return pd.read_pickle("{0}{1}{2}".format(root, os.sep, "cc_cache_tape.bin"))

    def __concatenate_tape(self):
        cur_off_t = C_defy.MemSchema.default_columns.get("offset", 0)
        off_info_t = C_defy.MemSchema.default_columns.get("offset_info", -1)
        frame = self.case.get("mem_frame", pd.DataFrame(C_defy.MemSchema.default_columns.keys()))
        if frame.empty:
            return
        offset_list = list()

        frame = MemFrameTool.drop(frame, "flag", Offset_Info.EXTRACTED, "more")
        frame = frame.reset_index(drop=True)

        for i in frame.index:
            offset = pickle.loads(frame.loc[i][off_info_t])
            if i + 1 >= frame.shape[0]:
                nxt_offset = [[self.case.get("size"), 0, 0]]
            else:
                nxt_offset = pickle.loads(frame.iloc[i + 1][off_info_t])
            if offset is None or nxt_offset is None:
                continue
            if len(offset) > 1:
                length = len(offset) - 2
                for idx, val in enumerate(offset):
                    if idx < length:
                        offset_list.append([val[1], 'default', offset[idx + 1][0], 0, b'\x00', b'\x00', None, 0, None])
            offset_list.append([offset[-1][1], 'default', nxt_offset[0][0], 0, b'\x00', b'\x00', None, 0, None])

        if len(offset_list) != 0 and frame.iloc[0][cur_off_t] != 0:
            offset = pickle.loads(frame.loc[0][off_info_t])
            offset_list = [[0, 'default', offset[0][0], 0, b'\x00', b'\x00', None, 0, None]] + offset_list

        self.case.update(
            {"tape": pd.DataFrame.from_records(offset_list, columns=C_defy.MemSchema.default_columns.keys())})

    # @ Module Interface
    def module_open(self, id=1):  # Reserved method for multiprocessing
        pass

    def module_close(self):  # Reserved method for multiprocessing
        pass

    def set_attrib(self, key, value):  # 모듈 호출자가 모듈 속성 변경/추가하는 method interface
        pass

    def get_attrib(self, key, value=None):  # 모듈 호출자가 모듈 속성 획득하는 method interface
        pass

    def execute(self, cmd=None, option=None):
        if cmd == C_defy.WorkLoad.LOAD_MODULE:
            if option is None:
                option = "cc"
            self.__log_write("INFO", "Main::Request to load actuator {0}'s module(s).".format(option), always=True)
            return self.__load_module(option)

        if cmd == C_defy.WorkLoad.ATTACH_ACTUATOR:
            self.__log_write("INFO", "Main::Request to add actuator {0}'s module(s).".format(option), always=True)
            if option is None:
                self.__log_write("ERR_", "Main::False parameters.", always=True)
                return False
            elif type(option) != list and len(option) != 3:
                self.__log_write("ERR_", "Main::False parameters {0}.".format(option), always=True)
                return False
            elif option[0] == "cc":
                self.__log_write("ERR_", "Main::Cannot load the default module.", always=True)
                return False
            return self.__attach_actuator(*option)

        if cmd == C_defy.WorkLoad.DETACH_ACTUATOR:
            self.__log_write("INFO", "Main::Request to detach actuator {0}'s module(s).".format(option), always=True)
            if option is None:
                self.__log_write("ERR_", "Main::False parameters.", always=True)
                return False
            elif type(option) != str:
                self.__log_write("ERR_", "Main::False parameters {0}.".format(option), always=True)
                return False
            elif option[0] == "cc":
                self.__log_write("ERR_", "Main::Cannot detach the default module.", always=True)
                return False
            return self.__detach_actuator(option)

        elif cmd == C_defy.WorkLoad.NEW_CASE:
            self.__cleanup_case()
            self.__create_case(option)
            self.set_token(self.case.get("perf", 0))
            self.__log_write("INFO", "Main::The old case is closed and a new case is now created.", always=True)

        elif cmd == C_defy.WorkLoad.CLOSE_CASE:
            self.__cleanup_case()
            self.__log_write("INFO", "Main::The current case is closed.", always=True)

        elif cmd == C_defy.WorkLoad.MODIFY_PARAMETER:
            if str(option[0]) in FiCA.CASE.keys():
                self.case.update({option[0]: option[1]})
                self.__log_write("INFO", "Main::Parameter is changed.")

        elif cmd == C_defy.WorkLoad.CARV and option is None:
            self.__log_write("", "", always=True, init=True)
            self.__log_write("INFO", "Main::Request to run carving process.", always=True)
            self.case.update({"hit": dict()})

            if self.__open:
                self.__file_open(remove=True)

                self.__log_write("INFO", "Carving::Scanning signatures...", always=True)
                self.__set_perf_counter()
                ret = self.__scan_signature()
                if ret < C_defy.Return.EVOID:
                    self.__log_write("INFO", "Carving::Scanning error", always=True)
                    return {}
                self.__log_write("INFO", "Carving::Scanning processing time:{0}.".format(self.__check_perf_counter()),
                                 always=True)

                self.__set_perf_counter()
                self.__cc_carving()
                if self.case.get("extract", True):
                    self.__carving_mergeable(flag=Offset_Info.VALID | Offset_Info.MERGEABLE | Offset_Info.GROUPABLE)
                self.__log_write("INFO", "Carving::Carving processing time:{0}.".format(self.__check_perf_counter()),
                                 always=True)
                hit = self.case.get("hit")
                self.__log_write("INFO", "Carving::Result:{0}".format(hit), always=True)
                self.__save_cc_carving()  # Save Original Data

                self.__set_perf_counter()
                self.__concatenate_tape()
                self.__log_write("INFO", "Carving::Taping is completed:{0}.".format(self.__check_perf_counter()),
                                 always=True)

                if self.case.get("export", False):
                    self.__log_write("INFO", "Carving::Exporting report files...", always=True)
                    try:
                        self.__save_cc_carving_tape()
                    except:
                        pass
                self.__file_close()
                return hit
            else:
                self.__log_write("INFO", "Carving::There is no case to be handled.", always=True)
            return {}

        elif cmd == C_defy.WorkLoad.CARV and type(option) == int:
            if self.__open:
                if option == -1:
                    self.__log_write("", "", always=True, init=True)
                    self.__log_write("INFO", "Main::Request to run carving process.", always=True)
                    self.case.update({"hit": dict()})
                    self.__file_open(remove=True)
                    self.__log_write("INFO", "Carving::Scanning signatures...", always=True)
                    return self.__scan_signature_lbl()
                elif option == 0:
                    ret = self.___scan_signature_lbl()
                    if ret == C_defy.Return.EVOID:
                        self.case.update({"mem_frame": self.__int_mem})
                        self.__int_mem = list()
                        return ret
                    return int(ret / self.__block_counter[0] * 100)
                elif option == 1:
                    self.__int_mem = list()
                    self.__set_perf_counter()
                    self.__cc_carving()
                    if self.case.get("extract", True):
                        self.__carving_mergeable(flag=Offset_Info.VALID | Offset_Info.MERGEABLE | Offset_Info.GROUPABLE)
                    self.__log_write("INFO",
                                     "Carving::Carving processing time:{0}.".format(self.__check_perf_counter()),
                                     always=True)
                    hit = self.case.get("hit")
                    self.__log_write("INFO", "Carving::Result:{0}".format(hit), always=True)
                    self.__save_cc_carving()  # Save Original Data
                    return hit
                elif option == 10:
                    ret = self.__cc_carving_interactive()
                    if ret[0] == C_defy.Return.SUCCESS:
                        self.__count_vector[1] = 0
                    return ret
                elif option == 11:
                    if self.case.get("extract", True):
                        self.__carving_mergeable(flag=Offset_Info.VALID | Offset_Info.MERGEABLE | Offset_Info.GROUPABLE)
                    hit = self.case.get("hit")
                    self.__log_write("INFO", "Carving::Result:{0}".format(hit), always=True)
                    self.__save_cc_carving()  # Save Original Data
                    return hit
                elif option == 2:
                    self.__set_perf_counter()
                    self.__concatenate_tape()
                    stamp = self.__check_perf_counter()
                    self.__log_write("INFO", "Carving::Taping is completed:{0}.".format(stamp), always=True)
                    if self.case.get("export", False):
                        self.__log_write("INFO", "Carving::Exporting report files...", always=True)
                        try:
                            self.__save_cc_carving_tape()
                        except:
                            pass
                    self.__file_close()
                    return stamp
            else:
                self.__log_write("INFO", "Carving::There is no case to be handled.", always=True)
            return {}

        elif cmd == C_defy.WorkLoad.RECARV:
            self.__log_write("", "", always=True, init=True)
            self.__log_write("INFO", "Main::Request to run re-carving process.", always=True)
            self.case.update({"hit": dict()})

            if self.__open:
                self.__load_cc_carving()
                self.__file_open(remove=False)

                self.__set_perf_counter()
                self.__cc_recarving()
                self.__log_write("INFO", "Carving::Carving processing time:{0}.".format(self.__check_perf_counter()),
                                 always=True)
                if self.case.get("extract", True):
                    self.__carving_mergeable(
                        flag=Offset_Info.EXTRACTED | Offset_Info.VALID | Offset_Info.MERGEABLE | Offset_Info.GROUPABLE)

                self.__set_perf_counter()
                self.__concatenate_tape()
                self.__log_write("INFO", "Carving::Taping is completed:{0}.".format(self.__check_perf_counter()),
                                 always=True)
                if self.case.get("export", False):
                    self.__log_write("INFO", "Carving::Exporting report files...", always=True)
                    try:
                        self.__save_cc_carving_tape()
                    except:
                        pass
                self.__file_close()
                return {}
            else:
                self.__log_write("INFO", "Carving::There is no case to be handled.", always=True)
            return {}

        elif cmd == C_defy.WorkLoad.DECODE:
            root = str(option) + os.sep + ".cache"
            try:
                frame = pd.read_pickle("{0}{1}{2}".format(root, os.sep, "cc_cache.bin"))
            except:
                return C_defy.Return.EINVAL_FILE
            if frame.empty:
                return
            copier = frame.copy(deep=False)
            sig_off_t = C_defy.MemSchema.default_columns.get("signature", 1)
            flg_off_t = C_defy.MemSchema.default_columns.get("flag", 3)
            off_info_t = C_defy.MemSchema.default_columns.get("offset_info", -1)
            singular = Offset_Info.VALID | Offset_Info.UNIT

            for i in frame.index:
                if frame.loc[i][off_info_t] is None:
                    copier.at[i, "offset_info"] = "[]"
                else:
                    copier.at[i, "offset_info"] = "{0}".format(pickle.loads(frame.loc[i][off_info_t]))

            copier.to_csv("{0}{1}{2}".format(root, os.sep, "cc_cache.csv"))

            return copier


def str2bool(s):
    if type(s) == str:
        return s.upper() == "TRUE"
    return False


if __name__ == '__main__':
    # py .\ficaLight.py -p G:\1.001 -n TestCase -r RoTCase

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", action="store", dest="path", type=str, default="", required=True)
    parser.add_argument("-n", action="store", dest="name", type=str, default="case", required=False)
    parser.add_argument("-e", action="store", dest="encode", type=str, default="euc-kr", required=False)
    parser.add_argument("-d", action="store", dest="debug", type=bool, default=False, required=False)
    parser.add_argument("-b", action="store", dest="block", type=int, default=4096, required=False)
    parser.add_argument("-s", action="store", dest="sector", type=int, default=512, required=False)
    parser.add_argument("-l", action="store", dest="log", type=str, default="carving.log", required=False)
    parser.add_argument("-m", action="store", dest="mode", type=int, default=1, required=False, choices=range(1, 6))
    parser.add_argument("--count", action="store", dest="count", type=int, default=10000, required=False)
    parser.add_argument("--enable", action="store", dest="enable", type=str, default="true", required=False)
    parser.add_argument("--start", action="store", dest="start", type=int, default=0, required=False)
    parser.add_argument("--end", action="store", dest="end", type=int, default=0, required=False)
    parser.add_argument("--plugin", action="store", dest="plugin", type=str, required=False)
    parser.add_argument("--plugin_path", action="store", dest="plugin_path", type=str, required=False)
    parser.add_argument("-r", action="store", dest="_result", type=str, default=".{0}result".format(os.sep),
                        required=False)
    # parser.add_argument("--timeout",action="store",dest="timeout",type=int, default=5,required=False)
    parser.add_argument("--export", action="store", dest="export", type=str, default="true", required=False)
    # parser.add_argument("-h","--help",action="store",dest="help",type=int,default=0,required=False)
    args = parser.parse_args()

    if args.path == "":
        print("[!] FiCA Light always needs one image file path.")
        sys.exit(0)
    if args.count < 0:
        args.count = 10000

    if args.mode in (1, 2):
        manager = FiCA(debug=args.debug, out=args.log)
        if not manager.execute(FiCA.Instruction.LOAD_MODULE):
            sys.exit(0)

        if args.mode == 1:
            manager.execute(FiCA.Instruction.NEW_CASE,
                            {
                                "name": args.name,
                                "uid": None,
                                "path": args.path,
                                "out": args.result,
                                "off_start": args.start,
                                "off_end": args.end,
                                "cluster": args.block,
                                "sector": args.sector,
                                "encode": args.encode,
                                "extract": str2bool(args.enable),
                                "export": str2bool(args.export)
                            }
                            )
            manager.execute(FiCA.Instruction.CARV)
            manager.execute(FiCA.Instruction.CLOSE_CASE)
            manager.execute(FiCA.Instruction.DECODE, args.result)
        elif args.mode == 2:
            manager.execute(FiCA.Instruction.NEW_CASE,
                            {
                                "name": args.name,
                                "uid": None,
                                "path": args.path,
                                "out": args.result,
                                "off_start": args.start,
                                "off_end": args.end,
                                "cluster": args.block,
                                "sector": args.sector,
                                "encode": args.encode,
                                "extract": str2bool(args.enable),
                                "export": str2bool(args.export)
                            }
                            )
            manager.execute(FiCA.Instruction.RECARV)
            manager.execute(FiCA.Instruction.CLOSE_CASE)
    sys.exit(0)
