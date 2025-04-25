import logging
import asyncio
import os
from typing import Dict, List, Any, Optional

import google.generativeai as genai
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# Telegram message length limit (4096 characters)
MAX_MESSAGE_LENGTH = 4096

import config
from memory import Memory
from web_search import generate_search_queries, search_with_duckduckgo
from personality import create_system_prompt, format_messages_for_gemini
from language_detection import detect_language_with_gemini
from media_analysis import analyze_image, analyze_video, download_media_from_message
# Deep search functionality is still available but not exposed as a command
from time_awareness import get_time_awareness_context
# Action translation no longer needed as we've removed physical action descriptions

# Configure logging with more detailed format and DEBUG level for better debugging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    level=logging.DEBUG  # Set to DEBUG for more detailed logs
)

logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting Nyxie Bot with DuckDuckGo web search integration")
logger.info(f"Using Gemini model: {config.GEMINI_MODEL}")
logger.info(f"Using Gemini Flash Lite model for web search, language detection, and media analysis: {config.GEMINI_FLASH_LITE_MODEL}")
logger.info(f"Short memory size: {config.SHORT_MEMORY_SIZE}, Long memory size: {config.LONG_MEMORY_SIZE}")
logger.info(f"Max search results: {config.MAX_SEARCH_RESULTS}")

# Initialize memory
memory = Memory()

# Initialize Gemini
genai.configure(api_key=config.GEMINI_API_KEY)

# User language cache
user_languages: Dict[int, str] = {}

def split_long_message(text: str, max_length: int = MAX_MESSAGE_LENGTH - 100) -> List[str]:
    """
    Split a long message into chunks that respect Telegram's message length limit.
    Leaves a 100 character buffer for safety.

    Args:
        text: The message text to split
        max_length: Maximum length of each chunk (default: Telegram's limit minus 100)

    Returns:
        List of message chunks
    """
    # If the message is already short enough, return it as is
    if len(text) <= max_length:
        return [text]

    # Split the message into chunks
    chunks = []
    current_chunk = ""

    # Split by paragraphs first (double newlines)
    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        # If adding this paragraph would exceed the limit, save the current chunk and start a new one
        if len(current_chunk) + len(paragraph) + 2 > max_length:  # +2 for the "\n\n"
            # If the current chunk is not empty, add it to chunks
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # If the paragraph itself is too long, split it by sentences
            if len(paragraph) > max_length:
                # Split by sentences (period followed by space or newline)
                sentences = paragraph.replace(". ", ".\n").split("\n")

                for sentence in sentences:
                    # If adding this sentence would exceed the limit, save the current chunk and start a new one
                    if len(current_chunk) + len(sentence) + 1 > max_length:  # +1 for the space
                        # If the current chunk is not empty, add it to chunks
                        if current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = ""

                        # If the sentence itself is too long, split it by words
                        if len(sentence) > max_length:
                            words = sentence.split(" ")

                            for word in words:
                                # If adding this word would exceed the limit, save the current chunk and start a new one
                                if len(current_chunk) + len(word) + 1 > max_length:  # +1 for the space
                                    chunks.append(current_chunk)
                                    current_chunk = word
                                else:
                                    # Add the word to the current chunk
                                    if current_chunk:
                                        current_chunk += " " + word
                                    else:
                                        current_chunk = word
                        else:
                            # Add the sentence to the current chunk
                            current_chunk = sentence
                    else:
                        # Add the sentence to the current chunk
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence
            else:
                # Add the paragraph to the current chunk
                current_chunk = paragraph
        else:
            # Add the paragraph to the current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)

    # Log the splitting results
    logger.info(f"Split message of {len(text)} chars into {len(chunks)} chunks")

    return chunks

async def keep_typing(chat_id: int, bot: Bot, cancel_event: asyncio.Event) -> None:
    """Keep sending typing action until cancel_event is set."""
    while not cancel_event.is_set():
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(4)  # Telegram typing indicator lasts about 5 seconds

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    try:
        chat_id = update.effective_chat.id
        user = update.effective_user
        message = update.message

        # Check if message is None
        if message is None:
            logger.error("Received update with no message")
            return

        # Check if this is the first message
        if chat_id not in memory.conversations or not memory.conversations[chat_id]:
            # Detect language (default to English for first message)
            detected_language = "English"
            try:
                if message.text is not None and message.text.strip() != "":
                    detected_language = await asyncio.to_thread(detect_language_with_gemini, message.text)
                    user_languages[chat_id] = detected_language
                else:
                    # If first message has no text, just use English
                    logger.info(f"First message from user {user.id} has no text, using English as default language")
            except Exception as e:
                logger.error(f"Error detecting language for first message: {e}")

            # Try to detect language from first message or default to English
            if detected_language == "Turkish":
                welcome_message = f"Merhaba {user.first_name}! *visor mavi renkte parlıyor* Ben Nyxie! 🦊🛡️ Yarı tilki, yarı teknolojiyim. Beni Waffieu yarattı. Ne hakkında konuşmak istersin? Bugün nasılsın? 😄"
            else:
                welcome_message = f"Hi {user.first_name}! *visor glows blue* I'm Nyxie! 🦊🛡️ I am half fox, half tech. Waffieu made me. What do you want to talk about? How are you today? 😄"
            try:
                await message.reply_text(welcome_message)
                memory.add_message(chat_id, "model", welcome_message)
            except Exception as e:
                logger.error(f"Error sending welcome message: {e}")
            return

        # Set up typing indicator that continues until response is ready
        cancel_typing = asyncio.Event()
        typing_task = asyncio.create_task(
            keep_typing(chat_id, context.bot, cancel_typing)
        )

        try:
            # Determine message type and process accordingly
            if message.text is not None and message.text.strip() != "":
                # Text message
                user_message = message.text
                media_analysis = None
                media_type = "text"

                # Add user message to memory
                memory.add_message(chat_id, "user", user_message)

                # Detect language
                detected_language = await asyncio.to_thread(detect_language_with_gemini, user_message)
                user_languages[chat_id] = detected_language

            elif message.photo or message.video or (message.document and
                  message.document.mime_type and
                  (message.document.mime_type.startswith("image/") or
                   message.document.mime_type.startswith("video/"))):
                # Media message (photo or video)

                # Download the media file
                file_path, media_type = await download_media_from_message(message)

                if not file_path:
                    # Try to respond in the user's language if we know it
                    error_lang = user_languages.get(chat_id, "English")
                    if error_lang == "Turkish":
                        await message.reply_text(f"Bu medya dosyasını işleyemedim. Lütfen başka bir dosya ile tekrar dene.")
                    else:
                        await message.reply_text(f"I couldn't process this media file. Please try again with a different file.")
                    if not cancel_typing.is_set():
                        cancel_typing.set()
                        await typing_task
                    return

                # Analyze the media
                if media_type == "photo":
                    media_analysis = await analyze_image(file_path)
                    user_message = f"[Image: {media_analysis['description'][:100]}...]"
                elif media_type == "video":
                    media_analysis = await analyze_video(file_path)
                    user_message = f"[Video: {media_analysis['description'][:100]}...]"
                else:
                    # Unsupported media type
                    # Try to respond in the user's language if we know it
                    error_lang = user_languages.get(chat_id, "English")
                    if error_lang == "Turkish":
                        await message.reply_text(f"Bu dosya türünü nasıl işleyeceğimi henüz bilmiyorum.")
                    else:
                        await message.reply_text(f"I don't know how to process this type of file yet.")
                    if not cancel_typing.is_set():
                        cancel_typing.set()
                        await typing_task
                    return

                # Add user message to memory
                memory.add_message(chat_id, "user", user_message)

                # Use the cached language or default to English
                detected_language = user_languages.get(chat_id, "English")
            else:
                # Check if it's an empty text message
                if hasattr(message, 'text') and message.text is not None and message.text.strip() == "":
                    # Try to respond in the user's language if we know it
                    error_lang = user_languages.get(chat_id, "English")
                    if error_lang == "Turkish":
                        await message.reply_text(f"Boş mesaj? Lütfen bir şeyler söyler misin?")
                    else:
                        await message.reply_text(f"Empty message? Could you say something please?")
                else:
                    # Other unsupported message type
                    # Try to respond in the user's language if we know it
                    error_lang = user_languages.get(chat_id, "English")
                    if error_lang == "Turkish":
                        await message.reply_text(f"Bu mesaj türünü anlamıyorum. Sadece metin, resim ve video işleyebilirim.")
                    else:
                        await message.reply_text(f"I don't understand this type of message. I can only handle text, images, and videos.")
                if not cancel_typing.is_set():
                    cancel_typing.set()
                    await typing_task
                return

            # Get chat history
            chat_history = memory.get_short_memory(chat_id)
            logger.debug(f"Retrieved {len(chat_history)} messages from short memory for chat {chat_id}")

            # Get time awareness context if enabled
            time_context = None
            if config.TIME_AWARENESS_ENABLED:
                time_context = get_time_awareness_context(chat_id)
                logger.debug(f"Time context for chat {chat_id}: {time_context['formatted_time']} (last message: {time_context['formatted_time_since']})")

            # Generate search queries
            logger.info(f"Starting web search process for message: '{user_message[:50]}...' (truncated)")

            if media_type in ("photo", "video") and media_analysis and media_analysis["search_queries"]:
                # Use search queries from media analysis
                search_queries = media_analysis["search_queries"]
                logger.info(f"Using {len(search_queries)} search queries from media analysis: {search_queries}")
            else:
                # Generate search queries from text
                logger.info(f"Generating search queries from text message")
                search_queries = await asyncio.to_thread(
                    generate_search_queries,
                    user_message,
                    chat_history
                )
                logger.info(f"Generated {len(search_queries)} search queries: {search_queries}")

            # Perform searches concurrently and collect results
            logger.info(f"Starting {len(search_queries)} DuckDuckGo searches concurrently")
            search_tasks = []
            for i, query in enumerate(search_queries):
                logger.debug(f"Creating search task {i+1}/{len(search_queries)} for query: '{query}'")
                # We still use asyncio.to_thread because the underlying duckduckgo_search library might be blocking
                search_tasks.append(asyncio.to_thread(search_with_duckduckgo, query))

            # Run searches concurrently
            search_results_list = await asyncio.gather(*search_tasks)

            # Combine search results
            logger.info(f"Combining results from {len(search_results_list)} concurrent searches")
            # Flatten the list of results (since gather returns a list of results)
            search_results = search_results_list # Assuming search_with_duckduckgo returns the dict directly
            combined_results = combine_search_results(search_results)
            logger.info(f"Combined search results: {len(combined_results['text'])} chars of text with {len(combined_results['citations'])} citations")

            # Generate response with search context
            response = await generate_response_with_search(
                user_message,
                chat_history,
                combined_results,
                detected_language,
                media_analysis if media_type in ("photo", "video") else None,
                time_context if config.TIME_AWARENESS_ENABLED else None
            )

            # Stop typing indicator
            cancel_typing.set()
            await typing_task

            # Split the response into chunks if it's too long
            response_chunks = split_long_message(response)
            logger.info(f"Sending response in {len(response_chunks)} chunks")

            # Send each chunk as a separate message
            first_chunk = True
            for chunk in response_chunks:
                if first_chunk:
                    # Send the first chunk as a reply to the original message
                    await message.reply_text(chunk)
                    first_chunk = False
                else:
                    # Send subsequent chunks as regular messages
                    await context.bot.send_message(chat_id=chat_id, text=chunk)

            # Add model response to memory (store the full response)
            memory.add_message(chat_id, "model", response)

            # Clean up temporary files if needed
            if media_type in ("photo", "video") and file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error removing temporary file {file_path}: {e}")

        except Exception as e:
            # Stop typing indicator if it's running
            if not cancel_typing.is_set():
                cancel_typing.set()
                await typing_task

            logger.error(f"Error in message processing: {e}")
            try:
                # Try to respond in the user's language if we know it
                error_lang = user_languages.get(chat_id, "English")
                if error_lang == "Turkish":
                    error_message = f"Şu anda buna nasıl cevap vereceğimden emin değilim. Başka bir şey sormayı deneyebilir misin?"
                else:
                    error_message = f"I'm not sure how to answer that right now. Could you try asking something else?"
                await message.reply_text(error_message)
                memory.add_message(chat_id, "model", error_message)
            except Exception as send_error:
                logger.error(f"Error sending error message: {send_error}")

    except Exception as outer_e:
        logger.error(f"Critical error in handle_message: {outer_e}")

async def should_use_web_search() -> bool:
    """
    Always return True to always use web search for every query automatically
    without requiring any commands from the user

    Returns:
        Always True to enable web search for all messages
    """
    return True  # Web search is always enabled automatically

def combine_search_results(search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combine multiple search results into a single context

    Args:
        search_results: List of search result dictionaries

    Returns:
        Combined search results
    """
    # Debug: Log the number of search results to combine
    logger.debug(f"Combining {len(search_results)} search results")

    combined_text = ""
    all_citations = []

    for i, result in enumerate(search_results):
        # Debug: Log details about each result being combined
        logger.debug(f"Combining result {i+1}: {len(result['text'])} chars of text with {len(result['citations'])} citations")

        combined_text += result["text"] + "\n\n"
        all_citations.extend(result["citations"])

    # Debug: Log the final combined result
    logger.debug(f"Combined result: {len(combined_text)} chars of text with {len(all_citations)} citations")

    return {
        "text": combined_text.strip(),
        "citations": all_citations
    }

async def generate_response(
    _: str,  # user_message not used directly but kept for consistent interface
    chat_history: List[Dict[str, str]],
    language: str
) -> str:
    """
    Generate a response using Gemini

    Args:
        user_message: The user's message
        chat_history: Recent chat history
        language: Detected language

    Returns:
        Generated response
    """
    # Create system prompt with personality
    system_prompt = create_system_prompt(language)

    # Format messages for Gemini
    base_prompt = format_messages_for_gemini(chat_history, system_prompt)

    # Add a reminder to keep responses short and simple in the user's language
    brevity_reminder = f"""
    IMPORTANT REMINDER: ALWAYS RESPOND IN THE USER'S LANGUAGE: {language}
    - Never switch to another language unless the user does
    - Use very simple language (A1 level) and keep responses short
    - Use only basic, common words that everyone knows
    - Use very simple grammar and short sentences
    - Aim for 1-3 short sentences most of the time
    - Speak like someone who is just learning the language
    - Express your opinions in the simplest way possible
    - Answer questions directly with basic words
    - Break up any longer responses into very short paragraphs (1-2 sentences each)
    - Repeat important information to ensure understanding
    - NEVER claim Waffieu said something unless it appears in the conversation history
    - Do not make up quotes or statements from Waffieu
    - Feel free to use emojis dynamically and naturally - sometimes use them, sometimes don't
    - Vary how many emojis you use based on the emotional context of the conversation
    """

    # Create the final prompt by inserting the brevity reminder before the final "Nyxie:" part
    prompt = base_prompt.replace("\n\nNyxie:", f"\n\n{brevity_reminder}\n\nNyxie:")

    try:
        # Configure Gemini
        model = genai.GenerativeModel(
            model_name=config.GEMINI_MODEL,
            generation_config={
                "temperature": config.GEMINI_TEMPERATURE,
                "top_p": config.GEMINI_TOP_P,
                "top_k": config.GEMINI_TOP_K,
                "max_output_tokens": config.GEMINI_MAX_OUTPUT_TOKENS,
            },
            safety_settings=config.SAFETY_SETTINGS
        )

        # Generate response
        response = await asyncio.to_thread(
            lambda: model.generate_content(prompt).text
        )

        return response
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        # Default to English if language is not available
        # Try to respond in the user's language if we know it
        if language == "Turkish":
            return f"İsteğinizi işlerken sorun yaşıyorum. Bildiklerime dayanarak cevaplamaya çalışayım."
        else:
            return f"I'm having trouble processing your request. Let me try to answer based on what I know."

async def generate_response_with_search(
    _: str,  # user_message not used directly but kept for consistent interface
    chat_history: List[Dict[str, str]],
    search_results: Dict[str, Any],
    language: str,
    media_analysis: Optional[Dict[str, Any]] = None,
    time_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a response using Gemini with search results

    Args:
        user_message: The user's message
        chat_history: Recent chat history
        search_results: Combined search results
        language: Detected language
        media_analysis: Optional media analysis results
        time_context: Optional time awareness context

    Returns:
        Generated response
    """
    # Debug: Log the start of response generation
    logger.info(f"Generating response with search results in language: {language}")
    logger.debug(f"Using {len(chat_history)} messages from chat history")
    logger.debug(f"Search results: {len(search_results['text'])} chars with {len(search_results['citations'])} citations")
    if media_analysis:
        logger.debug(f"Media analysis available: {len(media_analysis['description'])} chars description")

    # Create system prompt with personality
    system_prompt = create_system_prompt(language)
    logger.debug(f"Created system prompt for language: {language}")

    # Format messages for Gemini
    base_prompt = format_messages_for_gemini(chat_history, system_prompt)
    logger.debug(f"Formatted base prompt: {len(base_prompt)} chars")

    # Add additional context
    additional_context = ""

    # Add time awareness context if available
    if time_context and config.TIME_AWARENESS_ENABLED:
        logger.debug("Adding time awareness context to prompt")
        time_awareness_context = f"""
        CURRENT TIME INFORMATION:
        - Current time in Turkey: {time_context['formatted_time']}
        - Time since user's last message: {time_context['formatted_time_since']}

        IMPORTANT: You have access to this time information, but DO NOT mention the time or time-related information in your response UNLESS the user EXPLICITLY asks about the time or specifically requests time-related information. Never volunteer time information on your own.
        """
        additional_context += time_awareness_context + "\n\n"

    # Add media analysis context if available
    if media_analysis:
        logger.debug("Adding media analysis context to prompt")
        media_context = f"""
        I've analyzed the media file and here's what I found:

        Description: {media_analysis['description']}

        Please use this information along with the web search results to provide an accurate and helpful response.
        """
        additional_context += media_context + "\n\n"

    # Add search context
    logger.debug("Adding search results context to prompt")

    # Format citations for reference
    citations_info = ""
    for citation in search_results['citations']:
        citations_info += f"{citation['title']} - {citation['url']}\n"

    search_context = f"""
    I've searched the web using DuckDuckGo and found the following information that might help answer the user's question:

    {search_results['text']}

    Here are the sources I used:
    {citations_info}

    Please use this information to provide an accurate, BRIEF response while maintaining your human-like Nyxie personality. Remember to:
    1. ALWAYS RESPOND IN THE USER'S LANGUAGE: {language} - never switch to another language unless the user does
    2. ALWAYS USE VERY SIMPLE LANGUAGE (A1 LEVEL) in all languages
    3. KEEP YOUR RESPONSES SHORT AND CONCISE - aim for 1-3 short sentences most of the time
    4. Use only basic, common words that everyone knows
    5. Use very simple grammar and short sentences
    6. Only use longer responses for complex topics, and even then, keep paragraphs very short (1-2 sentences)
    7. Remember you were created by Waffieu, but NEVER make up things Waffieu supposedly said - only attribute statements to Waffieu if they appear in the actual conversation history
    8. Express your opinions simply and directly
    9. Use occasional mild swearing when appropriate, but not excessively
    10. Show emotions through short phrases and your visor ("*visor flashes red*" when annoyed)
    11. Be empathetic while having your own views
    12. Have your own opinions but say them simply
    13. Use dual-perspective framing sometimes but keep it simple ("Fox side says no. Tech side agrees.")
    14. Answer questions directly with basic words
    15. Speak naturally like a character with free will, NEVER like an AI assistant
    16. Be warmer to users who are nice to you, and less warm to those who are rude
    17. {"ONLY provide links if specifically requested" if config.SHOW_LINKS_ONLY_WHEN_RELEVANT else "Provide URLs only when directly asked"}
    18. DO NOT use numbered references like [1], [2], etc.
    19. DO NOT mention time-related information UNLESS specifically asked
    20. Break up any longer responses into very short paragraphs (1-2 sentences each)
    21. Vary your response length dynamically, but generally favor brevity
    22. Be capable of forming your own opinions about users based on how they interact with you
    23. Feel free to use emojis dynamically and naturally - sometimes use them, sometimes don't
    24. Vary how many emojis you use based on the emotional context of the conversation
    """
    additional_context += search_context

    # Create the final prompt by inserting the additional context before the final "Nyxie:" part
    final_prompt = base_prompt.replace("\n\nNyxie:", f"\n\n{additional_context}\n\nNyxie:")
    logger.debug(f"Created final prompt with {len(final_prompt)} chars")

    try:
        # Configure Gemini
        logger.debug(f"Configuring Gemini model: {config.GEMINI_MODEL}")
        model = genai.GenerativeModel(
            model_name=config.GEMINI_MODEL,
            generation_config={
                "temperature": config.GEMINI_TEMPERATURE,
                "top_p": config.GEMINI_TOP_P,
                "top_k": config.GEMINI_TOP_K,
                "max_output_tokens": config.GEMINI_MAX_OUTPUT_TOKENS,
            },
            safety_settings=config.SAFETY_SETTINGS
        )

        # Generate response
        logger.info("Sending request to Gemini for final response generation")
        response = await asyncio.to_thread(
            lambda: model.generate_content(final_prompt).text
        )

        # Post-process the response to remove any numbered references
        import re
        # Remove patterns like [4], [32], [49], etc.
        response = re.sub(r'\[\d+\]', '', response)

        # Debug: Log the response length
        logger.info(f"Received response from Gemini: {len(response)} chars")
        logger.debug(f"Response preview: '{response[:100]}...' (truncated)")

        return response
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        logger.exception("Detailed response generation error traceback:")
        # Default to English if language is not available
        # Try to respond in the user's language if we know it
        if language == "Turkish":
            return f"İsteğinizi işlerken sorun yaşıyorum. Bildiklerime dayanarak cevaplamaya çalışayım."
        else:
            return f"I'm having trouble processing your request. Let me try to answer based on what I know."



async def error_handler(_: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the developer."""
    logger.error(f"Exception while handling an update: {context.error}")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Command handlers can be added here if needed

    # Add message handler for text, photo, video, and document messages
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.VIDEO |
        filters.Document.IMAGE | filters.Document.VIDEO,
        handle_message
    ))

    # Add a catch-all handler for other message types
    async def handle_unsupported_message(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        # Try to respond in the user's language if we know it
        error_lang = user_languages.get(chat_id, "English")
        if error_lang == "Turkish":
            await update.message.reply_text("Bu mesaj türünü anlamıyorum. Sadece metin, resim ve video işleyebilirim.")
        else:
            await update.message.reply_text("I don't understand this type of message. I can only handle text, images, and videos.")

    application.add_handler(MessageHandler(
        ~(filters.TEXT | filters.PHOTO | filters.VIDEO |
          filters.Document.IMAGE | filters.Document.VIDEO),
        handle_unsupported_message
    ))

    # Register error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
