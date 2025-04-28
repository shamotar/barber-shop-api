# Barber Shop API

This project is the backend APIs for the Barbershop application.

## Starting the Docker Containers

To run the Barber Shop API project using Docker, follow these steps:

### Prerequisites

Ensure you have the following installed on your system:
- [Docker](https://www.docker.com/products/docker-desktop/) (For containerization)
- [Docker Compose](https://docs.docker.com/compose/) (For managing multi-container applications)

### Steps to Start the Containers

1. **Clone the Repository**:
   If you haven't already, clone the repository to your local machine:
   ```bash
   git clone https://github.com/shamotar/barber-shop-api.git
   cd barber-shop-api
   ```
2. **Start the Containers**:
    Use Docker Compose to start all the services:
    ```bash
    docker-compose up --build
    ```
3. **Access the services**:
    - **API Docs**: The api docs will be available at <http://localhost:8000/docs>.
    - **Keycloak**: The Keycloak admin console will be available at <http://localhost:8080>.
    - **Database**: MySQL will be running on port `3306`.
    - **phpMyAdmin**: Access phpMyAdmin at <http://localhost:8082>.
    - **Fake SMTP Server**: To view emails sent from the application visit the FakeSMTP UI at <http://localhost:8180>.

### Troubleshooting

- If you encounter issues with container health checks, ensure that the .env file is correctly configured.
- Use the following command to view logs for debugging:
    ```bash
    docker-compose logs -f
    ```
