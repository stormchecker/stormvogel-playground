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
└── Dockerfile      # Dockerfile with the stormvogel playground
```

---

## 🚀 Setup Instructions

### **Backend Setup (Flask)**
1. install docker: deamon and cli (or docker-desktop:))
    (TODO: further details)

2. Install flask:
    ```bash
    pip install flask
    pip install flask_cors
    ```

3. Install python docker api:
    ```bash
    pip install docker
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
    python3 app.py (--debug)
    ```

### **Running backend (Flask)**
1. in frontend folder:
    ```bash
    npm run (build/dev)
    ```

---

### **

## 🤝 Collaboration Guidelines

### **Branching Strategy**
- `main`: Stable branch, with only stable versions of the project.
- `dev`: Active development branch where features are integrated.
- Feature branches: Named using the format `feature/<your-name>/<feature-name>`. For example, `feature/ben/usersessionfix`.
- In general you never work on `main` or `dev` branches but only in feature branches that you merge to `dev`

### **Development Workflow (first time)**

#### **1. First-Time Setup**
Clone and navigate to the repository:
```bash
git clone <repository-url>
cd <repository-folder>
```

#### **2. Sync with the Latest Changes**
Switch to the `dev` branch and pull the latest changes:
```bash
git checkout dev
git pull origin dev
```

#### **3. Some usefull things**
Get information on what branch you are on, whether it is up-to-date, things to commit etc
```bash
git status
```
See all branches (and the one you are on)
```bash
git branch -a
```
To update all meta info locally (sync it with remote):
```bash
git fetch --all --prune
```
If you want to put changes in one file in seperate commits then you can only add specific changes of files with -p flag:
```bash
git add -p <file-name>
```
Go through the "hunks", y for accept add to commmit (stage), n for don't do that, q for quit adding.
Don't forget to commit once you stages (added) everything you want to commit.

### **Development Workflow (continuous)**

#### **1. Sync with the Latest Changes**
IMPORTANT: If you are continueing with a feature check step 4 (Synchronize with dev branch!).
OTHERWISE: Switch to the `dev` branch and pull the latest changes:
```bash
git checkout dev
git pull origin dev
```

#### **2. Create Your Own Feature Branch**
```bash
git checkout -b feature/<your-name>/<feature-name>
```

#### **3. Commit Your Changes**
1. Stage your changes:
    ```bash
    git add <file>
    ```
2. Commit with a meaningful message:
    ```bash
    git commit -m "Add user authentication module"
    ```

#### **4. When you stop working**
If you are done with the feature (or you don't want to work in current branch anymore) then push changes.
Continue with steps 5 till 9.
```bash
git push -u origin feature/<your-name>/<feature-name>
```
If you are not done with the feature and want to continue in your current branch later.
Once you continue working do the following (synchronizing with dev branch)
1. Commit work (alwasy before you swith branches):
    ```bash
    git add .
    git commit
    ```
2. Switch to `dev` branch:
    ```bash
    git checkout dev
    ```
3. Pull latst changes from `dev` branch:
    ```bash
    git pull origin dev
    ```
4. Switch back to your feature branch:
    ```bash
    git checkout feature/<your-name>/<feature-name>
    ```
5. Merge `dev` into your feature branch:
    ```bash
    git merge dev 
    ```
    Resolve any merge conflicts. Look this up if you don't know how to.
    If merging fails you can always revert merge with:
    ```bash
    git merge --abort
    ```
    But now you won't have a synchronized feature branch, so a pull request will likely also fail to merge.

#### **5. Create a Pull Request (PR) to `dev`**
1. Open the **GitHub repository** in your browser.
2. Click on the **Pull Requests** tab.
3. Click **"Compare & pull request"**.
4. Set the base branch to `dev` and the compare branch to your feature branch.
5. Add a title and description for your PR.
6. Click **"Create pull request"**.

#### **6. Merge to `dev` after Review**
Once your PR is reviewed and approved, merge it to the `dev` branch.

#### **7. Sync with Latest `dev` Changes**
After merging your PR, switch back to the `dev` branch:
```bash
git checkout dev
git pull origin dev
```

#### **8. Stable Release to `main`**
- When the `dev` branch is stable and ready for release, the project maintainer will merge it into `main`.

#### **9. Clean Up Your Branch**
Locally delete your branch:
```bash
git branch -d feature/<your-name>/<feature-name>
```
Delete the branch on GitHub:
```bash
git push origin --delete feature/<your-name>/<feature-name>
```

---

## 📜 License 
This project is licensed under the [TODO](LICENSE).

---

## 🔗 Links
- Storm model checker: [Storm](https://www.stormchecker.org/)
- Stormpy python bindings: [Stormpy](https://github.com/moves-rwth/stormpy)
- Stormvogel: [Stormvogel](https://github.com/moves-rwth/stormvogel)
