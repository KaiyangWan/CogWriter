import re

def count_words(text):
    """
    Count words in mixed Chinese and English text.
    
    For English text:
    - Consecutive letters/numbers with special characters (^,-,.,etc) count as one word
    - Mathematical expressions (e.g., ma^2) count as one word
    - Hyphenated words (e.g., sub-task) count as one word
    - Punctuation marks are not counted
    
    For Chinese text:
    - Each Chinese character counts as one word
    - Chinese punctuation marks are not counted
    - Handles both full-width and half-width characters
    
    Args:
        text (str): Input text containing both Chinese and English
    Returns:
        tuple: (total word count, Chinese word count, English word count)
    """
    if not text:
        return 0
    
    # Convert full-width spaces to half-width spaces for consistency
    text = text.replace('\u3000', ' ')
    
    # Extract all Chinese characters using Unicode range
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    chinese_count = len(chinese_chars)
    
    # Remove Chinese characters but keep special characters that might be part of words
    # Then replace other punctuation with spaces
    english_text = re.sub(r'[\u4e00-\u9fff]', ' ', text)
    english_text = re.sub(r'[^\w\s\^\-\.\']', ' ', english_text)
    
    # Split on spaces and filter out empty strings
    # Words can now contain ^, -, and . in addition to alphanumeric characters
    english_words = [word for word in english_text.split() if word.strip()]
    english_count = len(english_words)
    
    total_count = chinese_count + english_count
    
    return total_count