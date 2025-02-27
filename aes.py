from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def aes_ctr_encrypt(key, nonce, plaintext):
    """
    使用AES算法和CTR模式加密明文。

    AES（高级加密标准）是一种对称加密算法，适用于加密大量数据。
    CTR（计数器）模式是一种将块密码转换为流密码的加密模式，允许并行加密和解密，
    以及对加密数据的随机访问。

    :param key: 加密密钥，必须为16、24或32字节长。
    :param nonce: 一个不重复的数值，用于增加加密的安全性。通常与密钥一起使用，以确保即使使用相同的密钥，加密输出也是唯一的。
    :param plaintext: 需要加密的明文数据。
    :return: 加密后的密文数据。
    """
    # 创建一个AES加密器，使用给定的密钥和CTR模式。
    # 使用default_backend()作为加密后端，它是一个默认的、与平台无关的加密后端。
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())

    # 创建一个加密器对象，用于执行加密操作。
    encryptor = cipher.encryptor()

    # 对明文数据进行加密。首先调用update方法处理大部分数据，
    # 然后调用finalize_options方法处理剩余数据（如果有）并完成加密过程。
    # 这种方式可以处理任意长度的明文数据。
    return encryptor.update(plaintext) + encryptor.finalize()



def aes_ctr_decrypt(key, nonce, ciphertext):
    """
    使用AES-CTR模式解密数据。

    AES-CTR模式是一种对称加密模式，其中密钥和nonce（数字仅使用一次）用于加密和解密过程。
    CTR模式将块加密器用作基于块的流加密器，允许并行加密和解密，以及在加密和解密过程中随机访问数据。

    参数:
    key (bytes): 用于解密的密钥，必须是16、24或32字节长。
    nonce (bytes): 用于解密的nonce值，必须与加密时使用的值相同。
    ciphertext (bytes): 要解密的密文。

    返回:
    bytes: 解密后的明文。
    """

    # 创建Cipher对象，指定加密算法为AES，模式为CTR，并使用默认的后端。
    # key和nonce作为参数用于初始化Cipher对象。
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())

    # 创建解密器对象。
    # 解密器对象允许我们处理密文并生成明文。
    decryptor = cipher.decryptor()

    # 使用解密器对象更新密文并获取解密后的数据。
    # 解密过程分为两步：首先使用update方法处理密文的大部分，
    # 然后使用finalize方法处理密文的剩余部分并完成解密过程。
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    # 返回解密后的明文。
    return plaintext

def test_aes():
    nonce = "0100000030894a57f148f4f900000000"
    key = "f3aed12668b8bc72ba41461d78e91be9"

    plaintext = b"Hello, World!"

    # Encrypt the plaintext
    ciphertext = aes_ctr_encrypt(bytes.fromhex(key), bytes.fromhex(nonce), plaintext)
    logging.info(f"Ciphertext: {ciphertext.hex()}")

    # Decrypt the ciphertext back to plaintext
    decrypted_plaintext = aes_ctr_decrypt(bytes.fromhex(key), bytes.fromhex(nonce), ciphertext)
    logging.info(f"Decrypted plaintext: {decrypted_plaintext}")


if __name__ == "__main__":
    test_aes()