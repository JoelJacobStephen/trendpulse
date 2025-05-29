import re
import string
from typing import List, Dict, Any, Optional
from datetime import datetime
import html
from bs4 import BeautifulSoup
import unicodedata
from dateutil import parser
import logging

logger = logging.getLogger(__name__)

class TextPreprocessor:
    """Text cleaning and preprocessing utilities"""
    
    def __init__(self):
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
    def clean_html(self, text: str) -> str:
        """Remove HTML tags and decode HTML entities"""
        if not text:
            return ""
            
        # Parse HTML and extract text
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Decode HTML entities
        text = html.unescape(text)
        
        return text
    
    def normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters"""
        if not text:
            return ""
            
        # Normalize unicode to NFKD form
        text = unicodedata.normalize('NFKD', text)
        
        # Remove non-ASCII characters
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        return text
    
    def clean_whitespace(self, text: str) -> str:
        """Clean and normalize whitespace"""
        if not text:
            return ""
            
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def remove_urls(self, text: str) -> str:
        """Remove URLs from text"""
        if not text:
            return ""
            
        # Remove HTTP/HTTPS URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove www URLs
        text = re.sub(r'www\.\S+', '', text)
        
        return text
    
    def clean_text(self, text: str) -> str:
        """Complete text cleaning pipeline"""
        if not text:
            return ""
            
        # Apply all cleaning steps
        text = self.clean_html(text)
        text = self.normalize_unicode(text)
        text = self.remove_urls(text)
        text = self.clean_whitespace(text)
        
        return text
    
    def extract_keywords(self, text: str, min_length: int = 3, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text"""
        if not text:
            return []
            
        # Clean and lowercase text
        text = self.clean_text(text).lower()
        
        # Split into words
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        
        # Filter words
        keywords = []
        for word in words:
            if (len(word) >= min_length and 
                word not in self.stopwords and 
                word.isalpha()):
                keywords.append(word)
        
        # Count frequency and return top keywords
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:max_keywords]]

class DateTimeProcessor:
    """Date and time processing utilities"""
    
    @staticmethod
    def parse_date(date_string: str) -> Optional[datetime]:
        """Parse various date formats to datetime"""
        if not date_string:
            return None
            
        try:
            # Try parsing with dateutil (handles most formats)
            return parser.parse(date_string)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse date '{date_string}': {e}")
            return None
    
    @staticmethod
    def format_date_iso(dt: datetime) -> str:
        """Format datetime to ISO string"""
        if not dt:
            return ""
        return dt.isoformat()

class ArticleProcessor:
    """Main article processing class"""
    
    def __init__(self):
        self.text_processor = TextPreprocessor()
        self.date_processor = DateTimeProcessor()
    
    def process_article(self, raw_article: Dict[str, Any]) -> Dict[str, Any]:
        """Process a raw article into clean, structured format"""
        processed = {}
        
        # Clean title
        processed['title'] = self.text_processor.clean_text(
            raw_article.get('title', '')
        )
        
        # Clean content
        content = raw_article.get('content', '') or raw_article.get('description', '')
        processed['content'] = self.text_processor.clean_text(content)
        
        # Generate summary (first 200 chars of content)
        if processed['content']:
            processed['summary'] = processed['content'][:200] + "..." if len(processed['content']) > 200 else processed['content']
        else:
            processed['summary'] = processed['title']
        
        # Process URL
        processed['url'] = raw_article.get('url', '')
        
        # Process date
        date_str = raw_article.get('published_date', '')
        parsed_date = self.date_processor.parse_date(date_str)
        processed['published_date'] = parsed_date or datetime.now()
        
        # Source information
        processed['source_name'] = raw_article.get('source_name', 'Unknown')
        processed['source_url'] = raw_article.get('source_url', '')
        processed['source_type'] = raw_article.get('source_type', 'unknown')
        
        # Extract keywords
        text_for_keywords = f"{processed['title']} {processed['content']}"
        processed['keywords'] = self.text_processor.extract_keywords(text_for_keywords)
        
        # Calculate word count
        processed['word_count'] = len(processed['content'].split()) if processed['content'] else 0
        
        # Language detection (simplified - assume English for now)
        processed['language'] = 'en'
        
        # Additional metadata
        processed['author'] = raw_article.get('author', '')
        processed['tags'] = raw_article.get('tags', [])
        processed['section'] = raw_article.get('section', '')
        processed['image_url'] = raw_article.get('image_url', '')
        
        return processed
    
    def deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on URL and title similarity"""
        seen_urls = set()
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            url = article.get('url', '')
            title = article.get('title', '').lower()
            
            # Skip if URL already seen
            if url and url in seen_urls:
                continue
                
            # Skip if very similar title already seen
            title_words = set(title.split())
            is_duplicate = False
            
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())
                # Check for high overlap
                if title_words and seen_words:
                    overlap = len(title_words.intersection(seen_words))
                    similarity = overlap / max(len(title_words), len(seen_words))
                    if similarity > 0.8:  # 80% similarity threshold
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_articles.append(article)
                if url:
                    seen_urls.add(url)
                if title:
                    seen_titles.add(title)
        
        logger.info(f"Deduplicated {len(articles)} -> {len(unique_articles)} articles")
        return unique_articles
    
    def batch_process_articles(self, raw_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of raw articles"""
        processed_articles = []
        
        for raw_article in raw_articles:
            try:
                processed = self.process_article(raw_article)
                if processed['title'] and processed['url']:  # Basic validation
                    processed_articles.append(processed)
            except Exception as e:
                logger.error(f"Error processing article: {e}")
                continue
        
        # Deduplicate
        processed_articles = self.deduplicate_articles(processed_articles)
        
        return processed_articles 