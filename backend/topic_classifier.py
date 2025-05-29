import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional
import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModel
from sklearn.preprocessing import LabelEncoder
import joblib
import re
from config import settings

logger = logging.getLogger(__name__)

class TopicClassifier:
    """TensorFlow-based topic classification for news articles"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.label_encoder = None
        self.max_length = 512
        self.confidence_threshold = 0.3
        
        # Topic keywords for rule-based classification (fallback)
        self.topic_keywords = {
            "Politics & Elections": [
                "election", "vote", "government", "president", "minister", "congress", 
                "senate", "parliament", "political", "campaign", "policy", "legislation",
                "democrat", "republican", "party", "ballot", "candidate"
            ],
            "Technology & Innovation": [
                "technology", "tech", "digital", "ai", "artificial intelligence", 
                "machine learning", "robot", "computer", "software", "app", "internet",
                "cybersecurity", "blockchain", "cryptocurrency", "innovation", "startup"
            ],
            "Climate & Environment": [
                "climate", "environment", "global warming", "carbon", "emission", 
                "renewable", "solar", "wind", "pollution", "sustainability", "green",
                "ecosystem", "conservation", "deforestation", "biodiversity"
            ],
            "Health & Medicine": [
                "health", "medical", "hospital", "doctor", "patient", "disease", 
                "treatment", "medicine", "pharmaceutical", "covid", "vaccine", "virus",
                "epidemic", "pandemic", "healthcare", "surgery", "therapy"
            ],
            "Business & Economy": [
                "business", "economy", "economic", "market", "stock", "finance", 
                "company", "corporation", "trade", "investment", "profit", "revenue",
                "gdp", "inflation", "recession", "banking", "financial"
            ],
            "Sports & Entertainment": [
                "sport", "sports", "game", "team", "player", "match", "championship",
                "olympic", "football", "basketball", "soccer", "tennis", "entertainment",
                "movie", "film", "music", "celebrity", "actor", "singer"
            ],
            "War & International": [
                "war", "military", "conflict", "defense", "army", "soldier", "battle",
                "weapon", "missile", "peace", "treaty", "international", "foreign",
                "diplomat", "embassy", "alliance", "nato", "un", "united nations"
            ],
            "Society & Culture": [
                "society", "social", "culture", "cultural", "community", "education",
                "school", "university", "religion", "religious", "art", "history",
                "tradition", "lifestyle", "family", "gender", "race", "equality"
            ],
            "Science & Research": [
                "science", "research", "study", "scientist", "discovery", "experiment",
                "laboratory", "academic", "university", "physics", "chemistry", "biology",
                "space", "nasa", "astronomy", "genetics", "dna"
            ],
            "Crime & Justice": [
                "crime", "criminal", "police", "court", "judge", "lawyer", "attorney",
                "trial", "sentence", "prison", "arrest", "investigation", "murder",
                "theft", "fraud", "justice", "law", "legal"
            ]
        }
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the classification model"""
        try:
            # Try to load pre-trained model if it exists
            model_path = os.path.join(settings.HUGGINGFACE_CACHE_DIR, "topic_classifier")
            if os.path.exists(model_path):
                self._load_saved_model(model_path)
            else:
                self._create_simple_model()
                
        except Exception as e:
            logger.error(f"Error initializing topic classifier: {e}")
            logger.info("Falling back to rule-based classification")
    
    def _create_simple_model(self):
        """Create a simple transformer-based model"""
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
            
            # Create classification head
            input_ids = tf.keras.Input(shape=(self.max_length,), dtype=tf.int32, name="input_ids")
            attention_mask = tf.keras.Input(shape=(self.max_length,), dtype=tf.int32, name="attention_mask")
            
            # Get embeddings from base model
            outputs = base_model(input_ids, attention_mask=attention_mask)
            sequence_output = outputs.last_hidden_state
            
            # Global average pooling
            pooled_output = tf.keras.layers.GlobalAveragePooling1D()(sequence_output)
            
            # Classification layers
            x = tf.keras.layers.Dense(512, activation='relu')(pooled_output)
            x = tf.keras.layers.Dropout(0.3)(x)
            x = tf.keras.layers.Dense(256, activation='relu')(x)
            x = tf.keras.layers.Dropout(0.2)(x)
            
            predictions = tf.keras.layers.Dense(
                len(settings.NEWS_TOPICS), 
                activation='softmax',
                name='topic_predictions'
            )(x)
            
            self.model = tf.keras.Model(
                inputs=[input_ids, attention_mask],
                outputs=predictions
            )
            
            self.model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=2e-5),
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy']
            )
            
            # Initialize label encoder
            self.label_encoder = LabelEncoder()
            self.label_encoder.fit(settings.NEWS_TOPICS)
            
            logger.info("Created simple topic classification model")
            
        except Exception as e:
            logger.error(f"Error creating model: {e}")
            self.model = None
            self.tokenizer = None
    
    def _load_saved_model(self, model_path: str):
        """Load a previously saved model"""
        try:
            self.model = tf.keras.models.load_model(model_path)
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.label_encoder = joblib.load(os.path.join(model_path, "label_encoder.pkl"))
            logger.info("Loaded saved topic classification model")
        except Exception as e:
            logger.error(f"Error loading saved model: {e}")
            self._create_simple_model()
    
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
        """Clean text for classification"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        return text.strip()
    
    def classify_with_model(self, text: str) -> Optional[Dict[str, Any]]:
        """Classify text using the neural model"""
        if not self.model or not self.tokenizer:
            return None
        
        try:
            # Preprocess text
            inputs = self._preprocess_text(text)
            if not inputs:
                return None
            
            # Make prediction
            predictions = self.model.predict([inputs['input_ids'], inputs['attention_mask']], verbose=0)
            
            # Get probabilities
            probabilities = predictions[0]
            
            # Get top predictions
            top_indices = np.argsort(probabilities)[::-1]
            
            primary_idx = top_indices[0]
            primary_confidence = float(probabilities[primary_idx])
            
            # Only return if confidence is above threshold
            if primary_confidence < self.confidence_threshold:
                return None
            
            primary_topic = self.label_encoder.inverse_transform([primary_idx])[0]
            
            # Get secondary topics
            secondary_topics = []
            for i in range(1, min(3, len(top_indices))):
                idx = top_indices[i]
                confidence = float(probabilities[idx])
                if confidence > 0.2:  # Lower threshold for secondary topics
                    topic = self.label_encoder.inverse_transform([idx])[0]
                    secondary_topics.append(topic)
            
            return {
                'primary_topic': primary_topic,
                'primary_confidence': primary_confidence,
                'secondary_topics': secondary_topics,
                'confidence': primary_confidence,
                'method': 'neural'
            }
            
        except Exception as e:
            logger.error(f"Error in neural classification: {e}")
            return None
    
    def classify_with_rules(self, text: str) -> Dict[str, Any]:
        """Classify text using rule-based approach"""
        if not text:
            return {
                'primary_topic': 'Society & Culture',  # Default
                'confidence': 0.1,
                'secondary_topics': [],
                'method': 'rule-based'
            }
        
        text_lower = text.lower()
        topic_scores = {}
        
        # Calculate scores for each topic based on keyword presence
        for topic, keywords in self.topic_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                # Count keyword occurrences
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                if count > 0:
                    score += count
                    matched_keywords.append(keyword)
            
            # Normalize score by text length
            text_words = len(text_lower.split())
            if text_words > 0:
                topic_scores[topic] = score / text_words
            else:
                topic_scores[topic] = 0
        
        # Sort topics by score
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_topics or sorted_topics[0][1] == 0:
            return {
                'primary_topic': 'Society & Culture',
                'confidence': 0.1,
                'secondary_topics': [],
                'method': 'rule-based'
            }
        
        primary_topic = sorted_topics[0][0]
        primary_score = sorted_topics[0][1]
        
        # Convert score to confidence (0-1 range)
        confidence = min(primary_score * 10, 1.0)  # Scale and cap at 1.0
        
        # Get secondary topics
        secondary_topics = []
        for topic, score in sorted_topics[1:3]:
            if score > 0 and score > primary_score * 0.5:  # At least 50% of primary score
                secondary_topics.append(topic)
        
        return {
            'primary_topic': primary_topic,
            'confidence': confidence,
            'secondary_topics': secondary_topics,
            'method': 'rule-based'
        }
    
    def classify_text(self, text: str) -> Dict[str, Any]:
        """Main classification method - tries neural model first, falls back to rules"""
        if not text:
            return self.classify_with_rules(text)
        
        # Try neural model first
        neural_result = self.classify_with_model(text)
        if neural_result and neural_result['confidence'] > self.confidence_threshold:
            return neural_result
        
        # Fall back to rule-based classification
        rule_result = self.classify_with_rules(text)
        
        # If neural model gave a low-confidence result, combine with rules
        if neural_result and neural_result['confidence'] > 0.1:
            # Use neural primary topic if it's above a minimal threshold
            if neural_result['confidence'] > rule_result['confidence']:
                return neural_result
        
        return rule_result
    
    def batch_classify(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Classify multiple texts"""
        results = []
        for text in texts:
            result = self.classify_text(text)
            results.append(result)
        return results
    
    def get_topic_distribution(self, texts: List[str]) -> Dict[str, float]:
        """Get distribution of topics across a list of texts"""
        if not texts:
            return {}
        
        topic_counts = {topic: 0 for topic in settings.NEWS_TOPICS}
        total_texts = len(texts)
        
        for text in texts:
            result = self.classify_text(text)
            primary_topic = result.get('primary_topic')
            if primary_topic in topic_counts:
                topic_counts[primary_topic] += 1
        
        # Convert to percentages
        topic_distribution = {
            topic: (count / total_texts) * 100 
            for topic, count in topic_counts.items()
        }
        
        return topic_distribution 