# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, sys, platform
import importlib.util
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname('__file__')) + "{0}parsers".format(os.sep)))

import pdb
class ArtifactAnalyzer():
    def __init__(self):
        # Artifact Analyzer Init
        self.ParseModuleFile = {}
        self.ParseModuleObject = {}
        self.Status = 0
        self.ArtList_File = os.path.join(os.path.abspath(os.path.dirname('__file__')), "artifact_list")
        self.Module_File = os.path.join(os.path.abspath(os.path.dirname('__file__')), "parsers")
        self.YAML_File = os.path.join(os.path.abspath(os.path.dirname('__file__')), "artifacts")

    def LoadArtifacts(self):
        """
            Load Artifact List
        """
        art_file = open(self.ArtList_File, "rt")
        lines = art_file.read().splitlines()
        
        for line in lines:
            self.ParseModuleFile[line.split(':')[0]] = line.split(':')[1]

    def LoadModule(self):
        """
            Load Artifact Analyze Module
        """
        for module_name in self.ParseModuleFile.keys():
            file_name = self.ParseModuleFile[module_name] + '.py'
            mod_spec = importlib.util.spec_from_file_location(module_name, os.path.join(self.Module_File, file_name))
            mod = importlib.util.module_from_spec(mod_spec)
            mod_spec.loader.exec_module(mod)
            mod_obj = getattr(mod, module_name)()
            self.ParseModuleObject[module_name] = mod_obj
            # TODO: Add System Log (Load Complete)

    def LoadYAML(self):
        """
            Load YAML for each Artifact Analyze Module
        """
        for module_name in self.ParseModuleFile.keys():
            file_name = os.path.join(self.YAML_File, (self.ParseModuleFile[module_name] + '.yaml'))
            mod_obj = self.ParseModuleObject[module_name]

            y_file = open(file_name, 'r')
            data = y_file.read()
            mod_obj.LoadYAML(data)

    def Analyze(self, case_id, evd_id):
        for obj_name in self.ParseModuleObject.keys():
            obj = self.ParseModuleObject[obj_name]
            obj.Parse(case_id, evd_id)


a = ArtifactAnalyzer()
a.LoadArtifacts()
a.LoadModule()
a.LoadYAML()
a.Analyze(0, 0)