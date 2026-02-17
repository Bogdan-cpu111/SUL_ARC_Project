# core/sul_crypto.py
import zlib

class SulCrypto:
    """
    Уникальный модуль шифрования и сжатия SUL.
    Использует ZLIB для сжатия + Циклический XOR (S-U-L) для защиты.
    """
    
    # Ключ шифрования: байты "SUL"
    KEY = b'SUL' 

    @staticmethod
    def _transform(data: bytes) -> bytes:
        """Применяет XOR с ключом SUL циклически."""
        key_len = len(SulCrypto.KEY)
        # Используем bytearray для изменяемости
        result = bytearray(data)
        for i in range(len(result)):
            result[i] ^= SulCrypto.KEY[i % key_len]
        return bytes(result)

    @staticmethod
    def encode_data(data: bytes) -> bytes:
        """Сначала сжимаем, потом шифруем своим алгоритмом."""
        compressed = zlib.compress(data, level=9) # Максимальное сжатие
        encrypted = SulCrypto._transform(compressed)
        return encrypted

    @staticmethod
    def decode_data(data: bytes) -> bytes:
        """Сначала расшифровываем (XOR обратим), потом разжимаем."""
        decrypted = SulCrypto._transform(data)
        try:
            decompressed = zlib.decompress(decrypted)
            return decompressed
        except zlib.error:
            raise ValueError("Ошибка: Неверный ключ или поврежденные данные SUL.")