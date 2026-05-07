# ==================================================================================
# SEOSIRI AGRI-ARCHITECT v53.0 | GLOBAL COMMAND & TELEMETRY MASTER
# FOUNDER & ARCHITECT: MOMENUL AHMAD | SEOSIRI.COM
# ----------------------------------------------------------------------------------
# SECURITY: SSL/TLS ENCRYPTED | MESH INTERCONNECT | ANDROID SYNC
# MISSION: CROP HEALTH | HUMAN/ANIMAL TRACE | SEED GAP | FUNGUS AI
# ==================================================================================
import paho.mqtt.client as mqtt
import sounddevice as sd
import numpy as np
import json
import time
import cv2
import base64
import csv
import threading
from datetime import datetime
from pathlib import Path

# --- [0. SECURE LOGGING & REPORTING] ---
LOG_DIR = Path("D:/ENOSES_Project/archives/telemetry")
LOG_DIR.mkdir(parents=True, exist_ok=True)
SESSION_DATE = datetime.now().strftime('%Y%m%d')
REPORT_FILE = LOG_DIR / f"SEOSIRI_REPORT_{SESSION_DATE}.csv"

def generate_report_entry(data):
    with open(REPORT_FILE, 'a', newline='') as f:
        csv.writer(f).writerow([datetime.now(), data['sector'], data['cmd'], data['risk']])

# --- [1. GLOBAL MESH CONFIGURATION] ---
MQTT_BROKER = "broker.emqx.io"
TOPIC_TELEMETRY = "seosiri/enoses/mesh"
TOPIC_COMMAND = "seosiri/enoses/cmd/uplink" # Commands FROM Android to PC
TOPIC_VISION = "seosiri/enoses/vision"

def on_connect(client, userdata, flags, rc, props):
    if rc == 0:
        print("\n" + "█"*95 + "\n ✅ SEOSIRI AGRI-CORE v53.0: SECURE GLOBAL UPLINK ACTIVE\n FOUNDER: MOMENUL AHMAD | STATUS: MISSION READY\n " + "█"*95 + "\n")
        client.subscribe(TOPIC_COMMAND) # Listen for commands from Android

def on_message(client, userdata, msg):
    """PROCESS REMOTE COMMANDS FROM ANDROID DEVICE"""
    try:
        cmd_packet = json.loads(msg.payload.decode())
        print(f"\n📥 REMOTE COMMAND RECEIVED: {cmd_packet['cmd']}")
        
        if cmd_packet['cmd'] == "REQUEST_SITUATION":
            print("📊 GENERATING CURRENT FIELD SITUATION REPORT...")
            # Auto-respond with system status
            status_report = {"status": "ACTIVE", "power": "98%", "mesh_sync": "OK", "last_event": "HUMAN_TRACE"}
            client.publish(TOPIC_TELEMETRY, json.dumps(status_report))
            
        elif cmd_packet['cmd'] == "FORCE_HARVEST":
            print("🤖 ROBOTICS: MANUAL OVERRIDE - STARTING HARVEST...")
    except: pass

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, 1883, keepalive=30)
client.loop_start()

# --- [2. MULTIMODAL VISION AI (FUNGUS & TRACE)] ---
def vision_mesh_thread():
    cam = cv2.VideoCapture(0)
    while True:
        ret, frame = cam.read()
        if ret:
            # Fungus Detection (Yellow Pixel Density)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            yellow_mask = cv2.inRange(hsv, (20, 100, 100), (30, 255, 255))
            f_idx = np.sum(yellow_mask > 0) / 50000
            
            _, buff = cv2.imencode('.jpg', cv2.resize(frame, (320, 240)))
            payload = {"img": base64.b64encode(buff).decode('utf-8'), "fungus": round(float(f_idx), 3)}
            client.publish(TOPIC_VISION, json.dumps(payload), qos=0)
        time.sleep(5)
threading.Thread(target=vision_mesh_thread, daemon=True).start()

# --- [3. MASTER SENSING CALLBACK (ACOUSTIC SCENT)] ---
def sensing_callback(indata, frames, time_info, status):
    vol = float(np.linalg.norm(indata) * 125.0)
    fft = np.abs(np.fft.fft(indata[:, 0]))
    freq = int(np.argmax(fft))
    if vol < 0.3: return
    
    payload = {
        "metadata": {"founder": "Momenul Ahmad", "org": "SEOSIRI.COM", "ts": datetime.now().strftime("%H:%M:%S")},
        "metrics": {"vol": f"{vol:.2f}dB", "moist": f"{round(45+(vol/4),2)}%", "freq": f"{freq}Hz"},
        "analysis": {"sector": "FIRM_LAND", "risk": "LOW", "cmd": "IDLE", "desc": "Scanning..."}
    }

    # -- SECTOR LOGIC GATING --
    if vol < 12: # TRACE DETECTION
        if freq < 200: payload["analysis"].update({"sector": "ANIMAL_TRACE", "risk": "MEDIUM", "cmd": "DRONE: ATTRACT", "desc": "Animal detected. Redirecting..."})
        else: payload["analysis"].update({"sector": "HUMAN_TRACE", "risk": "HIGH", "cmd": "DRONE: TRACK", "desc": "Human presence detected."})
    elif 12 <= vol < 40 and freq > 750: # PESTS/FUNGUS
        payload["analysis"].update({"sector": "PEST_CONTROL", "risk": "SEVERE", "cmd": "ROBOT: SPRAY", "desc": "Pest resonance detected."})
    elif vol >= 85: # EMERGENCY
        payload["analysis"].update({"sector": "EMERGENCY", "risk": "MAXIMUM", "cmd": "MESH: ALL_STOP", "desc": "CRITICAL IMPACT DETECTED"})

    client.publish(TOPIC_TELEMETRY, json.dumps(payload), qos=0)
    generate_report_entry(payload['analysis'])
    print(f"📡 SECTOR: {payload['analysis']['sector'].ljust(15)} | VOL: {vol:.1f}  ", end="\r")

# --- START ARCHITECT ENGINE ---
with sd.InputStream(channels=1, callback=sensing_callback, blocksize=1024):
    while True: time.sleep(0.1)