# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, sys, platform
import importlib.util
sys.path.append(os.path.join(os.path.join(os.path.abspath(os.path.dirname('__file__')), "artifact_analyzer"), "parsers"))

class ArtifactAnalyzer():
    def __init__(self):
        # Artifact Analyzer Init
        self.case_id = ''
        self.evd_id = ''
        self.ParserModuleFile = {}
        self.ParserModuleObject = {}
        self.TargetArtifacts = []
        self.isDefault = True
        self.Status = 0
        self.ArtList_File = os.path.join(os.path.join(os.path.abspath(os.path.dirname('__file__')), "artifact_analyzer"), "artifact_list")
        self.Module_File = os.path.join(os.path.join(os.path.abspath(os.path.dirname('__file__')), "artifact_analyzer"), "parsers")
        self.YAML_File = os.path.join(os.path.join(os.path.abspath(os.path.dirname('__file__')), "artifact_analyzer"), "artifacts")

    def Init_Module(self, _case_id, _evd_id, art_list):
        self.case_id = _case_id
        self.evd_id = _evd_id

        self.LoadTargetArtifacts(art_list)
        self.LoadArtifacts()
        self.LoadModule()
        self.LoadYAML()

    def LoadTargetArtifacts(self, art_list):
        if art_list == 'Default' or art_list == 'default':
            self.isDefault = True
        else:
            for art in art_list:
                self.TargetArtifacts.append(art)

            self.isDefault = False
            
    def LoadArtifacts(self):
        """
            Load Artifact List
        """
        art_file = open(self.ArtList_File, "rt")
        lines = art_file.read().splitlines()
        
        for line in lines:
            module_name = line.split(':')[0]
            file_name = line.split(':')[1]

            if not self.isDefault and module_name not in self.TargetArtifacts:
                continue
            else:
                self.ParserModuleFile[module_name] = file_name

    def LoadModule(self):
        """
            Load Artifact Analyze Module
        """
        for module_name in self.ParserModuleFile.keys():
            file_name = os.path.join(self.Module_File, (self.ParserModuleFile[module_name] + '.py'))
            mod_spec = importlib.util.spec_from_file_location(module_name, file_name)
            mod = importlib.util.module_from_spec(mod_spec)
            mod_spec.loader.exec_module(mod)
            mod_obj = getattr(mod, module_name)()
            self.ParserModuleObject[module_name] = mod_obj
            # TODO: Add System Log (Load Complete)

    def LoadYAML(self):
        """
            Load YAML for each Artifact Analyze Module
        """
        for module_name in self.ParserModuleFile.keys():
            file_name = os.path.join(self.YAML_File, (self.ParserModuleFile[module_name] + '.yaml'))
            mod_obj = self.ParserModuleObject[module_name]

            y_file = open(file_name, 'r')
            data = y_file.read()
            mod_obj.LoadYAML(data)

    def Analyze(self):
        for obj_name in self.ParserModuleObject.keys():
            obj = self.ParserModuleObject[obj_name]
            obj.Parse(self.case_id, self.evd_id)