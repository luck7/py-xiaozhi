import pyaudio
import opuslib
from os import urandom
from aes import aes_ctr_encrypt, aes_ctr_decrypt


def test_audio():
    key = urandom(16)  # AES-256 key
    nonce = urandom(16)  # Initialization vector (IV) or nonce for CTR mode

    logging.info(f"Key: {key.hex()}")
    logging.info(f"Nonce: {nonce.hex()}")

    # 初始化Opus编码器
    encoder = opuslib.Encoder(16000, 1, opuslib.APPLICATION_AUDIO)
    decoder = opuslib.Decoder(16000, 1)
    # 初始化PyAudio
    p = pyaudio.PyAudio()

    # 打开麦克风流, 帧大小，应该与Opus帧大小匹配
    mic = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=960)
    spk = p.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True, frames_per_buffer=960)

    try:
        while True:
            # 读取音频数据
            data = mic.read(960)
            # 编码音频数据
            encoded_data = encoder.encode(data, 960)
            # 加密数据，添加nonce
            encrypt_encoded_data = nonce + aes_ctr_encrypt(key, nonce, bytes(encoded_data))
            # 解密数据,分离nonce
            split_encrypt_encoded_data_nonce = encrypt_encoded_data[:len(nonce)]
            split_encrypt_encoded_data = encrypt_encoded_data[len(nonce):]
            decrypt_data = aes_ctr_decrypt(key, split_encrypt_encoded_data_nonce, split_encrypt_encoded_data)
            # 解码播放音频数据
            spk.write(decoder.decode(decrypt_data, 960))
            # logging.info(f"Encoded frame size: {len(encoded_data)} bytes")
    except KeyboardInterrupt:
        logging.info("停止录制.")
    finally:
        # 关闭流和PyAudio
        mic.stop_stream()
        mic.close()
        spk.stop_stream()
        spk.close()
        p.terminate()


if __name__ == "__main__":
    test_audio()
