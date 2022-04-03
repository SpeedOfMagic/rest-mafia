class UIntConverter:
    @staticmethod
    def encode(uint: int, length: int) -> bytes:
        return uint.to_bytes(length=length, byteorder='big', signed=False)

    @staticmethod
    def decode(raw: bytes) -> int:
        return int.from_bytes(raw, byteorder='big', signed=False)


class StrConverter:
    @staticmethod
    def encode(string: str) -> bytes:
        return string.encode('UTF-8')

    @staticmethod
    def decode(raw: bytes) -> str:
        return raw.decode('UTF-8')


class ArrayConverter:
    @staticmethod
    def encode(arr: list) -> bytes:
        return StrConverter.encode(str(arr))

    @staticmethod
    def decode(raw: bytes) -> list:
        return eval(StrConverter.decode(raw))
