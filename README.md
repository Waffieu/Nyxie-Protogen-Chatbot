# Nyxie Telegram Bot

A Telegram chatbot featuring Nyxie, a protogen-fox hybrid character, powered by Google's Gemini AI models.

## Features

- **Nyxie Personality**: The bot embodies Nyxie, a protogen-fox hybrid with a unique personality - playful, thoughtful, with both emotional fox instincts and logical tech capabilities. Nyxie has her own opinions and can express them freely.
- **Typing Indicator**: Shows typing animation while generating responses
- **Web Search Capabilities**:
  - **Automatic Web Search**: Automatically searches the web for every query to provide accurate information
- **Advanced Media Analysis**:
  - Uses gemini-2.5-flash-preview-04-17 model for image and video analysis
  - Provides detailed descriptions of images and videos
  - Generates relevant search queries based on media content

- **Persistent Memory System**:
  - Short-term memory (25 messages) for immediate context
  - Long-term memory (100 messages) for each user
  - Memories persist between bot restarts
  - Each user has their own personalized memory file
- **Time Awareness**:
  - Understands the current time in Turkey
  - Recognizes time of day (morning, afternoon, evening, night)
  - Tracks how long it's been since the user's last message
  - Naturally references time information in conversations
- **Language Adaptation**:
  - Automatically detects and responds in the user's language
  - Uses simple vocabulary and sentence structures (A1 level) in all languages
  - Maintains Nyxie's authentic personality across all languages
  - Never switches languages unless the user does
  - Currently has enhanced support for English and Turkish, with basic support for many other languages
- **Authentic Character Behavior**:
  - Responds like a character with free will rather than an AI assistant
  - Uses natural, dynamic speech that varies appropriately with the conversation
  - Can express opinions and occasionally disagree with users
  - Uses mild swearing when appropriate (but not excessively)
  - Shows complex emotions through text and visor descriptions
- **Dynamic Emoji Usage**:
  - Uses emojis naturally and dynamically like a human would
  - Sometimes uses emojis, sometimes doesn't
  - Varies the number of emojis based on emotional context

## Setup

### Prerequisites

- Python 3.9+
- A Telegram Bot Token (from [BotFather](https://t.me/botfather))
- A Google Gemini API Key (from [Google AI Studio](https://aistudio.google.com/))

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/waffieu/Nyxie-Furry-Chatbot.git
   cd Nyxie-Furry-Chatbot
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the `.env.example` template:
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file with your API keys and configuration:
   ```
   # Telegram Bot Token (get from BotFather)
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

   # Google Gemini API Key
   GEMINI_API_KEY=your_gemini_api_key_here

   # Memory settings
   SHORT_MEMORY_SIZE=25
   LONG_MEMORY_SIZE=100
   MEMORY_DIR=user_memories

   # Web search settings
   MAX_SEARCH_RESULTS=5

   # Maximum number of retries for DuckDuckGo searches
   MAX_SEARCH_RETRIES=5
   ```

### Running the Bot

Run the bot with:
```
python main.py
```

## Usage

Once the bot is running, you can interact with it on Telegram by simply sending messages or using commands.

### Regular Chat

Simply send messages to the bot and it will:

- Automatically respond in your language
- Search the web for relevant information for every query
- Remember your entire conversation history
- Show a typing indicator while generating responses

### Commands

No commands are currently available. Simply chat with the bot normally and it will automatically search the web for information.

## Customization

- Adjust Nyxie's personality in `personality.py`
- Modify memory settings in `.env`
- Configure Gemini model parameters in `config.py`
- Customize language detection in `language_detection.py`
- Edit welcome messages and error responses in `main.py`

## AI Models Used

This bot uses multiple specialized Gemini models for different tasks:

- **Main Conversation**: gemini-2.5-flash-preview-04-17 - Handles the primary conversation with users
- **Image/Video Analysis**: gemini-2.5-flash-preview-04-17 - Processes and describes images and videos
- **Web Search & Language Detection**: gemini-2.0-flash-lite - Handles web search queries and language detection

## Recent Updates

- **Enhanced Image Analysis**: Now using gemini-2.5-flash-preview-04-17 model specifically for image and video analysis
- **Personality Change**: Changed from Puro to Nyxie, a protogen-fox hybrid character
- **Language Improvements**: Enhanced language detection and response in multiple languages
- **Concise Responses**: Updated to provide shorter, more natural responses
- **Emoji Support**: Added dynamic emoji usage based on conversation context
- **Attribution Fix**: Ensured the bot doesn't falsely attribute statements to its creator

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Created by Waffieu
- Powered by Google's Gemini AI
- Built with python-telegram-bot
