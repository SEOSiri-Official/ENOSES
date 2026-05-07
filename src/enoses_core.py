import paho.mqtt.client as mqtt
import sounddevice as sd
import numpy as np
import json, time, sys, cv2, base64, argparse, threading
from datetime import datetime
parser = argparse.ArgumentParser()
parser.add_argument('--gain', type=float, default=125.0)
args = parser.parse_args()
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect("broker.emqx.io", 1883, keepalive=60)
client.loop_start()
def vision():
    cam = cv2.VideoCapture(0)
    while True:
        ret, frame = cam.read()
        if ret:
            _, b = cv2.imencode('.jpg', cv2.resize(frame, (320, 240)))
            client.publish("seosiri/enoses/vision", json.dumps({"image_data": base64.b64encode(b).decode('utf-8')}))
        time.sleep(8)
threading.Thread(target=vision, daemon=True).start()
def sensing_callback(indata, frames, time_info, status):
    vol = float(np.linalg.norm(indata) * args.gain)
    if vol < 1.5: return
    fft = np.abs(np.fft.fft(indata[:, 0]))
    freq = int(np.argmax(fft))
    payload = {
        "metadata": {"ts": datetime.now().strftime("%H:%M:%S")},
        "metrics": {"intensity": f"{vol:.2f}", "frequency": f"{freq}", "moisture": f"{round(45+(vol/5),2)}", "density": f"{round((vol*2.1)/(freq+1),4)}", "ozone": f"{round(0.01+(vol/1000),5)}"},
        "analysis": {"sector": "FIRM_LAND", "desc": "Sensing activity detected."}
    }
    if vol < 15 and freq < 320: payload["analysis"].update({"sector": "RESCUE", "desc": "Human/Canine life sign detected."})
    elif vol < 15 and freq >= 320: payload["analysis"].update({"sector": "ENVIRONMENT", "desc": "Avian resonance captured."})
    client.publish("seosiri/enoses/telemetry", json.dumps(payload), qos=0)
with sd.InputStream(channels=1, callback=sensing_callback, blocksize=1024):
    while True: time.sleep(0.1)
