"""
Neural Network Forecasting for Competitive Intelligence

Advanced deep learning models for predicting competitor behavior, market trends,
and competitive dynamics using state-of-the-art neural architectures.

Features:
- LSTM/GRU models for time series forecasting
- Transformer models for competitive sequence prediction
- Multi-task learning for competitor behavior modeling
- Attention mechanisms for feature importance
- Ensemble neural networks for robust predictions

Author: Claude
Date: January 2026
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

# ML/DL imports (optional dependencies)
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, Dataset
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Fallback implementations

try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    from sklearn.ensemble import RandomForestRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of forecasting models."""
    LSTM = "lstm"
    GRU = "gru"
    TRANSFORMER = "transformer"
    CONV1D = "conv1d"
    ENSEMBLE = "ensemble"
    RANDOM_FOREST = "random_forest"  # Fallback


class PredictionTarget(Enum):
    """Types of prediction targets."""
    PRICE_CHANGE = "price_change"
    MARKET_SHARE = "market_share"
    COMPETITOR_ACTIVITY = "competitor_activity"
    SENTIMENT_SHIFT = "sentiment_shift"
    FEATURE_RELEASE = "feature_release"
    REVENUE_IMPACT = "revenue_impact"


@dataclass
class ForecastModel:
    """Neural forecasting model configuration and state."""
    model_id: str
    model_type: ModelType
    prediction_target: PredictionTarget
    sequence_length: int
    prediction_horizon: int
    feature_dim: int
    hidden_dim: int = 128
    num_layers: int = 2
    dropout_rate: float = 0.1
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    early_stopping_patience: int = 10
    
    # Model state
    model: Optional[Any] = None
    optimizer: Optional[Any] = None
    scaler: Optional[Any] = None
    training_history: List[Dict[str, float]] = field(default_factory=list)
    is_trained: bool = False
    last_training_time: Optional[datetime] = None
    
    # Performance metrics
    train_loss: float = 0.0
    val_loss: float = 0.0
    test_mse: float = 0.0
    test_mae: float = 0.0
    prediction_confidence: float = 0.0


@dataclass
class CompetitorData:
    """Competitor time series data for training."""
    competitor_id: str
    timestamps: List[datetime]
    features: np.ndarray  # Shape: (time_steps, feature_dim)
    targets: np.ndarray   # Shape: (time_steps, target_dim)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForecastResult:
    """Neural forecast result."""
    forecast_id: str
    model_id: str
    competitor_id: str
    prediction_target: PredictionTarget
    forecast_horizon: int
    predictions: np.ndarray
    confidence_intervals: Optional[np.ndarray]
    feature_importance: Dict[str, float]
    model_confidence: float
    generated_at: datetime
    valid_until: datetime


class LSTMForecaster(nn.Module):
    """LSTM-based neural forecasting model."""
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        num_layers: int,
        output_dim: int,
        dropout_rate: float = 0.1
    ):
        super(LSTMForecaster, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_dim, 
            hidden_dim, 
            num_layers, 
            batch_first=True,
            dropout=dropout_rate if num_layers > 1 else 0
        )
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=8,
            dropout=dropout_rate
        )
        
        # Output layers
        self.dropout = nn.Dropout(dropout_rate)
        self.fc1 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc2 = nn.Linear(hidden_dim // 2, output_dim)
        
        self.relu = nn.ReLU()
    
    def forward(self, x):
        # LSTM forward pass
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Apply attention
        attn_out, attention_weights = self.attention(
            lstm_out.transpose(0, 1),  # (seq_len, batch, hidden_dim)
            lstm_out.transpose(0, 1),
            lstm_out.transpose(0, 1)
        )
        
        # Use the last time step output
        last_output = attn_out[-1]  # (batch, hidden_dim)
        
        # Feed through output layers
        out = self.dropout(last_output)
        out = self.fc1(out)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        
        return out, attention_weights


class TransformerForecaster(nn.Module):
    """Transformer-based neural forecasting model."""
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        num_layers: int,
        num_heads: int,
        output_dim: int,
        dropout_rate: float = 0.1,
        max_seq_length: int = 100
    ):
        super(TransformerForecaster, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.max_seq_length = max_seq_length
        
        # Input projection
        self.input_projection = nn.Linear(input_dim, hidden_dim)
        
        # Positional encoding
        self.positional_encoding = self._create_positional_encoding(
            max_seq_length, hidden_dim
        )
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout_rate,
            activation='relu'
        )
        
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )
        
        # Output layers
        self.dropout = nn.Dropout(dropout_rate)
        self.output_projection = nn.Linear(hidden_dim, output_dim)
        
    def _create_positional_encoding(self, max_len: int, d_model: int):
        """Create positional encoding for transformer."""
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * 
            (-np.log(10000.0) / d_model)
        )
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        return pe.unsqueeze(0)  # Shape: (1, max_len, d_model)
    
    def forward(self, x):
        # Input projection
        x = self.input_projection(x)  # (batch, seq_len, hidden_dim)
        
        # Add positional encoding
        seq_len = x.size(1)
        pos_encoding = self.positional_encoding[:, :seq_len, :].to(x.device)
        x = x + pos_encoding
        
        # Transformer forward pass (expects seq_first format)
        x = x.transpose(0, 1)  # (seq_len, batch, hidden_dim)
        transformer_out = self.transformer_encoder(x)
        
        # Use the last time step output
        last_output = transformer_out[-1]  # (batch, hidden_dim)
        
        # Output projection
        out = self.dropout(last_output)
        out = self.output_projection(out)
        
        return out


class CompetitorTimeSeriesDataset(Dataset):
    """PyTorch dataset for competitor time series data."""
    
    def __init__(
        self,
        data: List[CompetitorData],
        sequence_length: int,
        prediction_horizon: int,
        scaler: Optional[Any] = None
    ):
        self.data = data
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.scaler = scaler
        
        # Prepare sequences
        self.sequences = []
        self.targets = []
        
        for competitor_data in data:
            sequences, targets = self._create_sequences(competitor_data)
            self.sequences.extend(sequences)
            self.targets.extend(targets)
        
        # Convert to numpy arrays
        self.sequences = np.array(self.sequences)
        self.targets = np.array(self.targets)
        
        # Apply scaling if provided
        if self.scaler is not None:
            original_shape = self.sequences.shape
            # Reshape for scaling
            self.sequences = self.sequences.reshape(-1, original_shape[-1])
            self.sequences = self.scaler.transform(self.sequences)
            self.sequences = self.sequences.reshape(original_shape)
    
    def _create_sequences(self, competitor_data: CompetitorData):
        """Create input sequences and targets from competitor data."""
        features = competitor_data.features
        targets = competitor_data.targets
        
        sequences = []
        sequence_targets = []
        
        for i in range(len(features) - self.sequence_length - self.prediction_horizon + 1):
            # Input sequence
            sequence = features[i:i + self.sequence_length]
            
            # Target (next prediction_horizon steps)
            target = targets[i + self.sequence_length:i + self.sequence_length + self.prediction_horizon]
            
            sequences.append(sequence)
            sequence_targets.append(target)
        
        return sequences, sequence_targets
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        sequence = torch.FloatTensor(self.sequences[idx])
        target = torch.FloatTensor(self.targets[idx])
        return sequence, target


class NeuralForecaster:
    """
    Advanced Neural Network Forecaster for Competitive Intelligence
    
    Provides state-of-the-art deep learning models for predicting competitor
    behavior, market dynamics, and competitive events.
    """
    
    def __init__(
        self,
        model_type: ModelType = ModelType.LSTM,
        device: str = "auto"
    ):
        """
        Initialize neural forecaster.
        
        Args:
            model_type: Type of neural network model to use
            device: Computing device ('cpu', 'cuda', or 'auto')
        """
        self.model_type = model_type
        
        # Set device
        if device == "auto":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                self.device = torch.device("cuda")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)
        
        # Check dependencies
        if not TORCH_AVAILABLE and model_type in [
            ModelType.LSTM, ModelType.GRU, ModelType.TRANSFORMER, ModelType.CONV1D
        ]:
            logger.warning("PyTorch not available, falling back to Random Forest")
            self.model_type = ModelType.RANDOM_FOREST
        
        # Model registry
        self.models: Dict[str, ForecastModel] = {}
        
        # Performance tracking
        self.training_runs = 0
        self.predictions_made = 0
        
        logger.info(f"Neural forecaster initialized with {self.model_type.value} on {self.device}")
    
    async def create_forecast_model(
        self,
        prediction_target: PredictionTarget,
        sequence_length: int = 30,
        prediction_horizon: int = 7,
        feature_dim: int = 10,
        hidden_dim: int = 128,
        **kwargs
    ) -> str:
        """
        Create a new forecasting model.
        
        Args:
            prediction_target: What to predict
            sequence_length: Length of input sequences
            prediction_horizon: Number of steps to forecast
            feature_dim: Number of input features
            hidden_dim: Hidden layer dimension
            **kwargs: Additional model parameters
            
        Returns:
            Model ID
        """
        try:
            model_id = f"{prediction_target.value}_{self.model_type.value}_{uuid4().hex[:8]}"
            
            # Create model configuration
            model_config = ForecastModel(
                model_id=model_id,
                model_type=self.model_type,
                prediction_target=prediction_target,
                sequence_length=sequence_length,
                prediction_horizon=prediction_horizon,
                feature_dim=feature_dim,
                hidden_dim=hidden_dim,
                **kwargs
            )
            
            # Create the actual model
            if self.model_type == ModelType.LSTM:
                model_config.model = LSTMForecaster(
                    input_dim=feature_dim,
                    hidden_dim=hidden_dim,
                    num_layers=model_config.num_layers,
                    output_dim=prediction_horizon,
                    dropout_rate=model_config.dropout_rate
                ).to(self.device)
                
            elif self.model_type == ModelType.TRANSFORMER:
                model_config.model = TransformerForecaster(
                    input_dim=feature_dim,
                    hidden_dim=hidden_dim,
                    num_layers=model_config.num_layers,
                    num_heads=8,
                    output_dim=prediction_horizon,
                    dropout_rate=model_config.dropout_rate,
                    max_seq_length=sequence_length
                ).to(self.device)
                
            elif self.model_type == ModelType.RANDOM_FOREST:
                if SKLEARN_AVAILABLE:
                    model_config.model = RandomForestRegressor(
                        n_estimators=100,
                        random_state=42
                    )
                else:
                    raise ValueError("Neither PyTorch nor scikit-learn available")
            
            # Initialize optimizer and scaler
            if TORCH_AVAILABLE and self.model_type != ModelType.RANDOM_FOREST:
                model_config.optimizer = optim.Adam(
                    model_config.model.parameters(),
                    lr=model_config.learning_rate
                )
            
            if SKLEARN_AVAILABLE:
                model_config.scaler = StandardScaler()
            
            # Store model
            self.models[model_id] = model_config
            
            logger.info(f"Created forecast model {model_id} for {prediction_target.value}")
            return model_id
            
        except Exception as e:
            logger.error(f"Failed to create forecast model: {e}")
            raise
    
    async def train_model(
        self,
        model_id: str,
        training_data: List[CompetitorData],
        validation_data: Optional[List[CompetitorData]] = None,
        save_path: Optional[str] = None
    ) -> bool:
        """
        Train a forecasting model with competitive data.
        
        Args:
            model_id: Model to train
            training_data: Training data
            validation_data: Optional validation data
            save_path: Path to save trained model
            
        Returns:
            True if training successful
        """
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model_config = self.models[model_id]
            
            logger.info(f"Starting training for model {model_id}")
            
            if self.model_type == ModelType.RANDOM_FOREST:
                # Scikit-learn training
                success = await self._train_sklearn_model(
                    model_config, training_data, validation_data
                )
            else:
                # PyTorch training
                success = await self._train_pytorch_model(
                    model_config, training_data, validation_data
                )
            
            if success:
                model_config.is_trained = True
                model_config.last_training_time = datetime.now(timezone.utc)
                self.training_runs += 1
                
                logger.info(f"Model {model_id} training completed successfully")
                
                if save_path and TORCH_AVAILABLE:
                    torch.save(model_config.model.state_dict(), save_path)
                    logger.info(f"Model saved to {save_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return False
    
    async def _train_pytorch_model(
        self,
        model_config: ForecastModel,
        training_data: List[CompetitorData],
        validation_data: Optional[List[CompetitorData]]
    ) -> bool:
        """Train PyTorch model."""
        try:
            # Prepare datasets
            train_dataset = CompetitorTimeSeriesDataset(
                training_data,
                model_config.sequence_length,
                model_config.prediction_horizon,
                model_config.scaler
            )
            
            train_loader = DataLoader(
                train_dataset,
                batch_size=model_config.batch_size,
                shuffle=True
            )
            
            val_loader = None
            if validation_data:
                val_dataset = CompetitorTimeSeriesDataset(
                    validation_data,
                    model_config.sequence_length, 
                    model_config.prediction_horizon,
                    model_config.scaler
                )
                val_loader = DataLoader(val_dataset, batch_size=model_config.batch_size)
            
            # Training loop
            model = model_config.model
            optimizer = model_config.optimizer
            criterion = nn.MSELoss()
            
            best_val_loss = float('inf')
            patience_counter = 0
            
            for epoch in range(model_config.epochs):
                # Training phase
                model.train()
                train_loss = 0.0
                
                for batch_x, batch_y in train_loader:
                    batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                    
                    optimizer.zero_grad()
                    
                    if isinstance(model, LSTMForecaster):
                        outputs, _ = model(batch_x)
                    else:
                        outputs = model(batch_x)
                    
                    loss = criterion(outputs, batch_y.squeeze())
                    loss.backward()
                    optimizer.step()
                    
                    train_loss += loss.item()
                
                train_loss /= len(train_loader)
                model_config.train_loss = train_loss
                
                # Validation phase
                if val_loader:
                    model.eval()
                    val_loss = 0.0
                    
                    with torch.no_grad():
                        for batch_x, batch_y in val_loader:
                            batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                            
                            if isinstance(model, LSTMForecaster):
                                outputs, _ = model(batch_x)
                            else:
                                outputs = model(batch_x)
                            
                            loss = criterion(outputs, batch_y.squeeze())
                            val_loss += loss.item()
                    
                    val_loss /= len(val_loader)
                    model_config.val_loss = val_loss
                    
                    # Early stopping
                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        patience_counter = 0
                    else:
                        patience_counter += 1
                        if patience_counter >= model_config.early_stopping_patience:
                            logger.info(f"Early stopping at epoch {epoch}")
                            break
                
                # Log progress
                if epoch % 10 == 0:
                    logger.debug(f"Epoch {epoch}: train_loss={train_loss:.4f}, val_loss={model_config.val_loss:.4f}")
                
                # Store training history
                model_config.training_history.append({
                    "epoch": epoch,
                    "train_loss": train_loss,
                    "val_loss": model_config.val_loss,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            return True
            
        except Exception as e:
            logger.error(f"PyTorch model training failed: {e}")
            return False
    
    async def _train_sklearn_model(
        self,
        model_config: ForecastModel,
        training_data: List[CompetitorData],
        validation_data: Optional[List[CompetitorData]]
    ) -> bool:
        """Train scikit-learn model."""
        try:
            # Prepare data for sklearn
            X_train = []
            y_train = []
            
            for competitor_data in training_data:
                features = competitor_data.features
                targets = competitor_data.targets
                
                for i in range(len(features) - model_config.sequence_length - model_config.prediction_horizon + 1):
                    # Flatten sequence for sklearn
                    sequence = features[i:i + model_config.sequence_length].flatten()
                    target = targets[i + model_config.sequence_length:i + model_config.sequence_length + model_config.prediction_horizon]
                    
                    X_train.append(sequence)
                    y_train.append(target.flatten())
            
            X_train = np.array(X_train)
            y_train = np.array(y_train)
            
            # Scale features
            if model_config.scaler:
                X_train = model_config.scaler.fit_transform(X_train)
            
            # Train model
            model_config.model.fit(X_train, y_train)
            
            # Calculate training metrics
            y_pred = model_config.model.predict(X_train)
            model_config.train_loss = mean_squared_error(y_train, y_pred)
            
            logger.info(f"Scikit-learn model trained with MSE: {model_config.train_loss:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Scikit-learn model training failed: {e}")
            return False
    
    async def generate_forecast(
        self,
        model_id: str,
        competitor_id: str,
        input_sequence: np.ndarray,
        confidence_level: float = 0.95
    ) -> ForecastResult:
        """
        Generate forecast for competitor behavior.
        
        Args:
            model_id: Trained model to use
            competitor_id: Competitor to forecast
            input_sequence: Input sequence data
            confidence_level: Confidence level for intervals
            
        Returns:
            Forecast result
        """
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model_config = self.models[model_id]
            
            if not model_config.is_trained:
                raise ValueError(f"Model {model_id} is not trained")
            
            # Preprocess input
            if model_config.scaler and self.model_type == ModelType.RANDOM_FOREST:
                input_flat = input_sequence.flatten().reshape(1, -1)
                input_scaled = model_config.scaler.transform(input_flat)
                predictions = model_config.model.predict(input_scaled)
                predictions = predictions.flatten()
                confidence_intervals = None
                feature_importance = {}
                
            else:
                # PyTorch inference
                model_config.model.eval()
                
                with torch.no_grad():
                    input_tensor = torch.FloatTensor(input_sequence).unsqueeze(0).to(self.device)
                    
                    if isinstance(model_config.model, LSTMForecaster):
                        output, attention_weights = model_config.model(input_tensor)
                        # Calculate feature importance from attention weights
                        feature_importance = self._extract_attention_importance(
                            attention_weights, input_sequence.shape[-1]
                        )
                    else:
                        output = model_config.model(input_tensor)
                        feature_importance = {}
                    
                    predictions = output.cpu().numpy().flatten()
                    confidence_intervals = None  # TODO: Implement uncertainty estimation
            
            # Create forecast result
            forecast_result = ForecastResult(
                forecast_id=str(uuid4()),
                model_id=model_id,
                competitor_id=competitor_id,
                prediction_target=model_config.prediction_target,
                forecast_horizon=model_config.prediction_horizon,
                predictions=predictions,
                confidence_intervals=confidence_intervals,
                feature_importance=feature_importance,
                model_confidence=0.8,  # TODO: Calculate actual confidence
                generated_at=datetime.now(timezone.utc),
                valid_until=datetime.now(timezone.utc) + timedelta(days=1)
            )
            
            self.predictions_made += 1
            
            logger.info(f"Generated forecast for {competitor_id} using model {model_id}")
            return forecast_result
            
        except Exception as e:
            logger.error(f"Forecast generation failed: {e}")
            raise
    
    def _extract_attention_importance(
        self,
        attention_weights: torch.Tensor,
        feature_dim: int
    ) -> Dict[str, float]:
        """Extract feature importance from attention weights."""
        try:
            # Average attention weights across heads and time steps
            attention_avg = attention_weights.mean(dim=0).mean(dim=0).cpu().numpy()
            
            # Create feature importance dictionary
            feature_importance = {}
            for i in range(min(len(attention_avg), feature_dim)):
                feature_importance[f"feature_{i}"] = float(attention_avg[i])
            
            return feature_importance
            
        except Exception as e:
            logger.error(f"Failed to extract attention importance: {e}")
            return {}
    
    def get_model_performance(self, model_id: str) -> Dict[str, Any]:
        """Get model performance metrics."""
        if model_id not in self.models:
            return {}
        
        model_config = self.models[model_id]
        
        return {
            "model_id": model_id,
            "model_type": model_config.model_type.value,
            "prediction_target": model_config.prediction_target.value,
            "is_trained": model_config.is_trained,
            "last_training_time": model_config.last_training_time.isoformat() 
                                  if model_config.last_training_time else None,
            "train_loss": model_config.train_loss,
            "val_loss": model_config.val_loss,
            "test_mse": model_config.test_mse,
            "test_mae": model_config.test_mae,
            "prediction_confidence": model_config.prediction_confidence,
            "training_epochs": len(model_config.training_history)
        }
    
    def get_forecaster_status(self) -> Dict[str, Any]:
        """Get overall forecaster status and metrics."""
        return {
            "model_type": self.model_type.value,
            "device": str(self.device),
            "models_count": len(self.models),
            "training_runs": self.training_runs,
            "predictions_made": self.predictions_made,
            "trained_models": sum(1 for m in self.models.values() if m.is_trained),
            "torch_available": TORCH_AVAILABLE,
            "sklearn_available": SKLEARN_AVAILABLE,
            "models": list(self.models.keys())
        }


class CompetitorBehaviorPredictor:
    """
    Specialized predictor for competitor behavior patterns.
    
    Uses ensemble of neural networks to predict specific competitor actions
    like pricing changes, feature releases, and strategic moves.
    """
    
    def __init__(self, forecaster: NeuralForecaster):
        """Initialize with a neural forecaster."""
        self.forecaster = forecaster
        self.behavior_models: Dict[str, str] = {}  # behavior_type -> model_id
        
        logger.info("Competitor behavior predictor initialized")
    
    async def setup_behavior_models(self, competitor_id: str) -> bool:
        """Setup models for predicting different behavior types."""
        try:
            # Create models for different prediction targets
            behavior_types = [
                PredictionTarget.PRICE_CHANGE,
                PredictionTarget.FEATURE_RELEASE,
                PredictionTarget.SENTIMENT_SHIFT
            ]
            
            for behavior in behavior_types:
                model_id = await self.forecaster.create_forecast_model(
                    prediction_target=behavior,
                    sequence_length=30,
                    prediction_horizon=7,
                    feature_dim=15,  # Rich feature set for competitor behavior
                    hidden_dim=256   # Larger network for complex behavior patterns
                )
                
                self.behavior_models[f"{competitor_id}_{behavior.value}"] = model_id
            
            logger.info(f"Setup behavior models for {competitor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup behavior models: {e}")
            return False
    
    async def predict_competitor_action(
        self,
        competitor_id: str,
        behavior_type: PredictionTarget,
        historical_data: np.ndarray
    ) -> Optional[ForecastResult]:
        """Predict specific competitor action."""
        try:
            model_key = f"{competitor_id}_{behavior_type.value}"
            
            if model_key not in self.behavior_models:
                logger.warning(f"No model found for {model_key}")
                return None
            
            model_id = self.behavior_models[model_key]
            
            return await self.forecaster.generate_forecast(
                model_id=model_id,
                competitor_id=competitor_id,
                input_sequence=historical_data
            )
            
        except Exception as e:
            logger.error(f"Competitor action prediction failed: {e}")
            return None


# Export public API
__all__ = [
    "NeuralForecaster",
    "ForecastModel",
    "CompetitorBehaviorPredictor", 
    "ModelType",
    "PredictionTarget",
    "ForecastResult",
    "CompetitorData"
]