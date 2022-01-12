class Payload:
    """Placeholder class for passing items to requests.post"""
    
    def __init__(self, *, data=None, json=None, files=None):
        """
        The parameters in requests.post
        Is is best only to use one parameter

        Parameters:
            data: usually bytes
            json: can be dict or list or other json serializable data
            files: dict of file pointers
        """
        self.data = data
        self.json = json
        self.files = files
