# Lifeline – IoT Accident Detection & Emergency Alert System

A production-ready FastAPI + MQTT + PostgreSQL backend for real-time IoT accident monitoring, event logging, and emergency alerting.

This system ingests sensor data from IoT devices (accelerometer, gyroscope, GPS), detects accident conditions, stores structured time-series data, and exposes REST APIs for dashboards, mobile apps, or emergency services.

---

## Features

- FastAPI backend with automatic documentation (`/docs`)
- MQTT listener for real-time IoT device ingestion
- PostgreSQL connection pooling for optimized database writes
- Accident detection engine (impact and tilt based)
- Modular architecture (config, db, models, mqtt, utils)
- Health check endpoint (`/health`)
- Docker-ready for deployment

---

## Project Structure

