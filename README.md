# 🎟️ Premier League Ticket System - High Concurrency Simulation

![Python](https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68-009688?style=for-the-badge&logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)
![Grafana](https://img.shields.io/badge/Grafana-Monitoring-F46800?style=for-the-badge&logo=grafana)

**Author:** Eduardo Richie Imanuell (2702234466)  
**Course:** Cloud Computing - Computer Science, BINUS University

---

## 📖 Project Overview
This project simulates a **High-Demand Ticketing System** (similar to Ticketmaster or Loket.com) designed to handle traffic spikes during flash sales. The primary goal is to demonstrate **Cloud-Native Architecture**, **Observability**, and **Bottleneck Analysis** under stress.

The system is instrumented with **Prometheus & Grafana** to monitor the "Golden Signals" (Latency, Traffic, Errors, and Saturation).

### 🚀 Key Features
* **Microservices-Ready:** Fully containerized using Docker & Docker Compose.
* **High Performance API:** Built with FastAPI (Asynchronous Python).
* **Database Optimization:** Implemented SQLAlchemy Connection Pooling.
* **Caching & Locking:** Redis integration for stock management.
* **Real-time Monitoring:** Custom Grafana Dashboards visualizing RPS, p95 Latency, and CPU usage.
* **Load Testing:** Automated stress testing scenarios using **k6**.

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | Python / FastAPI | High-performance async web framework. |
| **Database** | PostgreSQL | Relational database for transactions. |
| **Cache** | Redis | In-memory data store for stock caching. |
| **Monitoring** | Prometheus | Metric collection & scraping. |
| **Visualization** | Grafana | Real-time observability dashboard. |
| **Load Testing** | k6 (Grafana Labs) | Simulating thousands of concurrent users. |
| **Orchestration** | Docker Compose | Local container management. |

---

## ⚙️ How to Run

### 1. Prerequisites
Ensure you have **Docker Desktop** installed and running on your machine.

### 2. Clone & Start
```bash
git clone https://github.com/eduardorichie22/cloud-computing-ticket-system.git
cd cloud-computing-ticket-system

# Build and Start Containers
docker-compose up --build
```
### 3. Access the Application
- Web App: http://localhost:8000
- Grafana Dashboard: http://localhost:3000 (Login: admin / admin)
- Prometheus: http://localhost:9090

### 🔮 Future Improvements
Based on the analysis, the following improvements are recommended for a Production environment:
- Asynchronous Queue (RabbitMQ): To decouple the purchase requests from the database writing process.
- PgBouncer: To manage database connection pooling more efficiently.
- Horizontal Pod Autoscaling (HPA): Using Kubernetes to scale the backend pods when CPU usage exceeds 70%.
