# 22MIA1031 Backend Evaluation

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
3. Install dependencies:
   ```bash
   pip install -r vehicle_maintenance_scheduler/requirements.txt
   ```
4. Configure your environment variables. Open the `.env` file in the root directory of this project and paste your credentials:
   ```env
   CLIENT_ID=your_client_id_here
   CLIENT_SECRET=your_client_secret_here
   ACCESS_TOKEN=your_access_token_here
   ```

## Run

1. Start the server:
   ```bash
   uvicorn vehicle_maintenance_scheduler.main:app --reload
   ```

2. Open your browser or API client and navigate to:
   http://127.0.0.1:8000/schedule