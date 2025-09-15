# Stormvogel Playground Project 2025

Implementing a server that hosts playgrounds for the Storm(vogel) probabilistic model checker.

**Software stack:**  
1. Backend: Flask  
2. Frontend: Svelte

---

## 📁 Project Layout
```
project-root/
├── backend/        # Flask backend
│   ├── app.py      # Entry point for the backend
│   └── ...         # Additional backend files
├── frontend/       # Svelte frontend
│   ├── src/        # Component source code
│   └── ...         # Other frontend files
```

---

## 🚀 Deployment Setup Instructions
* See `server_installation_writeup.md`

---

## 🚀 Development Setup Instructions

### **Backend Setup (Flask)**

> **Note:** For detailed steps you can also look into `server_installation_writeup` in particular Step 1 and Step 2 

1. install docker: deamon and cli (or docker-desktop :) https://docs.docker.com/engine/install/ubuntu/ )
   also install Gvisor: https://gvisor.dev/docs/user_guide/install/
   To get the docker image we now only need to call this :
```bash
docker pull stormvogel/stormvogel
```

2. Install backend dependencies (probably want to use a pip or conda environment):
```bash
pip install requirements.txt
```

3. Create an environment file with a secret key in `backend/.env`:
```bash
python3 -c "import secrets; print(f'FLASK_SECRET_KEY=\"{secrets.token_urlsafe(32)}\"')" > backend/.env
```

### **Frontend Setup (Svelte)**
1. Install flask:
   ```bash
    npm install <in-frontend-folder> 
    npm run dev
    ```

### **Running backend (Flask)**
1. in backend folder:
    ```bash
    python3 app.py <in-backend-folder>
    gunicorn --bind 127.0.0.1:5000 app:app (can also be used but does not set debug flag)
    ```

### **Running frontend (Svelte)**
1. in frontend folder:
    ```bash
    npm run dev
    ```

### Testing

1. Vitest frontend testing (unit)
    * In frontend directory
    * To get a coverage report of the frontend run:
    ```bash
    npm run coverage 
    ```
    * To just test the frontend:
    ```bash
    npm test
    ```

2. Playwright frontend testing (integration) 
    * In frontend directory
    ```bash
    npm run playwright
    ```
    * You can also run the tests in ui mode:
    ```bash
    npm run playwright:ui
    ```
3. Pytest backend testing (unit)
    * In backend directory
    ```bash
    pytest
    ```

---

## Notes about the project
1. Container closing is not entirely foolproof
it doesn't account for abnormal session closing (like browser crash etc)
also if the tabs stay open, so do the containers.

2. Development on firefox is not ideal
There is some issue with running the server locally on firefox
there seems to be some internal timeout that stops requests.
We could not figure out why this happens it is certainly not our code.

3. The memory limit and cpu quota on the containers might need some tuning
Depending on how much cpu you want to give each container,
currently it is unboudned. You can change it in the starup container in sandbox.py.
The memory limit can also be changed as it is qutie low (256MB) right now.

---

## 📜 License 
This project is licensed under the [GPL-3.0 license](LICENSE).

---

## 🔗 Links
- Storm model checker: [Storm](https://www.stormchecker.org/)
- Stormpy python bindings: [Stormpy](https://github.com/moves-rwth/stormpy)
- Stormvogel: [Stormvogel](https://github.com/moves-rwth/stormvogel)
