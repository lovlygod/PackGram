# Telegram Media Forward Bot

This bot forwards media from Telegram channels and posts to users with a watermark. It supports both single media and media groups (albums).

## Features

- Forward media from public and private Telegram channels
- Support for photos, videos, documents, audio, and voice messages
- Automatic watermark attachment to media content
- Support for media groups (albums)
- Support for new Telegram post link formats (t.me/username/s/message_id)

## Prerequisites

- Python 3.8 or higher
- Telegram API ID and API Hash (get from https://my.telegram.org)
- Bot Token (get from @BotFather on Telegram)

## Installation

1. Clone the repository or download the files
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the `.env.example` with your credentials:
   ```
   API_ID=your_api_id_here
   API_HASH=your_api_hash_here
   BOT_TOKEN=your_bot_token_here
   SESSION_NAME=user_session_new
   MEDIA_DIR=cache_media
   ```

## Configuration

### Environment Variables

- `API_ID`: Your Telegram API ID
- `API_HASH`: Your Telegram API Hash
- `BOT_TOKEN`: Your Telegram Bot Token
- `SESSION_NAME`: Name for the session file (default: user_session_new)
- `MEDIA_DIR`: Directory for cached media (default: cache_media)

## Setup

1. Run the bot for the first time to create a session:
   ```
   python bot.py
   ```

2. Enter your phone number when prompted
3. Enter the code sent to your Telegram account
4. If you have 2FA enabled, enter your 2FA password

After the initial setup, a session file will be created and you won't need to authenticate again.

## Usage

1. Add your bot to Telegram
2. Send a link to a Telegram post (e.g., https://t.me/channel_name/post_number or https://t.me/channel_name/s/message_id)
3. The bot will download and forward all media with a watermark

## Deployment Options

### Local Deployment

Run the bot locally:
```
python bot.py
```

### Railway Deployment

1. Connect your GitHub repository to Railway
2. Add the required environment variables in Railway dashboard
3. Add a Procfile with content: `worker: python bot.py`
4. Deploy

### Other Platforms

For platforms like Heroku, PythonAnywhere, or Replit:
1. Upload the code
2. Set environment variables
3. Ensure the session file is persisted between restarts
4. Run `python bot.py`

## Security Notes

- Never commit your `.env` file to version control
- Store your session files securely
- Keep your API credentials secure
- The session file contains authentication data - protect it from unauthorized access

## Troubleshooting

### Common Issues

- **Session file locked**: Wait for other processes to finish or rename SESSION_NAME
- **Authentication required**: Run the bot locally first to create a session
- **Media download fails**: Check permissions and internet connection
- **Links not recognized**: Ensure the link format is correct

### Environment Variables Not Loading

If environment variables are not loading, ensure:
- `.env` file is in the same directory as `bot.py`
- Correct variable names in `.env` file
- `python-dotenv` package is installed

## Dependencies

- python-telegram-bot
- aiogram
- Telethon
- python-dotenv
- pillow

## License

This project is open-source and available under the MIT License.