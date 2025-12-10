# 🚑 Lifeline – IoT Based Accident Detection & Alert System
A real-time IoT accident detection and emergency alert system built using **FastAPI**, **MQTT**, and **PostgreSQL/TimescaleDB**.  
It collects sensor data from IoT devices (accelerometer, gyroscope, GPS), detects accidents using smart algorithms, and stores the data for analytics.

---

## 🔥 Features

- 📡 **IoT Integration via MQTT** (ESP32 / NodeMCU compatible)  
- ⚡ **FastAPI backend** with REST endpoints  
- 🧠 **Accident detection algorithm** based on impact force & tilt  
- 🗄️ **TimescaleDB/PostgreSQL storage**  
- 🛰️ **Live GPS-based tracking**  
- 🔔 **Emergency alert trigger ready (SMS/Call)**  
- 📊 **Dashboard compatible for analytics**  

---

## 🏗️ System Architecture (High-Level)

[IoT Device] → [MQTT Broker] → [FastAPI Backend] → [TimescaleDB]
↓
Accident Detection
↓
SMS / Alerts (Future)


---

## 📁 Project Structure

lifeline/
│
├── main.py # FastAPI + MQTT backend (single-file)
├── requirements.txt # Dependencies
└── README.md # Documentation



---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/lifeline-iot.git
cd lifeline-iot
