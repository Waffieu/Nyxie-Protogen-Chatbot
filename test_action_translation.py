import logging
from action_translation import get_translated_action, translate_action

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

def test_action_translation():
    """Test that action translation works correctly"""

    # Test languages - focus on fewer languages to avoid API limits
    languages = ["English", "Spanish", "Turkish", "German"]

    # Test actions
    actions = [
        "EARS_PERK_UP",
        "TAIL_WAGS",
        "TILTS_HEAD",
        "EARS_DROOP",
        "BOUNCES",
        "SITS_DOWN"
    ]

    print("Testing action translation:")
    print("==========================")

    for language in languages:
        print(f"\nLanguage: {language}")
        print("-" * 20)

        for action in actions:
            translated = get_translated_action(action, language)
            print(f"{action}: {translated}")

    # Test direct translation
    print("\nTesting direct translation:")
    print("-" * 30)

    test_phrases = [
        "*tilts head curiously*",
        "*ears perk up with interest*",
        "*tail wags excitedly*",
        "*sits down and listens attentively*"
    ]

    for language in languages:
        if language != "English":  # Skip English as it doesn't need translation
            print(f"\nLanguage: {language}")
            print("-" * 20)

            for phrase in test_phrases:
                translated = translate_action(phrase, language)
                print(f"Original: {phrase}")
                print(f"Translated: {translated}\n")

    print("\nTest completed!")

if __name__ == "__main__":
    test_action_translation()
