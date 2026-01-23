# Discord To-Do List Bot

A simple and efficient Discord bot that helps you manage your daily tasks directly within your Discord server. It supports slash commands, interactive buttons, auto-clears tasks daily, and sends notifications via LINE.

## ✨ Features

- **Add Tasks**: Quickly add new items to your to-do list using slash commands.
- **View List**: Check your pending and completed tasks for the day.
- **Interactive Buttons**: Mark tasks as "Done" with a single click.
- **Daily Reset**: Tasks are tracked based on the date (Thai Timezone). The list resets automatically or can be cleared manually.
- **LINE Notifications**: Receive real-time updates for new tasks and completed items via LINE.
- **Clean UI**: Uses Discord Embeds for a neat and organized display.

## 🛠️ Technologies Used

- **Python 3.8+**
- **discord.py**: For interacting with the Discord API.
- **SQLite**: For local data storage of tasks.
- **pytz**: For timezone handling (Asia/Bangkok).
- **line-bot-sdk**: For LINE Messaging API integration.
- **Discloud**: For cloud hosting and deployment.

## 📋 Prerequisites

Before running the bot, ensure you have:

1.  **Python 3.8** or higher installed.
2.  A **Discord Bot Token**. You can get one from the [Discord Developer Portal](https://discord.com/developers/applications).
3.  A **LINE Messaging API Channel** (Optional, but recommended for notifications).

## ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/TIM1Zk/Discord-Bot-todo-List.git
    cd Discord-Bot-todo-List
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    - Create a `.env` file in the root directory.
    - Add your Discord Bot Token and LINE API credentials to the file:
      ```env
      DISCORD_TOKEN=your_discord_bot_token_here
      LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
      LINE_GROUP_ID=your_line_group_id_here
      ```
    > **Note:** If `.env` is not set, the bot looks for hardcoded tokens in the source code (not recommended for production).

## 🚀 Usage

1.  **Start the bot:**
    ```bash
    python todolist.py
    ```

2.  **Slash Commands:**
    | Command | Description |
    | :--- | :--- |
    | `/add <task>` | Add a new task to your to-do list. |
    | `/list` | Show your current to-do list. |
    | `/clear` | Delete all your tasks for the current day. |


## ☁️ Deployment (Discloud)

This bot includes a `discloud.config` file for easy deployment on [Discloud](https://discloudbot.com/).

1.  **Configure `discloud.config`:**
    - Open the `discloud.config` file.
    - Update the `ID` and `NAME` fields to match your bot's information.

2.  **Upload:**
    - Upload the project files (`todolist.py`, `requirements.txt`, `.env`, `discloud.config`) to Discloud via their dashboard or CLI.
    - Ensure your `.env` variables are correctly set in the Discloud environment or included in the upload (security caution: environment variables are safer set in the dashboard if supported, but uploading `.env` is the direct method).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open-source.

## 👤 Author

Made by **TIM1Zk**
