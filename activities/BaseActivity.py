class BaseActivity:

    NAME = ""
    DESCRIPTION = ""
    PARAMETERS = {}
    EXAMPLES = []

    @classmethod
    def metadata(cls):
        return {
            "name": cls.NAME,
            "description": cls.DESCRIPTION,
            "parameters": cls.PARAMETERS,
            "examples": cls.EXAMPLES
        }