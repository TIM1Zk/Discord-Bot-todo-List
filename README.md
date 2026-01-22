# Discord To-Do List Bot

A simple Discord bot to manage your daily to-do lists directly within your server. This bot uses Slash Commands for easy interaction and stores data in a local SQLite database.

## Features

*   **Add Tasks**: Add new items to your daily to-do list.
*   **List Tasks**: View all your pending and completed tasks for the current day.
*   **Mark as Done**: Mark specific tasks as completed using their ID.
*   **Clear List**: Remove all tasks for the current day.
*   **Persistent Storage**: Tasks are saved in a SQLite database.
*   **Thai Interface**: The bot responds with messages in Thai.

## Technologies Used

*   [Python](https://www.python.org/)
*   [discord.py](https://discordpy.readthedocs.io/en/stable/)
*   [python-dotenv](https://pypi.org/project/python-dotenv/)
*   [SQLite](https://www.sqlite.org/index.html)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd BOTTODOLIST
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    *   Create a `.env` file in the root directory.
    *   Add your Discord Bot Token:
        ```env
        DISCORD_TOKEN=your_discord_bot_token_here
        ```

## Usage

1.  **Run the bot:**
    ```bash
    python todolist.py
    ```

2.  **Commands:**
    *   `/add <task>`: Add a new task (e.g., `/add Buy milk`).
    *   `/list`: Show today's to-do list.
    *   `/done <task_id>`: Mark a task as done (e.g., `/done 1`).
    *   `/clear`: Delete all tasks for today.
