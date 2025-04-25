import os
import json
import logging
from typing import Dict, List
import config

# Configure logging
logger = logging.getLogger(__name__)

class Memory:
    def __init__(self):
        # Dictionary to store conversations by chat_id
        self.conversations: Dict[int, List[Dict[str, str]]] = {}

        # Create memory directory if it doesn't exist
        os.makedirs(config.MEMORY_DIR, exist_ok=True)

        # Load existing memories
        self._load_all_memories()

    def add_message(self, chat_id: int, role: str, content: str) -> None:
        """
        Add a message to the conversation history for a specific chat

        Args:
            chat_id: The Telegram chat ID
            role: Either 'user' or 'model'
            content: The message content
        """
        if chat_id not in self.conversations:
            self.conversations[chat_id] = []

        self.conversations[chat_id].append({
            "role": role,
            "content": content
        })

        # Trim the conversation if it exceeds the long memory size
        if len(self.conversations[chat_id]) > config.LONG_MEMORY_SIZE:
            self.conversations[chat_id] = self.conversations[chat_id][-config.LONG_MEMORY_SIZE:]

        # Save the updated memory to disk
        self._save_memory(chat_id)

    def get_short_memory(self, chat_id: int) -> List[Dict[str, str]]:
        """
        Get the short-term memory (most recent messages) for a specific chat

        Args:
            chat_id: The Telegram chat ID

        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        if chat_id not in self.conversations:
            return []

        return self.conversations[chat_id][-config.SHORT_MEMORY_SIZE:]

    def get_long_memory(self, chat_id: int) -> List[Dict[str, str]]:
        """
        Get the long-term memory (all stored messages) for a specific chat

        Args:
            chat_id: The Telegram chat ID

        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        if chat_id not in self.conversations:
            return []

        return self.conversations[chat_id]

    def _get_memory_file_path(self, chat_id: int) -> str:
        """
        Get the file path for a specific chat's memory file

        Args:
            chat_id: The Telegram chat ID

        Returns:
            Path to the memory file
        """
        return os.path.join(config.MEMORY_DIR, f"memory_{chat_id}.json")

    def _save_memory(self, chat_id: int) -> None:
        """
        Save a specific chat's memory to disk

        Args:
            chat_id: The Telegram chat ID
        """
        try:
            memory_file = self._get_memory_file_path(chat_id)
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations[chat_id], f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved memory for chat {chat_id} to {memory_file}")
        except Exception as e:
            logger.error(f"Error saving memory for chat {chat_id}: {e}")

    def _load_memory(self, chat_id: int) -> None:
        """
        Load a specific chat's memory from disk

        Args:
            chat_id: The Telegram chat ID
        """
        memory_file = self._get_memory_file_path(chat_id)
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    self.conversations[chat_id] = json.load(f)
                logger.info(f"Loaded memory for chat {chat_id} with {len(self.conversations[chat_id])} messages")
            except Exception as e:
                logger.error(f"Error loading memory for chat {chat_id}: {e}")
                # Initialize empty conversation if loading fails
                self.conversations[chat_id] = []

    def _load_all_memories(self) -> None:
        """
        Load all memories from disk
        """
        try:
            # Get all memory files
            memory_files = [f for f in os.listdir(config.MEMORY_DIR) if f.startswith("memory_") and f.endswith(".json")]
            logger.info(f"Found {len(memory_files)} memory files to load")

            # Load each memory file
            for memory_file in memory_files:
                try:
                    # Extract chat_id from filename (memory_CHATID.json)
                    chat_id = int(memory_file.split('_')[1].split('.')[0])
                    self._load_memory(chat_id)
                except Exception as e:
                    logger.error(f"Error processing memory file {memory_file}: {e}")
        except Exception as e:
            logger.error(f"Error loading memories: {e}")
