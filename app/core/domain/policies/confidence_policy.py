"""Confidence policy - domain business rules for auto-approval thresholds."""


class ConfidencePolicy:
    """
    Domain policy for determining auto-approval based on AI confidence scores.

    This policy defines the thresholds for automatic processing vs. human review.
    """

    # Auto-approve threshold: above this, no human review needed
    AUTO_APPROVE_THRESHOLD = 0.85

    # High confidence threshold: recommendations are likely accurate
    HIGH_CONFIDENCE_THRESHOLD = 0.70

    # Low confidence threshold: below this, requires careful human review
    LOW_CONFIDENCE_THRESHOLD = 0.40

    @staticmethod
    def should_auto_approve(confidence: float) -> bool:
        """
        Determine if intake should be auto-approved based on confidence score.

        Args:
            confidence: AI confidence score (0.0 to 1.0)

        Returns:
            True if should auto-approve, False if requires human review
        """
        return confidence >= ConfidencePolicy.AUTO_APPROVE_THRESHOLD

    @staticmethod
    def is_high_confidence(confidence: float) -> bool:
        """Check if confidence is high (above HIGH_CONFIDENCE_THRESHOLD)."""
        return confidence >= ConfidencePolicy.HIGH_CONFIDENCE_THRESHOLD

    @staticmethod
    def is_low_confidence(confidence: float) -> bool:
        """Check if confidence is low (below LOW_CONFIDENCE_THRESHOLD)."""
        return confidence < ConfidencePolicy.LOW_CONFIDENCE_THRESHOLD

    @staticmethod
    def requires_review(confidence: float) -> bool:
        """Determine if human review is required (inverse of should_auto_approve)."""
        return not ConfidencePolicy.should_auto_approve(confidence)
