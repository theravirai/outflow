# Deployment Architecture & Azure Guide

## What does this component do?
This document details how Outflow transitions from a local development environment to a production-ready application. It provides a complete, step-by-step guide to containerizing the application and deploying it securely to Microsoft Azure App Service using a private Azure Container Registry (ACR), while using Neon as the database.

## 1. Environment Configuration
Outflow strictly adheres to the Twelve-Factor App methodology regarding configuration. All sensitive credentials and environment-specific toggles are injected via environment variables.

Required variables:
*   `SECRET_KEY`: Cryptographic key used by Flask to securely sign session cookies and CSRF tokens.
*   `DATABASE_URL`: The PostgreSQL connection string for the primary database (Neon).
*   `GROQ_API_KEY`: Authentication key required to communicate with the Groq LLM inference endpoints.

## 2. Server Architecture
Flask's built-in development server (`app.run()`) is explicitly not designed for production use, as it cannot handle concurrent requests efficiently and lacks security hardening.

*   **WSGI Server:** In production, Outflow must be served by a production-grade WSGI HTTP Server like **Gunicorn**.
*   **Worker Configuration (Crucial for Azure):** Azure App Services uses TCP health probes to check if the container is alive. If Gunicorn is run in its default single-threaded "sync" mode, these empty TCP connections will cause Gunicorn to hang on socket reads, eventually triggering a 30-second `WORKER TIMEOUT`. To prevent this and fix recurring 503 errors, Outflow's `Dockerfile` explicitly runs Gunicorn with multiple workers and threads (`--workers 2 --threads 4`).

## 3. Full Deployment Guide (Azure Web App + Neon PostgreSQL)

This guide assumes you are developing on a Mac and deploying to Azure's Linux App Service.

### Phase 1: Build the Image Locally
Because modern Apple computers use Apple Silicon (ARM64 architecture) and Azure Linux servers run on Intel/AMD processors (AMD64 architecture), we must explicitly tell Docker to build an Intel-compatible image. Otherwise, Azure will fail to run the container.

1. **Open your terminal** and navigate to the root folder of the `outflow` project.
2. **Build the Docker Image:**
   ```bash
   docker build --platform linux/amd64 -t <your-registry>.azurecr.io/outflow:latest .
   ```

### Phase 2: Test the Image Locally
*Always verify the image works on your local machine and can connect to the remote database before pushing it to the cloud.*

1. **Run the Container (with environment variables):**
   Ensure your `.env` file contains your `DATABASE_URL` (Neon), `GROQ_API_KEY`, and `SECRET_KEY`.
   ```bash
   docker run -d -p 5001:5001 --env-file .env --name outflow-test <your-registry>.azurecr.io/outflow:latest
   ```
   *CRITICAL WARNING:* When defining your `DATABASE_URL` (whether in `.env`, the terminal, Docker Desktop, or Azure), **do not surround the URL in double quotes (`""`)**. The Python `psycopg2` driver will interpret the quotes incorrectly, split the URL at the first `=`, drop the `?sslmode=require` query parameter, and fail to connect.

2. **Verify the App is Running:**
   * Open your browser and navigate to `http://localhost:5001`.
   * If it crashes, check the local logs to debug before deploying: `docker logs outflow-test`

3. **Clean Up:**
   ```bash
   docker stop outflow-test
   docker rm outflow-test
   ```

### Phase 3: Push the Image to Azure
*Upload your tested image to your private Azure Container Registry.*

1. **Log in to Azure and ACR:**
   ```bash
   az login
   az acr login --name <your-registry>
   ```
2. **Push the Image:**
   ```bash
   docker push <your-registry>.azurecr.io/outflow:latest
   ```

### Phase 4: Configure the Azure Web App
1. **Create the Web App:**
   * Go to the Azure Portal -> **App Services** -> **+ Create**.
   * Choose **Docker Container** and **Linux**.
   * Under the **Container** tab, select Azure Container Registry and point it to the `outflow:latest` image.
2. **Set Crucial Environment Variables:**
   Before visiting the site, go to **Settings** -> **Environment variables** and add:
   * `DATABASE_URL` = *(Your Neon URL ending in ?sslmode=require. No quotes!)*
   * `GROQ_API_KEY` = *(Your Groq Key)*
   * `SECRET_KEY` = *(Your Flask Secret)*
   * `WEBSITES_PORT` = `5001` *(Crucial: Tells Azure which port Gunicorn is listening on inside our container)*

### Phase 5: Container Registry Authentication
*By default, Azure Web Apps sometimes fail to pull images from a private ACR resulting in an ImagePullFailure.* 

You can force Azure to authenticate in one of two ways:

**Method A: System-Assigned Managed Identity (Recommended)**
1. Go to your Web App -> **Identity** (under Settings). Turn **Status** to **On** and save.
2. Go to your Container Registry -> **Access control (IAM)** -> **+ Add role assignment**.
3. Select **AcrPull** -> Assign to **Managed identity** -> Select your Web App -> Save.
4. Back in your Web App -> **Deployment Center** -> Set Authentication to **Managed Identity**.

**Method B: Manual Registry Credentials**
If Managed Identity fails, add these to your Web App **Environment variables**:
* `DOCKER_REGISTRY_SERVER_URL` = `https://<your-registry>.azurecr.io`
* `DOCKER_REGISTRY_SERVER_USERNAME` = `<your-registry-name>`
* `DOCKER_REGISTRY_SERVER_PASSWORD` = `<access-key-password-from-registry>`
Make sure Deployment Center Authentication is set back to **Admin Credentials**.

### Phase 6: Future Updates Workflow
Whenever you make changes to the Python code, HTML, or CSS, run these 3 steps to update the live site:

1. **Rebuild:** `docker build --platform linux/amd64 -t <your-registry>.azurecr.io/outflow:latest .`
2. **Push:** `docker push <your-registry>.azurecr.io/outflow:latest`
3. **Restart:** Go to the Azure Portal -> Web App -> Click **Restart**. Wait 60 seconds and refresh your site.

## 4. Pre-Deployment Engineering Checklist
Before promoting a project to production, perform these final verifications:
1. **Security Audit**: Ensure `.env` files are ignored by git. Generate complex passwords and `SECRET_KEY`s.
2. **Database Backup**: Verify automated backups are enabled (handled natively by Neon).
3. **Log & Monitoring**: Configure logging to track 500 server errors and LLM latency.
