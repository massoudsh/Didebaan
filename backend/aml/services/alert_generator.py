"""
Alert Generator Service
Generates and manages alerts for suspicious transactions
"""
import logging
import uuid
from decimal import Decimal
from typing import Dict, Optional, List
from django.utils import timezone
from django.db.models import Avg

from aml.models import Alert, Transaction, Customer, Rule

logger = logging.getLogger('aml')


class AlertGenerator:
    """
    Service for generating and managing AML alerts
    """
    
    def generate_alert(self, transaction: Transaction,
                      triggered_rules: List[Rule],
                      risk_score: Decimal,
                      severity: str,
                      reasons: List[str]) -> Alert:
        """
        Generate an alert for a suspicious transaction

        Args:
            transaction: Transaction that triggered the alert
            triggered_rules: List of rules that were triggered
            risk_score: Risk score of the transaction
            severity: Alert severity level
            reasons: List of reasons why the alert was generated

        Returns:
            Created Alert object
        """
        logger.info(f"Generating alert for transaction {transaction.transaction_id}")

        # Generate unique alert ID
        alert_id = f"ALT-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

        # Create alert title
        title = self._generate_alert_title(transaction, triggered_rules, severity)

        # Create alert description
        description = self._generate_alert_description(transaction, triggered_rules, reasons, risk_score)

        # Explainable AI: structured per-rule breakdown of why this alert fired
        explanation = self._build_explanation(triggered_rules, reasons)

        # Create alert
        alert = Alert.objects.create(
            alert_id=alert_id,
            transaction=transaction,
            customer=transaction.customer,
            severity=severity,
            status='OPEN',
            title=title,
            description=description,
            risk_score=risk_score,
            explanation=explanation,
        )
        
        # Add triggered rules
        if triggered_rules:
            alert.triggered_rules.set(triggered_rules)
        
        logger.info(f"Alert {alert_id} created for transaction {transaction.transaction_id} with severity {severity}")
        
        return alert
    
    def _build_explanation(self, triggered_rules: List[Rule], reasons: List[str]) -> List[Dict]:
        """
        Build an explainable-AI breakdown: one entry per triggered rule with
        the rule type/name, the human-readable reason, and its weighted
        contribution to the final risk score — so reviewers see *why*, not
        just a bare severity number.
        """
        explanation = []
        for i, rule in enumerate(triggered_rules):
            reason = reasons[i] if i < len(reasons) else ''
            explanation.append({
                'rule_name': rule.name,
                'rule_type': rule.rule_type,
                'reason': reason,
                'weight': float(rule.risk_weight),
            })
        return explanation

    def _generate_alert_title(self, transaction: Transaction,
                             triggered_rules: List[Rule],
                             severity: str) -> str:
        """Generate alert title"""
        if triggered_rules:
            rule_names = ', '.join([rule.name for rule in triggered_rules[:2]])
            if len(triggered_rules) > 2:
                rule_names += f" and {len(triggered_rules) - 2} more"
            return f"[{severity}] Suspicious Transaction - Rules: {rule_names}"
        else:
            return f"[{severity}] Suspicious Transaction - High Risk Score"
    
    def _generate_alert_description(self, transaction: Transaction,
                                   triggered_rules: List[Rule],
                                   reasons: List[str],
                                   risk_score: Decimal) -> str:
        """Generate alert description"""
        description_parts = [
            f"Transaction ID: {transaction.transaction_id}",
            f"Customer: {transaction.customer.first_name} {transaction.customer.last_name} ({transaction.customer.customer_id})",
            f"Amount: {transaction.amount} {transaction.currency}",
            f"Type: {transaction.get_transaction_type_display()}",
            f"Date: {transaction.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Risk Score: {risk_score}",
        ]
        
        if transaction.receiver_account:
            description_parts.append(f"Receiver: {transaction.receiver_account}")
        
        if transaction.receiver_country:
            description_parts.append(f"Receiver Country: {transaction.receiver_country}")
        
        if reasons:
            description_parts.append("\nTriggered Reasons:")
            for i, reason in enumerate(reasons, 1):
                description_parts.append(f"{i}. {reason}")
        
        if triggered_rules:
            description_parts.append("\nTriggered Rules:")
            for rule in triggered_rules:
                description_parts.append(f"- {rule.name}: {rule.description}")
        
        return "\n".join(description_parts)
    
    def review_alert(self, alert: Alert, reviewer: str, 
                    status: str, notes: str) -> Alert:
        """
        Review an alert and update its status
        
        Args:
            alert: Alert to review
            reviewer: Username of reviewer
            status: New status (RESOLVED, FALSE_POSITIVE, ESCALATED)
            notes: Review notes
            
        Returns:
            Updated Alert object
        """
        logger.info(f"Reviewing alert {alert.alert_id} by {reviewer}")
        
        alert.status = status
        alert.reviewed_by = reviewer
        alert.reviewed_at = timezone.now()
        alert.review_notes = notes
        
        if status == 'RESOLVED':
            alert.resolution_notes = notes
        
        alert.save()
        
        logger.info(f"Alert {alert.alert_id} reviewed. Status: {status}")
        
        return alert
    
    def escalate_alert(self, alert: Alert, reviewer: str, notes: str) -> Alert:
        """
        Escalate an alert to higher priority
        
        Args:
            alert: Alert to escalate
            reviewer: Username of reviewer
            notes: Escalation notes
            
        Returns:
            Updated Alert object
        """
        logger.info(f"Escalating alert {alert.alert_id}")
        
        # Increase severity if not already CRITICAL
        if alert.severity != 'CRITICAL':
            severity_map = {
                'LOW': 'MEDIUM',
                'MEDIUM': 'HIGH',
                'HIGH': 'CRITICAL'
            }
            alert.severity = severity_map.get(alert.severity, 'CRITICAL')
        
        alert.status = 'ESCALATED'
        alert.reviewed_by = reviewer
        alert.reviewed_at = timezone.now()
        alert.review_notes = f"ESCALATED: {notes}"
        alert.save()
        
        logger.info(f"Alert {alert.alert_id} escalated to {alert.severity}")
        
        return alert
    
    def mark_false_positive(self, alert: Alert, reviewer: str, notes: str) -> Alert:
        """
        Mark an alert as false positive
        
        Args:
            alert: Alert to mark
            reviewer: Username of reviewer
            notes: Notes explaining why it's false positive
            
        Returns:
            Updated Alert object
        """
        logger.info(f"Marking alert {alert.alert_id} as false positive")
        
        alert.status = 'FALSE_POSITIVE'
        alert.reviewed_by = reviewer
        alert.reviewed_at = timezone.now()
        alert.review_notes = notes
        alert.resolution_notes = f"False Positive: {notes}"
        alert.save()
        
        logger.info(f"Alert {alert.alert_id} marked as false positive")
        
        return alert
    
    def get_alerts_by_severity(self, severity: str, status: Optional[str] = None) -> List[Alert]:
        """
        Get alerts filtered by severity and optionally by status
        
        Args:
            severity: Severity level
            status: Optional status filter
            
        Returns:
            List of Alert objects
        """
        queryset = Alert.objects.filter(severity=severity)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return list(queryset.order_by('-created_at'))
    
    def get_customer_alerts(self, customer: Customer, 
                           status: Optional[str] = None,
                           limit: int = 50) -> List[Alert]:
        """
        Get alerts for a specific customer
        
        Args:
            customer: Customer object
            status: Optional status filter
            limit: Maximum number of alerts to return
            
        Returns:
            List of Alert objects
        """
        queryset = Alert.objects.filter(customer=customer)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return list(queryset.order_by('-created_at')[:limit])
    
    def get_open_alerts_count(self) -> Dict[str, int]:
        """
        Get count of open alerts by severity
        
        Returns:
            Dict with severity as key and count as value
        """
        alerts = Alert.objects.filter(status='OPEN')
        
        return {
            'LOW': alerts.filter(severity='LOW').count(),
            'MEDIUM': alerts.filter(severity='MEDIUM').count(),
            'HIGH': alerts.filter(severity='HIGH').count(),
            'CRITICAL': alerts.filter(severity='CRITICAL').count(),
            'TOTAL': alerts.count()
        }
    
    def get_alerts_statistics(self, days: int = 30) -> Dict:
        """
        Get alert statistics for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict with statistics
        """
        start_date = timezone.now() - timezone.timedelta(days=days)
        alerts = Alert.objects.filter(created_at__gte=start_date)
        
        return {
            'total': alerts.count(),
            'by_severity': {
                'LOW': alerts.filter(severity='LOW').count(),
                'MEDIUM': alerts.filter(severity='MEDIUM').count(),
                'HIGH': alerts.filter(severity='HIGH').count(),
                'CRITICAL': alerts.filter(severity='CRITICAL').count(),
            },
            'by_status': {
                'OPEN': alerts.filter(status='OPEN').count(),
                'UNDER_REVIEW': alerts.filter(status='UNDER_REVIEW').count(),
                'RESOLVED': alerts.filter(status='RESOLVED').count(),
                'FALSE_POSITIVE': alerts.filter(status='FALSE_POSITIVE').count(),
                'ESCALATED': alerts.filter(status='ESCALATED').count(),
            },
            'average_risk_score': float(
                alerts.aggregate(avg=Avg('risk_score'))['avg'] or Decimal('0')
            ) if alerts.exists() else 0,
        }


# Singleton instance
_alert_generator_instance = None

def get_alert_generator() -> AlertGenerator:
    """Get singleton instance of AlertGenerator"""
    global _alert_generator_instance
    if _alert_generator_instance is None:
        _alert_generator_instance = AlertGenerator()
    return _alert_generator_instance

