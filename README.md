# AI Customer Support Bot

This project is a backend for an AI-powered customer support bot designed to simulate and handle customer interactions. The system can answer frequently asked questions, maintain conversational context, and escalate complex queries when necessary. It is built with a FastAPI backend, uses a PostgreSQL database for session tracking, and integrates with a Large Language Model (LLM) for intelligent response generation.

## Features

- **FAQ-Based Responses**: Answers user queries based on a provided dataset of frequently asked questions.
- **Contextual Memory**: Retains the history of the current conversation to provide relevant and coherent responses.
- **Escalation Simulation**: Simulates escalating a query to a human agent when the bot cannot find a satisfactory answer.
- **Session Tracking**: Manages and tracks user chat sessions in a database.
- **Admin Analytics**: Provides endpoints for administrators to get summaries and analytics on bot conversations.

## Technical Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **LLM**: Google Gemini
- **Authentication**: JWT with OAuth2

## Project Structure

```
/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── admin.py
│   │   │   ├── bots.py
│   │   │   └── chat.py
│   │   ├── api.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── llm.py
│   │   └── security.py
│   ├── db/
│   │   ├── crud.py
│   │   ├── models.py
│   │   └── session.py
│   ├── schemas/
│   │   ├── bot.py
│   │   ├── chat.py
│   │   ├── token.py
│   │   └── user.py
│   ├── __init__.py
│   └── main.py
├── .gitignore
├── docker-compose.yml
├── faqs.json
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for Docker-based setup)
- PostgreSQL

### Manual Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/meetptl04/ai-customer-support-bot.git
    cd ai_support_bot_backend
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the environment variables:**
    - Create a file named `.env` in the root directory.
    - Copy the contents of the "Environment Variables" section below into the `.env` file and provide the required values.

### Database Setup with Docker

This project uses Docker to run a PostgreSQL database. This is the recommended way to set up the database for local development.

1.  **Start the database:**
    ```bash
    docker-compose up -d
    ```
    This will start a PostgreSQL container in the background and expose it on port 5432. The database credentials are set in the `docker-compose.yml` file and should be used to construct the `DATABASE_URL` in your `.env` file.

## Running the Application

Once you have completed the installation steps and started the database, you can run the application:

```bash
uvicorn app.main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

## Environment Variables

To run this application, you will need to set the following environment variables in a `.env` file:

- `DATABASE_URL`: The connection string for your PostgreSQL database.
- `GEMINI_API_KEY`: Your API key for the Gemini language model.
- `SECRET_KEY`: A secret key for signing JWTs.
- `JWT_ALGORITHM`: The algorithm used for JWT encoding (e.g., "HS256").
- `ACCESS_TOKEN_EXPIRE_MINUTES`: The number of minutes after which an access token expires.

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Authentication (`/auth`)

- **POST `/admin/register`**: Creates a new admin user.
  - **Request Body**: `UserCreate` schema (`email`, `password`).
  - **Response**: `User` schema.

- **POST `/{bot_id}/register`**: Registers a new user for a specific bot.
  - **Path Parameter**: `bot_id` (UUID).
  - **Request Body**: `UserCreate` schema (`email`, `password`).
  - **Response**: `User` schema.

- **POST `/admin/login`**: Authenticates an admin user.
  - **Request Body**: OAuth2PasswordRequestForm (`username`, `password`).
  - **Response**: `Token` schema (`access_token`, `token_type`).

- **POST `/{bot_id}/login`**: Authenticates a user for a specific bot.
  - **Path Parameter**: `bot_id` (UUID).
  - **Request Body**: OAuth2PasswordRequestForm (`username`, `password`).
  - **Response**: `Token` schema (`access_token`, `token_type`).

### Admin (`/admin`)

- **GET `/bots/{bot_id}/summaries`**: Retrieves all chat summaries for a specific bot.
  - **Path Parameter**: `bot_id` (UUID).
  - **Response**: A list of `UserChatSummary` objects.

- **POST `/bots/{bot_id}/process-summaries`**: Processes new chat sessions to generate and store summaries.
  - **Path Parameter**: `bot_id` (UUID).
  - **Response**: A message indicating the number of processed summaries.

- **GET `/bots/{bot_id}/analytics`**: Generates an analytics report for a specific bot based on its chat summaries.
  - **Path Parameter**: `bot_id` (UUID).
  - **Response**: `AnalyticsReport` schema.

### Bots (`/bots`)

- **POST `/`**: Creates a new bot.
  - **Form Data**: `name` (string).
  - **File Upload**: `file` (a `.json` or `.csv` file containing FAQs).
  - **Response**: `Bot` schema.

- **GET `/`**: Retrieves all bots owned by the current admin user.
  - **Response**: A list of `Bot` objects.

### Chat (`/chat`)

- **GET `/{bot_id}/sessions`**: Retrieves all chat sessions for the current user and a specific bot.
  - **Path Parameter**: `bot_id` (UUID).
  - **Response**: A list of `ChatSession` objects.

- **GET `/summary/{session_id}`**: Generates a summary of a specific chat session for the user.
  - **Path Parameter**: `session_id` (string).
  - **Response**: `UserChatSummary` schema.

- **GET `/history/{session_id}`**: Retrieves the full chat history for a specific session.
  - **Path Parameter**: `session_id` (string).
  - **Response**: A list of `ChatMessage` objects.

- **POST `/{bot_id}`**: Sends a message to a bot and gets a response.
  - **Path Parameter**: `bot_id` (UUID).
  - **Request Body**: `ChatRequest` schema (`message`, `session_id`).
  - **Response**: `ChatResponse` schema (`response`, `suggested_actions`).

## LLM Usage and Prompts

The LLM is integral to the bot's functionality. It is used in the following ways:

- **Generating Responses**: The core of the chat functionality. The LLM takes the user's query, the conversation history, and relevant FAQs to generate a helpful and context-aware response. If no relevant FAQs are found, it attempts to answer based on its general knowledge, and if it cannot, it will simulate an escalation.
- **Summarizing Conversations**: For both users and administrators, the LLM can summarize a chat session. This is useful for quickly understanding the context of a long conversation.
- **Generating Analytics**: For administrators, the LLM analyzes all the chat summaries for a bot and generates a high-level analytics report, identifying key themes, common issues, and user sentiment.
- **Suggesting Next Actions**: After providing a response, the LLM suggests a few potential next questions or actions the user might want to take, improving the user experience.
