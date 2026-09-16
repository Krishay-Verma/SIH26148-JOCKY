"""
Report encryption using AES-GCM via the cryptography library.

AES-256-GCM provides both confidentiality and integrity (it detects
tampering). Each encryption call generates a fresh random 96-bit nonce
so two encryptions of the same plaintext produce different ciphertexts.

Output format (all bytes, concatenated):
    [ 12-byte nonce ][ encrypted ciphertext ][ 16-byte auth tag ]

The key is a 32-byte (256-bit) value. In this prototype it is
generated fresh per encryption call and returned alongside the
ciphertext so the investigator can store or transmit it separately.
"""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_report(plaintext: bytes) -> tuple[bytes, bytes]:
    """
    Encrypt plaintext bytes with AES-256-GCM.

    Returns:
        (ciphertext_with_nonce, key)

    The caller is responsible for storing the key separately from
    the ciphertext. Without the key, the report cannot be recovered.
    """
    key = os.urandom(32)          # 256-bit key, fresh per investigation
    nonce = os.urandom(12)        # 96-bit nonce, required by GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return nonce + ciphertext, key


def decrypt_report(ciphertext_with_nonce: bytes, key: bytes) -> bytes:
    """
    Decrypt a report encrypted by encrypt_report().

    Raises cryptography.exceptions.InvalidTag if the key is wrong
    or the ciphertext has been tampered with.
    """
    nonce = ciphertext_with_nonce[:12]
    ciphertext = ciphertext_with_nonce[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, associated_data=None)