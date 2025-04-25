import logging
import os
from memory import Memory
import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

def test_memory_persistence():
    """Test that memory is saved and loaded correctly"""
    
    # Create a test chat ID
    test_chat_id = 12345
    
    # Create a memory instance
    memory = Memory()
    
    # Add some test messages
    memory.add_message(test_chat_id, "user", "Hello, this is a test message")
    memory.add_message(test_chat_id, "model", "Hi there! I'm responding to your test message")
    memory.add_message(test_chat_id, "user", "Can you remember this conversation?")
    
    # Check if the memory file was created
    memory_file = os.path.join(config.MEMORY_DIR, f"memory_{test_chat_id}.json")
    logger.info(f"Checking if memory file exists: {memory_file}")
    assert os.path.exists(memory_file), f"Memory file {memory_file} was not created"
    
    # Create a new memory instance to test loading
    new_memory = Memory()
    
    # Check if the messages were loaded
    loaded_messages = new_memory.get_long_memory(test_chat_id)
    logger.info(f"Loaded {len(loaded_messages)} messages for chat {test_chat_id}")
    assert len(loaded_messages) == 3, f"Expected 3 messages, got {len(loaded_messages)}"
    
    # Check the content of the messages
    assert loaded_messages[0]["role"] == "user", f"Expected first message role to be 'user', got {loaded_messages[0]['role']}"
    assert loaded_messages[0]["content"] == "Hello, this is a test message", f"First message content doesn't match"
    
    logger.info("Memory persistence test passed!")
    
    return True

if __name__ == "__main__":
    test_memory_persistence()
