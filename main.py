#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import time
import requests
import paho.mqtt.client as mqtt
import threading
import pyaudio
import opuslib
import socket
import logging
from pynput import keyboard as pynput_keyboard
from aes import aes_ctr_encrypt, aes_ctr_decrypt

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

OTA_VERSION_URL = 'https://api.tenclass.net/xiaozhi/ota/'
MAC_ADDR = '00:00:00:00:00:00'

mqtt_info = {}
aes_opus_info = {"type": "hello", "version": 3, "transport": "udp",
                 "udp": {"server": "120.24.160.13", "port": 8884, "encryption": "aes-128-ctr",
                         "key": "263094c3aa28cb42f3965a1020cb21a7", "nonce": "01000000ccba9720b4bc268100000000"},
                 "audio_params": {"format": "opus", "sample_rate": 24000, "channels": 1, "frame_duration": 60},
                 "session_id": "b23ebfe9"}

iot_msg = {"session_id": "635aa42d", "type": "iot",
           "descriptors": [{"name": "Speaker", "description": "当前 AI 机器人的扬声器",
                            "properties": {"volume": {"description": "当前音量值", "type": "number"}},
                            "methods": {"SetVolume": {"description": "设置音量",
                                                      "parameters": {
                                                          "volume": {"description": "0到100之间的整数",
                                                                     "type": "number"}
                                                      }
                                                      }
                                        }
                            },
                           {"name": "Lamp", "description": "一个测试用的灯",
                            "properties": {"power": {"description": "灯是否打开", "type": "boolean"}},
                            "methods": {"TurnOn": {"description": "打开灯", "parameters": {}},
                                        "TurnOff": {"description": "关闭灯", "parameters": {}}
                                        }
                            }
                           ]
           }
iot_status_msg = {"session_id": "635aa42d", "type": "iot", "states": [
    {"name": "Speaker", "state": {"volume": 50}}, {"name": "Lamp", "state": {"power": False}}]}
goodbye_msg = {"session_id": "b23ebfe9", "type": "goodbye"}
local_sequence = 0
listen_state = None
tts_state = None
key_state = None
audio = None
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# udp_socket.setblocking(False)
conn_state = False
recv_audio_thread = threading.Thread()
send_audio_thread = threading.Thread()
mqc = None


def get_ota_version():
    global mqtt_info
    header = {
        'Device-Id': MAC_ADDR,
        'Content-Type': 'application/json'
    }
    post_data = {"flash_size": 16777216, "minimum_free_heap_size": 8318916, "mac_address": f"{MAC_ADDR}",
                 "chip_model_name": "esp32s3", "chip_info": {"model": 9, "cores": 2, "revision": 2, "features": 18},
                 "application": {"name": "xiaozhi", "version": "0.9.9", "compile_time": "Jan 22 2025T20:40:23Z",
                                 "idf_version": "v5.3.2-dirty",
                                 "elf_sha256": "22986216df095587c42f8aeb06b239781c68ad8df80321e260556da7fcf5f522"},
                 "partition_table": [{"label": "nvs", "type": 1, "subtype": 2, "address": 36864, "size": 16384},
                                     {"label": "otadata", "type": 1, "subtype": 0, "address": 53248, "size": 8192},
                                     {"label": "phy_init", "type": 1, "subtype": 1, "address": 61440, "size": 4096},
                                     {"label": "model", "type": 1, "subtype": 130, "address": 65536, "size": 983040},
                                     {"label": "storage", "type": 1, "subtype": 130, "address": 1048576,
                                      "size": 1048576},
                                     {"label": "factory", "type": 0, "subtype": 0, "address": 2097152, "size": 4194304},
                                     {"label": "ota_0", "type": 0, "subtype": 16, "address": 6291456, "size": 4194304},
                                     {"label": "ota_1", "type": 0, "subtype": 17, "address": 10485760,
                                      "size": 4194304}],
                 "ota": {"label": "factory"},
                 "board": {"type": "bread-compact-wifi", "ssid": "mzy", "rssi": -58, "channel": 6,
                           "ip": "192.168.124.38", "mac": "cc:ba:97:20:b4:bc"}}

    response = requests.post(OTA_VERSION_URL, headers=header, data=json.dumps(post_data))
    logging.info(response.text)
    mqtt_info = response.json()['mqtt']


def send_audio():
    global aes_opus_info, udp_socket, local_sequence, listen_state, audio

    key = aes_opus_info['udp']['key']
    nonce = aes_opus_info['udp']['nonce']
    server_ip = aes_opus_info['udp']['server']
    server_port = aes_opus_info['udp']['port']

    # 初始化Opus编码器
    encoder = opuslib.Encoder(16000, 1, opuslib.APPLICATION_AUDIO)

    # 打开麦克风流, 帧大小，应该与Opus帧大小匹配
    mic = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=960)
    try:
        while True:
            if listen_state == "stop":
                continue
                time.sleep(0.1)
            # 读取音频数据
            data = mic.read(960)
            # 编码音频数据
            encoded_data = encoder.encode(data, 960)
            # 打印音频数据
            # logging.info(f"Encoded data: {len(encoded_data)}")
            # nonce插入data.size local_sequence_
            local_sequence += 1
            new_nonce = nonce[0:4] + format(len(encoded_data), '04x') + nonce[8:24] + format(local_sequence, '08x')
            # 加密数据，添加nonce
            encrypt_encoded_data = aes_ctr_encrypt(bytes.fromhex(key), bytes.fromhex(new_nonce), bytes(encoded_data))
            data = bytes.fromhex(new_nonce) + encrypt_encoded_data
            sent = udp_socket.sendto(data, (server_ip, server_port))
    except Exception as e:
        logging.info(f"send audio err: {e}")
    finally:
        logging.info("send audio exit()")
        local_sequence = 0
        udp_socket = None
        # 关闭流和PyAudio
        mic.stop_stream()
        mic.close()


def recv_audio():
    global aes_opus_info, udp_socket, audio

    key = aes_opus_info['udp']['key']
    nonce = aes_opus_info['udp']['nonce']
    sample_rate = aes_opus_info['audio_params']['sample_rate']
    frame_duration = aes_opus_info['audio_params']['frame_duration']
    frame_num = int(frame_duration / (1000 / sample_rate))

    logging.info(
        f"recv audio: sample_rate -> {sample_rate}, frame_duration -> {frame_duration}, frame_num -> {frame_num}")

    # 初始化Opus编码器
    decoder = opuslib.Decoder(sample_rate, 1)
    spk = audio.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, output=True, frames_per_buffer=frame_num)
    try:
        while True:
            data, server = udp_socket.recvfrom(4096)
            # logging.info(f"Received from server {server}: {len(data)}")
            encrypt_encoded_data = data
            # 解密数据,分离nonce
            split_encrypt_encoded_data_nonce = encrypt_encoded_data[:16]
            # 十六进制格式打印nonce
            # logging.info(f"split_encrypt_encoded_data_nonce: {split_encrypt_encoded_data_nonce.hex()}")
            split_encrypt_encoded_data = encrypt_encoded_data[16:]
            decrypt_data = aes_ctr_decrypt(bytes.fromhex(key),
                                           split_encrypt_encoded_data_nonce,
                                           split_encrypt_encoded_data)
            # 解码播放音频数据
            spk.write(decoder.decode(decrypt_data, frame_num))
    # except BlockingIOError:
    #     # 无数据时短暂休眠以减少CPU占用
    #     time.sleep(0.1)
    except Exception as e:
        logging.info(f"recv audio err: {e}")
    finally:
        udp_socket = None
        spk.stop_stream()
        spk.close()


def on_message(client, userdata, message):
    global aes_opus_info, udp_socket, tts_state, recv_audio_thread, send_audio_thread
    msg = json.loads(message.payload)
    logging.info(f"recv msg: {msg}")
    if msg['type'] == 'hello':
        aes_opus_info = msg
        udp_socket.connect((msg['udp']['server'], msg['udp']['port']))
        # 发送 iot msg
        # iot_msg['session_id'] = msg['session_id']
        # push_mqtt_msg(iot_msg)
        # logging.info(f"send iot message: {iot_msg}")
        # 发送 iot status消息
        # iot_status_msg['session_id'] = msg['session_id']
        # logging.info(f"send iot status message: {iot_status_msg}")
        # push_mqtt_msg(iot_status_msg)
        # 检查recv_audio_thread线程是否启动
        if not recv_audio_thread.is_alive():
            # 启动一个线程，用于接收音频数据
            recv_audio_thread = threading.Thread(target=recv_audio)
            recv_audio_thread.start()
        else:
            logging.info("recv_audio_thread is alive")
        # 检查send_audio_thread线程是否启动
        if not send_audio_thread.is_alive():
            # 启动一个线程，用于发送音频数据
            send_audio_thread = threading.Thread(target=send_audio)
            send_audio_thread.start()
        else:
            logging.info("send_audio_thread is alive")
    if msg['type'] == 'tts':
        tts_state = msg['state']
    if msg['type'] == 'goodbye' and udp_socket and msg['session_id'] == aes_opus_info['session_id']:
        logging.info(f"recv good bye msg")
        aes_opus_info['session_id'] = None


def on_connect(client, userdata, flags, rs, pr):
    # subscribe_topic = mqtt_info['subscribe_topic'].split("/")[0] + '/p2p/GID_test@@@' + MAC_ADDR.replace(':', '_')
    # logging.info(f"subscribe topic: {subscribe_topic}")
    # 订阅主题
    # client.subscribe(subscribe_topic)
    logging.info("connect to mqtt server")


def push_mqtt_msg(message):
    global mqtt_info, mqc
    mqc.publish(mqtt_info['publish_topic'], json.dumps(message))


def on_mic_key_press(event):
    global key_state, udp_socket, aes_opus_info, listen_state, conn_state
    if key_state == "press":
        return
    key_state = "press"
    # 判断是否需要发送hello消息
    if conn_state is False or aes_opus_info['session_id'] is None:
        conn_state = True
        # 发送hello消息,建立udp连接
        hello_msg = {"type": "hello", "version": 3, "transport": "udp",
                     "audio_params": {"format": "opus", "sample_rate": 16000, "channels": 1, "frame_duration": 60}}
        push_mqtt_msg(hello_msg)
        logging.info(f"send hello message: {hello_msg}")
    if tts_state == "start" or tts_state == "sentence_start":
        # 在播放状态下发送abort消息
        push_mqtt_msg({"type": "abort"})
        logging.info(f"send abort message")
    if aes_opus_info['session_id'] is not None:
        # 发送start listen消息
        msg = {"session_id": aes_opus_info['session_id'], "type": "listen", "state": "start", "mode": "manual"}
        logging.info(f"send start listen message: {msg}")
        push_mqtt_msg(msg)


def on_mic_key_release(event):
    global aes_opus_info, key_state
    key_state = "release"
    # 发送stop listen消息
    if aes_opus_info['session_id'] is not None:
        msg = {"session_id": aes_opus_info['session_id'], "type": "listen", "state": "stop"}
        logging.info(f"send stop listen message: {msg}")
        push_mqtt_msg(msg)


def on_press(key):
    if key == pynput_keyboard.Key.ctrl_r:
        on_mic_key_press(None)


def on_release(key):
    if key == pynput_keyboard.Key.ctrl_r:
        on_mic_key_release(None)
    # Stop listener
    if key == pynput_keyboard.Key.esc:
        return False


def run():
    global audio, mqtt_info, mqc

    # 获取mqtt与版本信息
    get_ota_version()

    # 监听键盘按键，当按下空格键时，发送listen消息
    listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    # 声音控制
    audio = pyaudio.PyAudio()

    # 创建MQTT客户端实例
    mqc = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_info['client_id'])
    mqc.username_pw_set(username=mqtt_info['username'], password=mqtt_info['password'])
    mqc.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                tls_version=mqtt.ssl.PROTOCOL_TLS, ciphers=None)
    mqc.on_connect = on_connect
    mqc.on_message = on_message
    mqc.connect(host=mqtt_info['endpoint'], port=8883)
    mqc.loop_forever()


if __name__ == "__main__":
    run()
