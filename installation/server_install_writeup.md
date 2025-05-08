# Server Installation Guide for Stormvogel-2025

## Overview

* **App Backend (WSGI application)**
  Runs local backend processes

* **Gunicorn (WSGI server)**
  Receives requests from Nginx over a UNIX socket

* **Nginx (HTTP(S) proxy server)**
  Handles remote access, HTTPS, load balancing, etc.

---

## Requirements

1. Server has at least 16 GB of storage
2. Server has at least 4 GB of RAM
3. Preferably use Ubuntu 24.04.2 LTS (Noble Numbat)

### Verifying Server Specs

```bash
uname -a             # Check distribution
free -h              # Check RAM
lsblk                # Check storage
```

---

## Step 0: App Setup

1. **Get SSH access to the server** — you must be a sudo user.

2. **Create an unprivileged user**, e.g., `serverhost0`:

```bash
sudo adduser serverhost0
sudo -u serverhost0 -i   # To act as the user
```

3. **\[Optional: If the repo is private]**

   * Generate SSH key pair: `ssh-keygen -t ed25519`
   * Save it in: `/home/serverhost0/.ssh/`
   * Provide the public key to the Stormvogel Playground team to add as a deploy key

4. **\[Optional: If the repo is public]**

   * Add the public key to your GitHub account

5. **Clone the repository:**

```bash
sudo -u serverhost0 -i
GIT_SSH_COMMAND='ssh -i ~/.ssh/[key_name]' git clone git@github.com:GiPHouse/Stormvogel-2025.git
```

Now you should have `/home/serverhost0/Stormvogel-2025`

> **Note:** Repo should contain `system_deps.sh` and `local_deps.sh`

---

## Step 1: App System-Wide Dependencies

1. **Run the system dependencies script:**

```bash
chmod +x /home/serverhost0/Stormvogel-2025/system_deps.sh
sudo /home/serverhost0/Stormvogel-2025/system_deps.sh serverhost0
```
   
* If install fails, read the system_deps.sh file for details
* Installs docker and gvisor
* Adds `serverhost0` to the docker group
* Installs python3, pip3, (not installed: nodejs, npm)

> **Retrospective Note:** No need for node and npm here see step 2 note for context **Preferred option.**

---

## Step 2: App Local Dependencies

1. **Run the local dependencies script:**

```bash
sudo -u serverhost0 -i
chmod +x /home/serverhost0/Stormvogel-2025/local_deps.sh
./home/serverhost0/Stormvogel-2025/local_deps.sh 
```

* Installs Python dependencies (flask, docker, etc.)
* (not installed: Installs Node dependencies)
* If you did install node and nmp install then build dist folder as follows (in frontend folder):
```bash
(npm install)
(npm run build)
```
* verify that frontend/dist exists

> **Retrospective Note:** You don’t have to install full frontend dependencies. You can build the frontend locally and just `scp` the `dist/` folder to the server. 
The .sh files have been updated not to install these (commented out) **Preferred option.**

---

## Step 3: Gunicorn WSGI Server

* Should be installed already with other local dependencies (`requirements.txt`)
* We can test the server locally:

```bash
gunicorn --bind 127.0.0.1:5000 app:app (backend dir)
```

* In another window you can run:
```bash
curl -c cookies.txt -X POST http://localhost:5000/startup \
-H "Content-Type: application/json" \
-d '{}'
```
This creates a container and stores the cookies (for session details) in cookies.txt

* You should receive something like:
```bash
{"message":"Succeeded in launching container","status":"success"}
```

* Try running code in the container:
```bash
curl -b cookies.txt -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"hello\")"}'
```

* You should see:
```bash
{"output_html":null,"output_non_html":"hello","status":"success"}
```

* Now try closing the container:
```bash
curl -b cookies.txt -X POST http://localhost:5000/stop \
  -H "Content-Type: application/json" \
  -d '{}'
```

* You should see:
```bash
{"status": "success", "message": "Sandbox stopped"}
```

* Note that you can also see what happens in the backend logs
* You can use `tmux` for terminal multiplexing

---

## Step 4: Nginx HTTP(S) Proxy Server

### Installation:

```bash
sudo apt update && sudo apt install nginx
```

### HTTPS Setup (requires a domain):

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d [domain].com
```

### Socket Permissions:

```bash
# Directory traversal permissions
chmod o+x /home/serverhost0
chmod o+x /home/serverhost0/Stormvogel-2025
chmod o+x /home/serverhost0/Stormvogel-2025/backend
chmod o+x /home/serverhost0/Stormvogel-2025/frontend
chmod o+x /home/serverhost0/Stormvogel-2025/frontend/dist
chmod -R o+r /home/serverhost0/Stormvogel-2025/frontend/dist
```

### Nginx Configuration:

Create file: `/etc/nginx/sites-available/stormvogel`

#### HTTPS with Redirect:

```nginx
#HTTP to HTTPS
server {
    listen 80;
    server_name [domain].com;

    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name [domain].com;

    ssl_certificate /etc/letsencrypt/live/[domain].com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/[domain].com/privkey.pem;

    root /home/serverhost0/Stormvogel-2025/frontend/dist;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://unix:/home/serverhost0/Stormvogel-2025/backend/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### HTTP-only (No domain, IP-only):

Create file: `/etc/nginx/sites-available/stormvogelhttp`

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /home/serverhost0/Stormvogel-2025/frontend/dist;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://unix:/home/serverhost0/Stormvogel-2025/backend/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Activate Nginx Config:

* We need to add a system link to sites-enabled:
```bash
sudo ln -s /etc/nginx/sites-available/[config] /etc/nginx/sites-enabled/
```

* To remove use:
```bash
sudo rm /etc/nginx/sites-enabled/[config]
```

* Check nginx enabled configs for errors and conflicts
```bash
sudo nginx -t
```

* If this fails you might have to remove the default (probably also listening on 80)
```bash
sudo rm /etc/nginx/sites-enabled/default
```

---

## Step 5: running the server

* nginx config is enables we can now do the run the server
* Bind app process to a unix socket using gunicorn (in backend directory):
* Give nginx permission 
* Run nginx

* This is done by running the `start_server.sh`

* Access app via `https://[domain].com` (if using HTTPS)
* Or via `http://[server_ip]`           (if using HTTP only)

* if not working check server firewall:
```bash
sudo ufw status
sudo ufw alllow 80 (for http)
```

---
