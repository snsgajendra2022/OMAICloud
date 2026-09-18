class ModuleRouter:



    def __init__(
        self
    ):

        self.modules={}



    def register(
        self,
        name,
        module
    ):

        self.modules[name]=module



    def execute(
        self,
        name,
        *args,
        **kwargs
    ):


        module=self.modules.get(
            name
        )


        if not module:

            return None



        return module(
            *args,
            **kwargs
        )