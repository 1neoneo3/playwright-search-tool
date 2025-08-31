"""Content extraction utilities."""

import re
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class ContentExtractor:
    """Utility class for extracting and cleaning web content."""
    
    def __init__(self, search_engine=None):
        self.search_engine = search_engine
        
    async def extract_content(self, url: str) -> Optional[Dict[str, str]]:
        """Extract structured content from a URL."""
        
        if not self.search_engine:
            return None
            
        try:
            await self.search_engine.page.goto(url, wait_until='networkidle')
            
            # Get page title
            title = await self.search_engine.page.title()
            
            # Get meta description
            description = await self.search_engine.page.get_attribute(
                'meta[name="description"]', 'content'
            ) or ""
            
            # Extract main content
            content = await self.search_engine.extract_text_content(url)
            
            # Get page language
            language = await self.search_engine.page.get_attribute('html', 'lang') or 'en'
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'content': content,
                'language': language,
                'word_count': len(content.split()) if content else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {str(e)}")
            return None
            
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content."""
        
        if not text:
            return ""
            
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common junk
        patterns = [
            r'Cookie[s]?\s+Policy',
            r'Privacy\s+Policy',
            r'Terms\s+of\s+Service',
            r'Accept\s+All\s+Cookies',
            r'This\s+website\s+uses\s+cookies',
            r'Advertisement',
            r'Skip\s+to\s+main\s+content',
            r'Jump\s+to\s+navigation'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
        return text.strip()
        
    @staticmethod 
    def extract_key_phrases(text: str, max_phrases: int = 10) -> List[str]:
        """Extract key phrases from text using simple techniques."""
        
        if not text:
            return []
            
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Count frequency
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
            
        # Get most frequent words
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'as', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        # Filter out common words
        filtered_freq = {
            word: freq for word, freq in word_freq.items() 
            if word not in common_words and freq > 1
        }
        
        # Sort by frequency
        sorted_words = sorted(filtered_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_words[:max_phrases]]
        
    @staticmethod
    def summarize_content(text: str, max_sentences: int = 3) -> str:
        """Create a simple extractive summary of the content."""
        
        if not text:
            return ""
            
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) <= max_sentences:
            return '. '.join(sentences) + '.'
            
        # Simple scoring: prefer sentences with more common words
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            words = len(sentence.split())
            position_score = 1.0 / (i + 1)  # Earlier sentences get higher score
            length_score = min(words / 20.0, 1.0)  # Prefer medium length
            score = position_score * 0.6 + length_score * 0.4
            scored_sentences.append((score, sentence))
            
        # Select top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [sentence for score, sentence in scored_sentences[:max_sentences]]
        
        return '. '.join(top_sentences) + '.'