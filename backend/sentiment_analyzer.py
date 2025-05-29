import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModel
import joblib
import re
from config import settings

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """TensorFlow-based sentiment analysis for news articles"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.max_length = 512
        self.confidence_threshold = 0.5
        
        # Sentiment keywords for rule-based fallback
        self.sentiment_keywords = {
            'positive': [
                'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'outstanding',
                'success', 'achievement', 'victory', 'win', 'progress', 'improvement', 'growth',
                'beneficial', 'advantage', 'positive', 'optimistic', 'hopeful', 'promising',
                'breakthrough', 'innovation', 'solution', 'opportunity', 'boost', 'rise',
                'celebrate', 'joy', 'happy', 'pleased', 'satisfied', 'thrilled', 'excited'
            ],
            'negative': [
                'bad', 'terrible', 'awful', 'horrible', 'disaster', 'crisis', 'problem',
                'failure', 'defeat', 'loss', 'decline', 'worsen', 'deteriorate', 'collapse',
                'harmful', 'dangerous', 'threat', 'risk', 'concern', 'worry', 'fear',
                'violence', 'war', 'conflict', 'attack', 'damage', 'destruction', 'death',
                'sad', 'angry', 'frustrated', 'disappointed', 'concerned', 'alarmed'
            ],
            'neutral': [
                'report', 'announce', 'state', 'say', 'according', 'officials', 'data',
                'information', 'details', 'statistics', 'analysis', 'study', 'research'
            ]
        }
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the sentiment analysis model"""
        try:
            # Try to load pre-trained model if it exists
            model_path = os.path.join(settings.HUGGINGFACE_CACHE_DIR, "sentiment_analyzer")
            if os.path.exists(model_path):
                self._load_saved_model(model_path)
            else:
                self._create_sentiment_model()
                
        except Exception as e:
            logger.error(f"Error initializing sentiment analyzer: {e}")
            logger.info("Falling back to rule-based sentiment analysis")
    
    def _create_sentiment_model(self):
        """Create a TensorFlow sentiment analysis model"""
        try:
            # Load pre-trained tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.MODEL_NAME,
                cache_dir=settings.HUGGINGFACE_CACHE_DIR
            )
            
            base_model = TFAutoModel.from_pretrained(
                settings.MODEL_NAME,
                cache_dir=settings.HUGGINGFACE_CACHE_DIR
            )
            
            # Create sentiment analysis head
            input_ids = tf.keras.Input(shape=(self.max_length,), dtype=tf.int32, name="input_ids")
            attention_mask = tf.keras.Input(shape=(self.max_length,), dtype=tf.int32, name="attention_mask")
            
            # Get embeddings from base model
            outputs = base_model(input_ids, attention_mask=attention_mask)
            sequence_output = outputs.last_hidden_state
            
            # Use CLS token for classification
            cls_token = sequence_output[:, 0, :]  # CLS token is first token
            
            # Additional pooling strategies
            mean_pooled = tf.keras.layers.GlobalAveragePooling1D()(sequence_output)
            max_pooled = tf.keras.layers.GlobalMaxPooling1D()(sequence_output)
            
            # Combine different pooling strategies
            combined = tf.keras.layers.Concatenate()([cls_token, mean_pooled, max_pooled])
            
            # Sentiment classification layers
            x = tf.keras.layers.Dense(512, activation='relu')(combined)
            x = tf.keras.layers.Dropout(0.3)(x)
            x = tf.keras.layers.BatchNormalization()(x)
            
            x = tf.keras.layers.Dense(256, activation='relu')(x)
            x = tf.keras.layers.Dropout(0.2)(x)
            x = tf.keras.layers.BatchNormalization()(x)
            
            x = tf.keras.layers.Dense(128, activation='relu')(x)
            x = tf.keras.layers.Dropout(0.1)(x)
            
            # Output layer - regression for sentiment score (-1 to 1)
            sentiment_score = tf.keras.layers.Dense(1, activation='tanh', name='sentiment_score')(x)
            
            # Additional output for confidence
            confidence = tf.keras.layers.Dense(1, activation='sigmoid', name='confidence')(x)
            
            self.model = tf.keras.Model(
                inputs=[input_ids, attention_mask],
                outputs=[sentiment_score, confidence]
            )
            
            # Compile with multiple losses
            self.model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=2e-5),
                loss={
                    'sentiment_score': 'mse',
                    'confidence': 'binary_crossentropy'
                },
                loss_weights={
                    'sentiment_score': 1.0,
                    'confidence': 0.5
                },
                metrics={
                    'sentiment_score': ['mae'],
                    'confidence': ['accuracy']
                }
            )
            
            logger.info("Created TensorFlow sentiment analysis model")
            
        except Exception as e:
            logger.error(f"Error creating sentiment model: {e}")
            self.model = None
            self.tokenizer = None
    
    def _load_saved_model(self, model_path: str):
        """Load a previously saved model"""
        try:
            self.model = tf.keras.models.load_model(model_path)
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            logger.info("Loaded saved sentiment analysis model")
        except Exception as e:
            logger.error(f"Error loading saved model: {e}")
            self._create_sentiment_model()
    
    def _preprocess_text(self, text: str) -> Dict[str, Any]:
        """Preprocess text for model input"""
        if not self.tokenizer:
            return {}
        
        try:
            # Clean and truncate text
            cleaned_text = self._clean_text(text)
            
            # Tokenize
            encoded = self.tokenizer(
                cleaned_text,
                max_length=self.max_length,
                padding='max_length',
                truncation=True,
                return_tensors='tf'
            )
            
            return {
                'input_ids': encoded['input_ids'],
                'attention_mask': encoded['attention_mask']
            }
            
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return {}
    
    def _clean_text(self, text: str) -> str:
        """Clean text for sentiment analysis"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation that affects sentiment
        text = re.sub(r'[^\w\s.,!?;:\'\"-]', '', text)
        
        # Handle common abbreviations
        text = re.sub(r'\bU\.S\.', 'United States', text)
        text = re.sub(r'\bUK\b', 'United Kingdom', text)
        
        return text.strip()
    
    def analyze_with_model(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze sentiment using the neural model"""
        if not self.model or not self.tokenizer:
            return None
        
        try:
            # Preprocess text
            inputs = self._preprocess_text(text)
            if not inputs:
                return None
            
            # Make prediction
            predictions = self.model.predict([inputs['input_ids'], inputs['attention_mask']], verbose=0)
            
            sentiment_score = float(predictions[0][0][0])  # First output, first batch, first value
            confidence = float(predictions[1][0][0])      # Second output, first batch, first value
            
            # Only return if confidence is above threshold
            if confidence < self.confidence_threshold:
                return None
            
            # Classify sentiment
            if sentiment_score > 0.1:
                sentiment_label = 'positive'
            elif sentiment_score < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return {
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'confidence': confidence,
                'method': 'neural'
            }
            
        except Exception as e:
            logger.error(f"Error in neural sentiment analysis: {e}")
            return None
    
    def analyze_with_rules(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using rule-based approach"""
        if not text:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.1,
                'method': 'rule-based'
            }
        
        text_lower = text.lower()
        
        # Count sentiment keywords
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        total_words = len(text_lower.split())
        
        for keyword in self.sentiment_keywords['positive']:
            matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            positive_count += matches
        
        for keyword in self.sentiment_keywords['negative']:
            matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            negative_count += matches
        
        for keyword in self.sentiment_keywords['neutral']:
            matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            neutral_count += matches
        
        # Handle negations (simple approach)
        negation_words = ['not', 'no', 'never', 'nothing', 'nowhere', 'neither', 'nobody', 'none']
        negation_count = sum(len(re.findall(r'\b' + re.escape(neg) + r'\b', text_lower)) for neg in negation_words)
        
        # Adjust for negations (flip positive/negative if high negation count)
        if negation_count > 2:
            positive_count, negative_count = negative_count, positive_count
        
        # Calculate sentiment score
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            sentiment_score = 0.0
            sentiment_label = 'neutral'
            confidence = 0.1
        else:
            # Normalize by total words to account for text length
            positive_ratio = positive_count / max(total_words, 1)
            negative_ratio = negative_count / max(total_words, 1)
            
            # Calculate final score (-1 to 1)
            sentiment_score = np.tanh((positive_ratio - negative_ratio) * 10)  # tanh to bound between -1,1
            
            # Determine label
            if sentiment_score > 0.1:
                sentiment_label = 'positive'
            elif sentiment_score < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            # Calculate confidence based on the number of sentiment words found
            confidence = min(total_sentiment_words / max(total_words * 0.1, 1), 1.0)
        
        return {
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'confidence': confidence,
            'method': 'rule-based',
            'details': {
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'negation_count': negation_count,
                'total_words': total_words
            }
        }
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Main sentiment analysis method - tries neural model first, falls back to rules"""
        if not text or len(text.strip()) < 10:  # Skip very short texts
            return self.analyze_with_rules(text)
        
        # Try neural model first
        neural_result = self.analyze_with_model(text)
        if neural_result and neural_result['confidence'] > self.confidence_threshold:
            return neural_result
        
        # Fall back to rule-based analysis
        rule_result = self.analyze_with_rules(text)
        
        # If neural model gave a low-confidence result, blend with rules
        if neural_result and neural_result['confidence'] > 0.2:
            # Weighted average of neural and rule-based scores
            neural_weight = neural_result['confidence']
            rule_weight = rule_result['confidence']
            total_weight = neural_weight + rule_weight
            
            if total_weight > 0:
                blended_score = (
                    neural_result['sentiment_score'] * neural_weight +
                    rule_result['sentiment_score'] * rule_weight
                ) / total_weight
                
                # Determine label from blended score
                if blended_score > 0.1:
                    sentiment_label = 'positive'
                elif blended_score < -0.1:
                    sentiment_label = 'negative'
                else:
                    sentiment_label = 'neutral'
                
                return {
                    'sentiment_score': blended_score,
                    'sentiment_label': sentiment_label,
                    'confidence': min(total_weight / 2, 1.0),
                    'method': 'blended'
                }
        
        return rule_result
    
    def batch_analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze sentiment for multiple texts"""
        results = []
        for text in texts:
            result = self.analyze_text(text)
            results.append(result)
        return results
    
    def analyze_article(self, title: str, content: str) -> Dict[str, Any]:
        """Analyze sentiment for a complete article (title + content)"""
        # Combine title and content with appropriate weighting
        if title and content:
            # Give title more weight as it's usually more indicative of sentiment
            combined_text = f"{title}. {title}. {content}"
        elif title:
            combined_text = title
        elif content:
            combined_text = content
        else:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'method': 'insufficient_data'
            }
        
        return self.analyze_text(combined_text)
    
    def get_sentiment_distribution(self, texts: List[str]) -> Dict[str, Any]:
        """Get sentiment distribution across multiple texts"""
        if not texts:
            return {}
        
        results = self.batch_analyze(texts)
        
        positive_count = sum(1 for r in results if r['sentiment_label'] == 'positive')
        negative_count = sum(1 for r in results if r['sentiment_label'] == 'negative')
        neutral_count = sum(1 for r in results if r['sentiment_label'] == 'neutral')
        
        total_texts = len(texts)
        avg_score = np.mean([r['sentiment_score'] for r in results])
        avg_confidence = np.mean([r['confidence'] for r in results])
        
        return {
            'total_texts': total_texts,
            'distribution': {
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count
            },
            'percentages': {
                'positive': (positive_count / total_texts) * 100,
                'negative': (negative_count / total_texts) * 100,
                'neutral': (neutral_count / total_texts) * 100
            },
            'average_score': avg_score,
            'average_confidence': avg_confidence,
            'overall_sentiment': 'positive' if avg_score > 0.1 else 'negative' if avg_score < -0.1 else 'neutral'
        }
    
    def save_model(self, path: str):
        """Save the trained model"""
        if self.model and self.tokenizer:
            try:
                os.makedirs(path, exist_ok=True)
                self.model.save(path)
                self.tokenizer.save_pretrained(path)
                logger.info(f"Saved sentiment model to {path}")
            except Exception as e:
                logger.error(f"Error saving model: {e}")

# Global instance
sentiment_analyzer = SentimentAnalyzer() 