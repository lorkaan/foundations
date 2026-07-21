from abc import ABC, abstractmethod


class BaseBackend(ABC):
    """
    Base interface for all backend providers.

    Backends should be:
    - replaceable
    - stateless where possible
    - independently configurable
    """

    def __init__(self, **config):
        self.config = config

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verify backend availability.
        """
        raise NotImplementedError
    
class StorageBackend(BaseBackend):

    @abstractmethod
    def save(self, filename, content):
        raise NotImplementedError


    @abstractmethod
    def retrieve(self, filename):
        raise NotImplementedError
    
class EncryptionBackend(BaseBackend):

    @abstractmethod
    def encrypt(self, plaintext: bytes) -> bytes:
        raise NotImplementedError


    @abstractmethod
    def decrypt(self, ciphertext: bytes) -> bytes:
        raise NotImplementedError


    @abstractmethod
    def rotate_key(self):
        raise NotImplementedError