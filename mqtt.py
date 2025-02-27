import json
import logging
import requests
import paho.mqtt.client as mqtt

OTA_VERSION_URL = 'https://api.tenclass.net/xiaozhi/ota/'
MAC_ADDR = '58:1C:F8:A5:28:55'

# MQTT 代理配置
mqtt_info = {
    "endpoint": "post-cn-apg3xckag01.mqtt.aliyuncs.com",
    "client_id": "GID_test@@@84_F7_03_D9_E8_96",
    "username": "Signature|LTAI5tF8J3CrdWmRiuTjxHbF|post-cn-apg3xckag01",
    "password": "pLIiMHflT64K4v6083Fq5xM5Z5I=",
    "publish_topic": "device-server",
    "subscribe_topic": "devices/84_F7_03_D9_E8_96"}

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def on_connect(client, userdata, flags, rc, pr):
    """MQTT 连接回调函数"""
    if rc == 0:
        logging.info("Connected to MQTT broker successfully.")
        # 订阅小智AI相关主题
        client.subscribe(mqtt_info['subscribe_topics'])
    else:
        logging.info(f"Failed to connect, return code {rc}.")


def on_message(client, userdata, msg):
    """MQTT 消息接收回调函数"""
    payload = msg.payload.decode()
    logging.info(f"Received message on topic {msg.topic}: {payload}")
    # 在这里处理从小智AI收到的消息
    # 例如：将接收到的文本发送到语音合成模块


def connect_to_broker():
    """连接到 MQTT 代理"""
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_info['client_id'])
    client.username_pw_set(username=mqtt_info['username'], password=mqtt_info['password'])
    client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                   tls_version=mqtt.ssl.PROTOCOL_TLS, ciphers=None)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(host=mqtt_info['endpoint'], port=8883)
        return client
    except Exception as e:
        logging.info(f"Failed to connect to MQTT broker: {e}")
        return None


def publish_message(client, topic, message):
    """发布消息到指定主题"""
    client.publish(topic, message)
    logging.info(f"Published message to topic {topic}: {message}")


def main():
    # 连接到 MQTT 代理
    client = connect_to_broker()
    if client is None:
        return

    try:
        # 启动网络循环
        client.loop_start()

        # 发布消息到小智AI
        message = "你好，小智！"
        publish_message(client, mqtt_info['publish_topic'], message)

        # 持续运行，等待消息
        while True:
            pass

    except KeyboardInterrupt:
        logging.info("\nExiting.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
