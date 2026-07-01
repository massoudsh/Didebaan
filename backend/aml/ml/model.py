"""
ML Risk Model Stub — Issue #34
سرویس یادگیری ماشین برای امتیازدهی ریسک بر اساس تاریخچه هشدارها

این ماژول یک stub آموزشی است و در نسخه‌های بعدی با مدل واقعی جایگزین می‌شود.
در نسخه کامل: داده‌های تاریخی هشدارها → scikit-learn RandomForest → امتیاز ریسک ML
"""
import logging
from decimal import Decimal
from typing import Dict, Optional

logger = logging.getLogger('aml')


class MLRiskModel:
    """
    Stub ML model for transaction risk scoring.
    Phase 1: rule-based fallback
    Phase 2 (future): trained on historical alert data using scikit-learn
    """

    VERSION = '0.1.0-stub'
    IS_TRAINED = False

    def __init__(self):
        self._model = None
        logger.info(f"MLRiskModel initialized (stub mode, v{self.VERSION})")

    def predict_risk_score(self, features: Dict) -> Dict:
        """
        Predict risk score from transaction features.

        Args:
            features: dict with keys:
                - amount (float): transaction amount in IRR
                - transaction_type (str): TRANSFER / DEPOSIT / etc.
                - is_cross_border (bool)
                - receiver_country (str): ISO-2 code
                - customer_risk_level (str): LOW/MEDIUM/HIGH/CRITICAL
                - transaction_hour (int): 0-23
                - daily_transaction_count (int)
                - amount_vs_avg_ratio (float)

        Returns:
            dict with 'score' (0-100), 'confidence', 'model_version', 'note'
        """
        if not self.IS_TRAINED:
            return self._heuristic_fallback(features)

        # Future: return self._model.predict(...)
        return self._heuristic_fallback(features)

    def _heuristic_fallback(self, features: Dict) -> Dict:
        """Simple heuristic scoring while model is not yet trained."""
        score = 0.0

        # Amount-based
        amount = float(features.get('amount', 0))
        if amount >= 500_000_000:    # >= 500M IRR (CTR threshold)
            score += 40
        elif amount >= 100_000_000:  # >= 100M IRR
            score += 25
        elif amount >= 10_000_000:   # >= 10M IRR
            score += 10

        # Cross-border
        if features.get('is_cross_border'):
            score += 20

        # Customer risk
        risk_level_score = {
            'LOW': 0, 'MEDIUM': 10, 'HIGH': 25, 'CRITICAL': 40
        }
        score += risk_level_score.get(features.get('customer_risk_level', 'MEDIUM'), 10)

        # Unusual hour (2 AM – 5 AM Tehran time)
        hour = features.get('transaction_hour', 12)
        if 2 <= hour <= 5:
            score += 10

        # Velocity
        daily_count = features.get('daily_transaction_count', 0)
        if daily_count >= 20:
            score += 15
        elif daily_count >= 10:
            score += 8

        final_score = min(100.0, score)
        return {
            'score': round(final_score, 2),
            'confidence': 0.55,   # Low confidence — heuristic only
            'model_version': self.VERSION,
            'note': 'heuristic_fallback — model not yet trained',
        }

    def train(self, X, y) -> Dict:
        """
        Placeholder for model training.
        Future: train a RandomForestClassifier on labeled alert data.

        Args:
            X: feature matrix (list of dicts or numpy array)
            y: labels (0 = not suspicious, 1 = suspicious)

        Returns:
            dict with training metrics
        """
        logger.warning("MLRiskModel.train() called but model training is not yet implemented. "
                       "Implement with scikit-learn RandomForest or XGBoost.")
        return {
            'status': 'not_implemented',
            'message': 'Model training is planned for a future release.',
        }

    def load(self, model_path: str) -> bool:
        """Load a previously trained model from disk (pickle/joblib)."""
        try:
            import joblib
            self._model = joblib.load(model_path)
            self.IS_TRAINED = True
            logger.info(f"ML model loaded from {model_path}")
            return True
        except Exception as exc:
            logger.error(f"Failed to load ML model: {exc}")
            return False

    def save(self, model_path: str) -> bool:
        """Save trained model to disk."""
        if not self.IS_TRAINED or self._model is None:
            logger.warning("No trained model to save.")
            return False
        try:
            import joblib
            joblib.dump(self._model, model_path)
            logger.info(f"ML model saved to {model_path}")
            return True
        except Exception as exc:
            logger.error(f"Failed to save ML model: {exc}")
            return False


# ─── Singleton ───────────────────────────────────────────────────────────────
_ml_model_instance: Optional[MLRiskModel] = None


def get_ml_model() -> MLRiskModel:
    """Return singleton MLRiskModel instance."""
    global _ml_model_instance
    if _ml_model_instance is None:
        _ml_model_instance = MLRiskModel()
    return _ml_model_instance
