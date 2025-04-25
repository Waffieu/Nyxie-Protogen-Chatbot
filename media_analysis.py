import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import tempfile

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from telegram import Update, Message

import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Gemini
genai.configure(api_key=config.GEMINI_API_KEY)

async def analyze_image(image_path: str) -> Dict[str, Any]:
    """
    Analyze an image using Gemini Vision capabilities

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary containing analysis results
    """
    try:
        # Configure Gemini model
        model = genai.GenerativeModel(
            model_name=config.GEMINI_FLASH_LITE_MODEL,
            generation_config={
                "temperature": config.GEMINI_FLASH_LITE_TEMPERATURE,
                "top_p": config.GEMINI_FLASH_LITE_TOP_P,
                "top_k": config.GEMINI_FLASH_LITE_TOP_K,
                "max_output_tokens": config.GEMINI_FLASH_LITE_MAX_OUTPUT_TOKENS,
            },
            safety_settings=config.SAFETY_SETTINGS
        )

        # Read the image file
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        # Generate image description
        prompt = "Describe this image in detail. Include all important elements, objects, people, text, and context."
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_data}])

        # Generate search queries based on the image
        search_prompt = """
        Based on this image, generate 3 effective search queries that would help find relevant information.
        Make the queries specific, focused, and likely to return useful information.
        Return only the queries, one per line, without numbering or additional text.
        """
        search_response = model.generate_content([search_prompt, {"mime_type": "image/jpeg", "data": image_data}])

        # Parse search queries
        search_queries = [q.strip() for q in search_response.text.strip().split('\n') if q.strip()]

        return {
            "description": response.text,
            "search_queries": search_queries[:3]  # Limit to 3 queries
        }
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return {
            "description": "I couldn't analyze this image properly.",
            "search_queries": ["image analysis error"]
        }

async def analyze_video(video_path: str) -> Dict[str, Any]:
    """
    Analyze a video using Gemini Vision capabilities

    Args:
        video_path: Path to the video file

    Returns:
        Dictionary containing analysis results
    """
    try:
        # Extract frames from the video (simplified approach - just analyze first frame)
        # In a production environment, you would extract multiple frames and analyze them

        # Configure Gemini model
        model = genai.GenerativeModel(
            model_name=config.GEMINI_FLASH_LITE_MODEL,
            generation_config={
                "temperature": config.GEMINI_FLASH_LITE_TEMPERATURE,
                "top_p": config.GEMINI_FLASH_LITE_TOP_P,
                "top_k": config.GEMINI_FLASH_LITE_TOP_K,
                "max_output_tokens": config.GEMINI_FLASH_LITE_MAX_OUTPUT_TOKENS,
            },
            safety_settings=config.SAFETY_SETTINGS
        )

        # Read the video file (first frame only for simplicity)
        with open(video_path, "rb") as video_file:
            video_data = video_file.read()

        # Generate video description
        prompt = "This is a video. Describe what you can see in this video frame. Include all important elements, objects, people, text, and context."
        response = model.generate_content([prompt, {"mime_type": "video/mp4", "data": video_data}])

        # Generate search queries based on the video
        search_prompt = """
        Based on this video frame, generate 3 effective search queries that would help find relevant information.
        Make the queries specific, focused, and likely to return useful information.
        Return only the queries, one per line, without numbering or additional text.
        """
        search_response = model.generate_content([search_prompt, {"mime_type": "video/mp4", "data": video_data}])

        # Parse search queries
        search_queries = [q.strip() for q in search_response.text.strip().split('\n') if q.strip()]

        return {
            "description": response.text,
            "search_queries": search_queries[:3]  # Limit to 3 queries
        }
    except Exception as e:
        logger.error(f"Error analyzing video: {e}")
        return {
            "description": "I couldn't analyze this video properly.",
            "search_queries": ["video analysis error"]
        }

async def download_media_from_message(message: Message) -> Tuple[Optional[str], str]:
    """
    Download media (photo or video) from a Telegram message

    Args:
        message: Telegram message containing media

    Returns:
        Tuple of (file_path, media_type)
    """
    try:
        # Create a temporary directory to store the file
        temp_dir = tempfile.mkdtemp()

        if message.photo:
            # Get the largest photo (best quality)
            photo = message.photo[-1]
            file = await photo.get_file()
            file_path = os.path.join(temp_dir, f"{file.file_id}.jpg")
            await file.download_to_drive(file_path)
            return file_path, "photo"

        elif message.video:
            video = message.video
            file = await video.get_file()
            file_path = os.path.join(temp_dir, f"{file.file_id}.mp4")
            await file.download_to_drive(file_path)
            return file_path, "video"

        elif message.document:
            # Check if document is an image or video
            mime_type = message.document.mime_type
            if mime_type and (mime_type.startswith("image/") or mime_type.startswith("video/")):
                file = await message.document.get_file()
                extension = mime_type.split("/")[1]
                file_path = os.path.join(temp_dir, f"{file.file_id}.{extension}")
                await file.download_to_drive(file_path)

                media_type = "photo" if mime_type.startswith("image/") else "video"
                return file_path, media_type

        return None, "unknown"
    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        return None, "error"
