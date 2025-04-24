class SteganographyError(Exception):
    """Base class for steganography related errors."""
    pass

class CapacityError(SteganographyError):
    """Raised when the secret data is too large for the cover medium."""
    pass

class EncodingError(SteganographyError):
    """Raised for general encoding failures."""
    pass

class DecodingError(SteganographyError):
    """Raised for general decoding failures or if data/delimiter not found."""
    pass