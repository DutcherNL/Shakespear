
class AlreadyRegistered(Exception):
    pass

class ModuleRegister:
    """ This class registers the various models and allows hooking onto those models """

    _modules = {}

    def register(self, module):
        if module._type_id in self._modules:
            msg = 'The model type_id %s is already registered ' % module.__name__
            raise AlreadyRegistered(msg)

        self._modules[module._type_id] = module

    def get_all_modules(self):
        modules = []
        for key, module in self._modules.items():
            modules.append(module)

        return modules

    def get_module(self, type_id):
        return self._modules.get(type_id, None)


registry = ModuleRegister()