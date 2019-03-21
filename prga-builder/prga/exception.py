"""
PRGA's exception and error types.
"""

__all__ = ["PRGAInternalError", "PRGAAPIError"]

class PRGAInternalError(RuntimeError):
    '''Critical internal error within PRGA flow.

    As an API user, you should never see this type of exception. If you get such an error, please email
    angl@princeton.edu with a detailed description and an example to repeat this error. We thank you for help
    developing PRGA!
    '''
    pass

class PRGAAPIError(PRGAInternalError):
    """An error of an API misuse.

    This error is thrown when the API is not used correctly.
    """
    pass
