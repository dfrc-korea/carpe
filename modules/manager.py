# -*- coding: utf-8 -*-
"""The modules manager."""


class ModulesManager(object):
    """The modules manager."""

    _module_classes = {}

    @classmethod
    def GetModuleObjects(cls, module_filter_expression=None):
        excludes, includes = cls.SplitExpression(cls, expression = module_filter_expression)

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

    @classmethod
    def _GetParsers(cls, module_filter_expression=None):
        """Retrieves the registered parsers and plugins.
        Args:
          module_filter_expression (Optional[str]): parser filter expression,
              where None represents all parsers and plugins.
              A module filter expression is a comma separated value string that
              denotes which modules should be used.
        Yields:
          tuple: containing:
          * str: name of the module:
          * type: module class (subclass of BaseModule).
        """
        excludes, includes = cls.SplitExpression(cls, expression=module_filter_expression)

        for module_name, module_class in cls._module_classes.items():
            # If there are no includes all parsers are included by default.
            if not includes and module_name in excludes:
                continue

            if includes and module_name not in includes:
                continue

            yield module_name, module_class

    @classmethod
    def GetModulesInformation(cls):
        """Retrieves the modules information.
        Returns:
          list[tuple[str, str]]: modules names and descriptions.
        """
        modules_information = []
        for _, parser_class in cls._GetParsers():
            description = getattr(parser_class, 'DESCRIPTION', '')
            modules_information.append((parser_class.NAME, description))

        return modules_information

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