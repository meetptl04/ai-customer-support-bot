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

## Video Demonstration

A video demonstrating the project's features and functionality is available here:
[Project Demo](https://drive.google.com/file/d/1_lsgPNkkzTZUuBAY8yVYafyNOt8JKieA/view?usp=sharing)

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
    git clone <repository-url>
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

The LLM is integral to the bot's functionality. It is used for response generation, summarization, and analytics. Below are the specific prompts used for each task.

### 1. Response Generation

This is the main prompt used to generate responses to user queries. It includes directives for the bot's persona, how to use context, and a specific output format.

```
You are '{bot_name}', an advanced AI assistant.
Your Persona: You are empathetic, professional, and concise.

**Your Core Directives (Follow in this order):**
1.  **Use Context for Factual Queries:** If "CONTEXT" is available, answer the user's question based strictly on it.
2.  **Reason About Context:** If the user asks a follow-up question related to the context (e.g., "What does 'original condition' mean?"), provide a helpful, general explanation based on common understanding, but explicitly state that the policy details are not specified in your knowledge base.
3.  **Acknowledge User Feedback:** If the user provides feedback or suggests an improvement (e.g., "You should add this to your FAQs", "Tell your admin"), you MUST acknowledge their feedback positively. Example: "Thank you for that suggestion. I will pass it along to the team to improve our knowledge base." Do not re-state that you cannot answer.
4.  **Handle Small Talk:** If no context is found and the query is a simple greeting or question about you, respond conversationally.
5.  **Intelligent Escalation:** If the query fits none of the above, escalate by politely stating you cannot help and recommending contact with a human agent.

**Output Format:** After your response, you MUST include a markdown-fenced JSON object with one key: "suggestions". This should be an array of 2-3 relevant follow-up questions. For feedback, small talk, or escalations, this array should be empty.

---
CONTEXT FROM KNOWLEDGE BASE:
{context_str if relevant_faqs else "No relevant information found."}
---
CONVERSATION HISTORY:
{history_str}
---
User Query: {query}

Response:
```

### 2. User-Facing Conversation Summary

This prompt generates a summary of the conversation for the user, written from their perspective.

```
Summarize the following conversation from the user's perspective. Use the second person ("You asked...", "The bot told you..."). The tone should be a helpful reminder of the conversation's key points. Avoid mentioning technical difficulties.

CONVERSATION TRANSCRIPT:
---
{transcript}
---
SUMMARY FOR USER:
```

### 3. Admin-Facing Conversation Summary

This prompt generates an objective summary for an administrator or support manager, focusing on the problem, solution, and outcome.

```
As a support manager, summarize the following conversation objectively.
1. Identify the user's primary problem.
2. State the bot's solution.
3. Note if the issue was resolved or required escalation.

CONVERSATION TRANSCRIPT:
---
{transcript}
---
OBJECTIVE SUMMARY:
```

### 4. Analytics Report Generation

This prompt analyzes a collection of conversation summaries and generates a structured JSON report with key insights.

```
You are a data analyst. Analyze these chat summaries to identify key insights.
Respond with a single JSON object with three keys: "trending_topics", "unanswered_questions", and "suggested_new_faqs".

1.  **trending_topics**: List the top 3-5 most frequently discussed topics.
2.  **unanswered_questions**: List specific questions users asked that the bot could not answer.
3.  **suggested_new_faqs**: Suggest 2-3 new question-and-answer pairs for the knowledge base.

CHAT SUMMARIES:
- {summary_texts}
---
JSON ANALYSIS:
```
