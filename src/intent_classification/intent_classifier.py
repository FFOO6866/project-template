"""
BERT-based intent classification model for DIY customer queries.
Implements transformer-based classification with confidence scoring and fallback strategies.
"""

import json
import time
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, AutoModel, AutoConfig,
    AdamW, get_linear_schedule_with_warmup
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of intent classification"""
    intent: str
    confidence: float
    entities: Dict[str, str]
    processing_time_ms: float
    fallback_used: bool = False


class DIYIntentDataset(Dataset):
    """PyTorch dataset for DIY intent classification"""
    
    def __init__(self, texts: List[str], labels: List[str], tokenizer, max_length: int = 128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # Create label mapping
        unique_labels = list(set(labels))
        self.label_to_id = {label: idx for idx, label in enumerate(unique_labels)}
        self.id_to_label = {idx: label for label, idx in self.label_to_id.items()}
        
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        # Tokenize text
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(self.label_to_id[label], dtype=torch.long)
        }


class BERTIntentClassifier(nn.Module):
    """BERT-based intent classifier with confidence scoring"""
    
    def __init__(self, model_name: str, num_classes: int, dropout_rate: float = 0.3):
        super().__init__()
        
        self.config = AutoConfig.from_pretrained(model_name, num_labels=num_classes)
        self.bert = AutoModel.from_pretrained(model_name, config=self.config)
        
        # Classification head
        self.dropout = nn.Dropout(dropout_rate)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_classes)
        
        # Confidence estimation head
        self.confidence_head = nn.Sequential(
            nn.Linear(self.bert.config.hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )
        
    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        
        # Classification logits
        logits = self.classifier(self.dropout(pooled_output))
        
        # Confidence score
        confidence = self.confidence_head(pooled_output)
        
        return logits, confidence


class DIYIntentClassificationSystem:
    """Complete intent classification system with training and inference"""
    
    def __init__(self, model_name: str = "distilbert-base-uncased"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.label_to_id = {}
        self.id_to_label = {}
        
        # Performance tracking
        self.training_history = []
        self.inference_times = []
        
        # Fallback strategies
        self.keyword_fallbacks = {
            "project_planning": ["renovate", "plan", "design", "build", "install", "create"],
            "problem_solving": ["fix", "repair", "broken", "leak", "stuck", "emergency"],
            "tool_selection": ["drill", "saw", "hammer", "tool", "equipment", "recommend"],
            "product_comparison": ["vs", "compare", "better", "best", "which", "dewalt", "makita"],
            "learning": ["how to", "learn", "tutorial", "guide", "teach", "step by step"]
        }
        
    def load_training_data(self, data_path: str) -> Tuple[List[str], List[str]]:
        """Load training data from JSON file"""
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        texts = [item['query'] for item in data]
        labels = [item['intent'] for item in data]
        
        logger.info(f"Loaded {len(texts)} training examples")
        return texts, labels
    
    def prepare_model(self, num_classes: int):
        """Initialize model and tokenizer"""
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = BERTIntentClassifier(self.model_name, num_classes)
        
        logger.info(f"Initialized model with {num_classes} classes")
    
    def create_data_loaders(self, texts: List[str], labels: List[str], 
                           test_size: float = 0.2, batch_size: int = 16) -> Tuple[DataLoader, DataLoader]:
        """Create training and validation data loaders"""
        
        # Split data
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=test_size, random_state=42, stratify=labels
        )
        
        # Create datasets
        train_dataset = DIYIntentDataset(train_texts, train_labels, self.tokenizer)
        val_dataset = DIYIntentDataset(val_texts, val_labels, self.tokenizer)
        
        # Store label mappings
        self.label_to_id = train_dataset.label_to_id
        self.id_to_label = train_dataset.id_to_label
        
        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        logger.info(f"Created data loaders: {len(train_texts)} train, {len(val_texts)} val")
        return train_loader, val_loader
    
    def train_model(self, train_loader: DataLoader, val_loader: DataLoader, 
                   epochs: int = 3, learning_rate: float = 2e-5):
        """Train the BERT intent classifier"""
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(device)
        
        # Optimizer and scheduler
        optimizer = AdamW(self.model.parameters(), lr=learning_rate, eps=1e-8)
        total_steps = len(train_loader) * epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps=0, num_training_steps=total_steps
        )
        
        # Training loop
        for epoch in range(epochs):
            logger.info(f"Epoch {epoch + 1}/{epochs}")
            
            # Training
            self.model.train()
            total_train_loss = 0
            
            for batch in train_loader:
                optimizer.zero_grad()
                
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                logits, confidence = self.model(input_ids, attention_mask)
                
                # Classification loss
                criterion = nn.CrossEntropyLoss()
                classification_loss = criterion(logits, labels)
                
                # Confidence loss (MSE with predicted probability)
                predicted_probs = torch.softmax(logits, dim=-1)
                max_probs = torch.max(predicted_probs, dim=-1)[0]
                confidence_loss = nn.MSELoss()(confidence.squeeze(), max_probs)
                
                # Combined loss
                total_loss = classification_loss + 0.1 * confidence_loss
                total_loss.backward()
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                
                optimizer.step()
                scheduler.step()
                
                total_train_loss += total_loss.item()
            
            # Validation
            val_accuracy, val_loss = self.evaluate_model(val_loader, device)
            
            avg_train_loss = total_train_loss / len(train_loader)
            self.training_history.append({
                'epoch': epoch + 1,
                'train_loss': avg_train_loss,
                'val_loss': val_loss,
                'val_accuracy': val_accuracy
            })
            
            logger.info(f"Train Loss: {avg_train_loss:.4f}, Val Loss: {val_loss:.4f}, Val Acc: {val_accuracy:.4f}")
    
    def evaluate_model(self, val_loader: DataLoader, device) -> Tuple[float, float]:
        """Evaluate model on validation set"""
        self.model.eval()
        total_eval_loss = 0
        correct_predictions = 0
        total_predictions = 0
        
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                
                logits, confidence = self.model(input_ids, attention_mask)
                
                criterion = nn.CrossEntropyLoss()
                loss = criterion(logits, labels)
                total_eval_loss += loss.item()
                
                predictions = torch.argmax(logits, dim=-1)
                correct_predictions += (predictions == labels).sum().item()
                total_predictions += labels.size(0)
        
        accuracy = correct_predictions / total_predictions
        avg_loss = total_eval_loss / len(val_loader)
        
        return accuracy, avg_loss
    
    def keyword_fallback_classify(self, query: str) -> Tuple[str, float]:
        """Fallback classification using keyword matching"""
        query_lower = query.lower()
        scores = {}
        
        for intent, keywords in self.keyword_fallbacks.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                scores[intent] = score / len(keywords)
        
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = min(scores[best_intent], 0.7)  # Cap fallback confidence
            return best_intent, confidence
        
        return "learning", 0.3  # Default fallback
    
    def classify_intent(self, query: str, use_fallback: bool = True) -> ClassificationResult:
        """Classify intent of a single query with confidence scoring"""
        start_time = time.time()
        
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(device)
        self.model.eval()
        
        try:
            # Tokenize input
            encoding = self.tokenizer(
                query,
                truncation=True,
                padding='max_length',
                max_length=128,
                return_tensors='pt'
            )
            
            input_ids = encoding['input_ids'].to(device)
            attention_mask = encoding['attention_mask'].to(device)
            
            # Model inference
            with torch.no_grad():
                logits, confidence_score = self.model(input_ids, attention_mask)
                
                # Get predictions
                probabilities = torch.softmax(logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                max_probability = torch.max(probabilities).item()
                model_confidence = confidence_score.item()
                
                # Combine probability and confidence score
                final_confidence = (max_probability + model_confidence) / 2
                
                intent = self.id_to_label[predicted_class]
                
                # Use fallback if confidence is too low
                fallback_used = False
                if final_confidence < 0.5 and use_fallback:
                    fallback_intent, fallback_conf = self.keyword_fallback_classify(query)
                    if fallback_conf > final_confidence:
                        intent = fallback_intent
                        final_confidence = fallback_conf
                        fallback_used = True
                
        except Exception as e:
            logger.error(f"Model inference failed: {e}")
            if use_fallback:
                intent, final_confidence = self.keyword_fallback_classify(query)
                fallback_used = True
            else:
                raise
        
        # Extract basic entities (simple rule-based for now)
        entities = self.extract_basic_entities(query, intent)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        self.inference_times.append(processing_time)
        
        return ClassificationResult(
            intent=intent,
            confidence=final_confidence,
            entities=entities,
            processing_time_ms=processing_time,
            fallback_used=fallback_used
        )
    
    def extract_basic_entities(self, query: str, intent: str) -> Dict[str, str]:
        """Basic rule-based entity extraction"""
        entities = {}
        query_lower = query.lower()
        
        # Skill level detection
        if any(word in query_lower for word in ['beginner', 'basic', 'first time', 'new to']):
            entities['skill_level'] = 'beginner'
        elif any(word in query_lower for word in ['advanced', 'professional', 'expert']):
            entities['skill_level'] = 'advanced'
        else:
            entities['skill_level'] = 'intermediate'
        
        # Urgency detection
        if any(word in query_lower for word in ['urgent', 'emergency', 'asap', 'immediately']):
            entities['urgency'] = 'high'
        elif any(word in query_lower for word in ['fix', 'repair', 'broken']):
            entities['urgency'] = 'medium'
        else:
            entities['urgency'] = 'low'
        
        # Budget range detection
        if any(word in query_lower for word in ['cheap', 'budget', 'affordable']):
            entities['budget_range'] = 'under_500'
        elif any(word in query_lower for word in ['expensive', 'premium', 'professional']):
            entities['budget_range'] = 'above_5000'
        else:
            entities['budget_range'] = '500_2000'
        
        # Room/location detection
        rooms = ['bathroom', 'kitchen', 'bedroom', 'living room', 'balcony']
        for room in rooms:
            if room in query_lower:
                entities['room'] = room
                break
        
        return entities
    
    def save_model(self, model_path: str):
        """Save trained model and associated data"""
        model_dir = Path(model_path)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model state
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'label_to_id': self.label_to_id,
            'id_to_label': self.id_to_label,
            'model_name': self.model_name,
            'training_history': self.training_history
        }, model_dir / 'model.pt')
        
        # Save tokenizer
        self.tokenizer.save_pretrained(model_dir / 'tokenizer')
        
        logger.info(f"Model saved to {model_path}")
    
    def load_model(self, model_path: str):
        """Load trained model"""
        model_dir = Path(model_path)
        
        # Load model state
        checkpoint = torch.load(model_dir / 'model.pt', map_location='cpu')
        
        self.label_to_id = checkpoint['label_to_id']
        self.id_to_label = checkpoint['id_to_label']
        self.model_name = checkpoint['model_name']
        self.training_history = checkpoint.get('training_history', [])
        
        # Initialize model and load weights
        num_classes = len(self.label_to_id)
        self.model = BERTIntentClassifier(self.model_name, num_classes)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir / 'tokenizer')
        
        logger.info(f"Model loaded from {model_path}")
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.inference_times:
            return {"message": "No inference data available"}
        
        return {
            "avg_response_time_ms": np.mean(self.inference_times),
            "max_response_time_ms": np.max(self.inference_times),
            "min_response_time_ms": np.min(self.inference_times),
            "total_inferences": len(self.inference_times),
            "under_500ms_percent": (np.array(self.inference_times) < 500).mean() * 100
        }


def train_intent_classifier():
    """Train the intent classification model"""
    classifier = DIYIntentClassificationSystem()

    # Load training data - use environment variable or relative path
    import os
    project_root = Path(__file__).parent.parent.parent
    data_path = os.getenv(
        'INTENT_TRAINING_DATA_PATH',
        str(project_root / 'src' / 'intent_classification' / 'training_data.json')
    )
    texts, labels = classifier.load_training_data(data_path)

    # Prepare model
    num_classes = len(set(labels))
    classifier.prepare_model(num_classes)

    # Create data loaders
    train_loader, val_loader = classifier.create_data_loaders(texts, labels)

    # Train model
    classifier.train_model(train_loader, val_loader, epochs=3)

    # Save model - use environment variable or relative path
    model_path = os.getenv(
        'INTENT_CLASSIFIER_MODEL_PATH',
        str(project_root / 'src' / 'intent_classification' / 'trained_model')
    )
    classifier.save_model(model_path)

    logger.info("Training completed successfully!")
    return classifier


if __name__ == "__main__":
    # Train the model
    classifier = train_intent_classifier()
    
    # Test with example queries
    test_queries = [
        "I want to renovate my bathroom",
        "fix squeaky floors", 
        "install new toilet",
        "DeWalt vs Makita drill",
        "how to use a drill"
    ]
    
    for query in test_queries:
        result = classifier.classify_intent(query)
        print(f"Query: {query}")
        print(f"Intent: {result.intent} (confidence: {result.confidence:.3f})")
        print(f"Entities: {result.entities}")
        print(f"Time: {result.processing_time_ms:.1f}ms")
        print("-" * 50)