# -*- coding: utf-8 -*-
"""The modules manager."""


class AdvancedModulesManager(object):
    """The modules manager."""

    _module_classes = {}

    @classmethod
    def GetModuleObjects(cls, advanced_module_filter_expression=None):
        excludes, includes = cls.SplitExpression(cls, expression = advanced_module_filter_expression)

        module_objects = {}
        for module_name, module_class in iter(cls._module_classes.items()):

            if not includes and module_name in excludes:
                continue

            if includes and module_name not in includes:
                continue

            module_object = module_class()
            if module_class.SupportsPlugins():
                plugin_includes = None
                if module_name in includes:
                    plugin_includes = includes[module_name]

                module_object.EnablePlugins(plugin_includes)

            module_objects[module_name] = module_object

        return module_objects



    @classmethod
    def RegisterModule(cls, module_class):
        """Registers a module class.

        The module classes are identified based on their lower case name.

        Args:
          module_class (type): module class.

        Raises:
          KeyError: if parser class is already set for the corresponding name.
        """
        module_name = module_class.NAME.lower()
        if module_name in cls._module_classes:
          raise KeyError('Module class already set for name: {0:s}.'.format(
              module_class.NAME))

        cls._module_classes[module_name] = module_class

    def SplitExpression(cls, expression = None):
        """Determines the excluded and included elements in an expression string.


        """
        if not expression:
            return {}, {}

        excludes = {}
        includes = {}

        for expression_element in expression.split(','):
            expression_element = expression_element.strip()
            if not expression_element:
                continue

            expression_element = expression_element.lower()

            if expression_element.startswith('!'):
                expression_element = expression_element[1:]
                modules = excludes
            else:
                modules = includes

            module, _, plugin = expression_element.partition('/')
            if not plugin:
                plugin = '*'

            modules.setdefault(module, set())
            modules[module].add(plugin)


        return excludes, includes