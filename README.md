# HeyGen Streaming Avatar Example

This project demonstrates how to set up a basic streaming avatar application using HeyGen's API. It includes a Python Flask backend to manage sessions and a TypeScript frontend to display the streaming avatar.

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Before you begin, ensure you have the following installed:

* **Node.js and npm (or yarn):** For running the frontend.
    * [Download Node.js](https://nodejs.org/en/download/)
* **Python 3.x:** For running the backend.
    * [Download Python](https://www.python.org/downloads/)
* **Git:** For cloning the repository.
    * [Download Git](https://git-scm.com/downloads)
* **HeyGen API Key:** You will need an API key from HeyGen to use their streaming avatar service.
    * [Get HeyGen API Key](https://www.heygen.com/)

### Installation

1.  **Clone the Repository:**

    ```bash
    git clone [https://github.com/JoanneHing/HeyGenModule.git](https://github.com/JoanneHing/HeyGenModule.git)
    cd HeyGenModule
    ```

2.  **Backend Setup (Python Flask):**

    a.  Create a virtual environment (recommended):

        ```bash
        python -m venv venv
        # On Windows
        .\venv\Scripts\activate
        # On macOS/Linux
        source venv/bin/activate
        ```

    b.  Install the required Python packages:

        ```bash
        pip install -r requirements.txt
        ```
        (Note: You will need to create a `requirements.txt` file if it doesn't exist, containing `Flask`, `python-dotenv`, `requests`, `Flask-Cors`)
        or you can install them directly
        ```bash
        pip install Flask python-dotenv requests Flask-Cors
        ```

        Example `requirements.txt`:
        ```
        Flask
        python-dotenv
        requests
        Flask-Cors
        ```

    c.  Create a `.env` file in the root directory of the project and add these HeyGen API Key:

        ```
        HEYGEN_API_KEY="ACTUAL_HEYGEN_API_KEY"
        FLASK_ENV=development
        PORT=3001
        ```
        Replace `"ACTUAL_HEYGEN_API_KEY_HERE"` with the actual HeyGen API Key.

3.  **Frontend Setup (TypeScript):**

    a.  Navigate to the project root directory (if you're not already there).

    b.  Install the Node.js dependencies:

        ```bash
        npm install
        # or if you use yarn
        yarn install
        ```

### Running the Application

1.  **Start the Backend Server:**

    Open a new terminal, navigate to the project root, activate your virtual environment, and run the Flask application:

    ```bash
    # Ensure your virtual environment is activated
    # You should see a (venv) before your device name
    python app.py
    ```
    The backend server should start on `http://localhost:3001`

2.  **Start the Frontend Development Server:**

    Open another new terminal, navigate to the project root, and start the Vite development server:

    ```bash
    npm run dev
    # or if you use yarn
    yarn dev
    ```
    This will usually start the frontend on `http://localhost:5173`

### Testing the Application

1.  **Create a New Streaming Session:**

    Open your web browser and navigate to the backend endpoint for creating a new session. For example, if your backend is running on `localhost:3001`, you would typically make a POST request to an endpoint like `/api/avatar/create`.

    You can use tools like Postman, Insomnia, or a simple `curl` command to initiate a session. Here's an example `curl` command (adjust the avatar ID as needed):

    ```bash
    curl -X POST http://localhost:3001/api/avatar/create \
    -H "Content-Type: application/json" \
    -d '{"avatar_id": "ACTUAL_AVATAR_ID", "quality": "medium"}'
    ```
    Replace `ACTUAL_AVATAR_ID` with actual IDs from your HeyGen account. If it is not set, the default avatar_id would be chosen.

    Upon successful creation, the backend will return a `local_session_id` (or `session_id`).

2.  **View the Streaming Avatar:**

    Once you have a `local_session_id` (or `session_id`) from the previous step, open your browser and navigate to the frontend URL, appending the `local_session_id` as a query parameter:

    ```
    http://localhost:5173/?local_session_id=ACTUAL_SESSION_ID_HERE
    ```
    Replace `ACTUAL_SESSION_ID_HERE` with the actual session ID obtained from the `create` endpoint.

    You should now see the streaming avatar in your browser. (But this part is currently on debugging stage)

## Project Structure

* `app.py`: The Python Flask backend application for managing HeyGen streaming sessions.
* `index.html`: The main HTML file for the frontend, which loads the streaming avatar.
* `src/main.ts`: The TypeScript code for the frontend, responsible for connecting to the HeyGen streaming avatar.
* `.env`: This contains HeyGen API key.
* `requirements.txt`: Lists Python dependencies.
* `package.json`: Frontend dependencies and scripts for npm/yarn.