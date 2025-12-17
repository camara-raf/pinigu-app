# Docker Setup for Pinigu App

This project is containerized using Docker. This allows you to run the application in an isolated environment while keeping your data and configuration on your host machine.

## Prerequisites

-   Docker installed on your system.
-   Docker Compose (often included with Docker Desktop or as a plugin `docker compose`).

## Files Created

The following files were added to support containerization:
-   `Dockerfile`: Defines the image, installing Python dependencies and `curl`.
-   `docker-compose.yml`: Defines the service, ports, and volume mounts.
-   `.dockerignore`: prevents unnecessary files from being copied into the container image.

## How to Run

1.  **Build and Start:**
    Run the following command in the project root:
    ```bash
    docker-compose up -d --build
    ```
    (Or `docker compose up -d --build` if using the plugin version).

2.  **Access the App:**
    Open your browser and navigate to:
    [http://localhost:8501](http://localhost:8501)

3.  **Stop the App:**
    ```bash
    docker-compose down
    ```

## Volume Mounts

The `docker-compose.yml` file maps the following host directories to the container:

-   `./data` -> `/app/data`: Your transaction files and database.
-   `./config` -> `/app/config`: Configuration files like `file_signatures.yaml`.
-   `./logs` -> `/app/logs`: Application logs.

Any changes made to files in these directories on your host will be visible to the container (and vice-versa for data/logs).

## Troubleshooting

-   **Check Logs:**
    ```bash
    docker-compose logs -f
    ```
-   **Rebuild:**
    If you add new dependencies to `requirements.txt`, you need to rebuild the image:
    ```bash
    docker-compose up -d --build
    ```
