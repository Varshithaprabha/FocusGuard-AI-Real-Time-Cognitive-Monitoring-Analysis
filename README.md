# FocusGuard: AI Real-Time Cognitive Monitoring & Analysis 🚀

FocusGuard is an intelligent study companion designed to help students and professionals optimize their productivity and focus. By utilizing computer vision, real-time analytics, and web monitoring, the system provides comprehensive insights into your study habits.

## 🌟 Key Features

- **Real-Time Cognitive Monitoring:** Uses AI (YOLO / OpenCV) to track focus levels through your webcam.
- **Interactive Dashboard:** A Vite-powered React frontend presenting real-time analytics, daily averages, and a live timeline of your study sessions.
- **FastAPI Backend:** A robust backend providing high-performance APIs and WebSockets for live data tracking.
- **Smart Analytics:** Compares your current productivity with your 7-day average and provides insights based on the time of day.
- **Browser Extension:** Includes a custom Chrome extension to monitor and manage user focus states.

## 📂 Project Structure

- `app.py`: Main application script to run the AI study helper camera via OpenCV.
- `api.py`: Core FastAPI server handling user authentication, statistics, and live WebSockets.
- `frontend/`: Vite React application serving the data analytics dashboard.
- `extension/`: Chrome browser extension files for web context tracking. 
- `src/`: Core Python logic, covering database operations, computer vision inferences, and logging.
- `run_all.py`: Utility script to orchestrate the backend, frontend, and camera services concurrently.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js and npm
- Valid camera/webcam device for cognitive monitoring

### Installation and Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Varshithaprabha/FocusGuard-AI-Real-Time-Cognitive-Monitoring-Analysis.git
   cd "FocusGuard-AI-Real-Time-Cognitive-Monitoring-Analysis"
   ```

2. **Backend Setup:**
   Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Frontend Setup:**
   Navigate to the `frontend` directory and install the required NPM packages:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Start the Application:**
   Run the global startup script to initialize all internal services in one go:
   ```bash
   python run_all.py
   ```
   This command will:
   - Start the FastAPI server (listening on Port `8000`)
   - Launch the Vite React frontend
   - Open the OpenCV camera tracking system

## 🧠 Technologies Used
- **Backend:** FastAPI, Python, SQLAlchemy, SQLite, Pandas
- **Frontend:** React, Vite, Tailwind CSS (optional depending on configuration)
- **AI / Computer Vision:** OpenCV, YOLO (ONNX/PyTorch models)
- **Extension:** Chrome Extension Framework
