from langdetect import detect
import google.generativeai as genai
import config
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Gemini
genai.configure(api_key=config.GEMINI_API_KEY)

def detect_language(text: str) -> str:
    """
    Detect the language of the input text

    Args:
        text: The text to detect language from

    Returns:
        Language code or 'English' if detection fails
    """
    try:
        # Use langdetect for initial detection
        lang_code = detect(text)

        # Map language codes to full language names
        language_map = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh-cn': 'Chinese',
            'zh-tw': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'tr': 'Turkish',
            # Add more languages as needed
        }

        return language_map.get(lang_code, 'English')
    except:
        # Default to English if detection fails
        return 'English'

def detect_language_with_gemini(text: str, is_search_query: bool = False) -> str:
    """
    Use Gemini to detect language more accurately

    Args:
        text: The text to detect language from

    Returns:
        Full language name
    """
    try:
        # Create a prompt to detect language
        if is_search_query:
            prompt = f"""
            Detect the language of the following search query and respond with ONLY the full language name (e.g., "English", "Spanish", "Japanese", etc.):

            "{text}"

            Note that search queries may contain terms in multiple languages or proper nouns.
            Focus on the structure and common words to determine the primary language.
            If the query is too short or ambiguous, prefer to classify it as "English" unless it's clearly in another language.

            Respond with ONLY the language name, nothing else.
            """
        else:
            prompt = f"""
            Detect the language of the following text and respond with ONLY the full language name (e.g., "English", "Spanish", "Japanese", etc.):

            "{text}"

            Respond with ONLY the language name, nothing else.
            """

        # Generate language detection
        model = genai.GenerativeModel(
            model_name=config.GEMINI_FLASH_LITE_MODEL,
            generation_config={
                "temperature": 0.1,
                "top_p": config.GEMINI_FLASH_LITE_TOP_P,
                "top_k": config.GEMINI_FLASH_LITE_TOP_K,
                "max_output_tokens": 10,
            }
        )

        response = model.generate_content(prompt)

        # Return the detected language
        detected_language = response.text.strip()

        # Fallback to basic detection if Gemini gives a complex response
        if len(detected_language.split()) > 2:
            return detect_language(text)

        return detected_language
    except Exception as e:
        logger.error(f"Error detecting language with Gemini: {e}")
        return detect_language(text)  # Fallback to basic detection
