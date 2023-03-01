class PBPException(Exception):
    """
    Placeholder for a more specific exception.
    """

    def __init__(self, msg: str):
        super().__init__(f"PBPException({msg})")
