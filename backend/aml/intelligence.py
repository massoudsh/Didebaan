from collections import Counter
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
import unicodedata

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from .models import Alert, Customer, Rule, Transaction, WatchlistEntry
from .permissions import CompliancePermission, RolePermission
from .rules.aml_rules import RuleEngine
from .serializers import AlertSerializer, AlertCommentSerializer
from .services.alert_generator import get_alert_generator


class WindowSerializer(serializers.Serializer):
    days = serializers.IntegerField(default=30, min_value=1, max_value=90)


class SimulationSerializer(WindowSerializer):
    rule_id = serializers.UUIDField()
    configuration = serializers.JSONField()
    limit = serializers.IntegerField(default=100, min_value=1, max_value=500)

    def validate_configuration(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError('Provide a non-empty configuration object.')
        return value


class ScreeningSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False, default='')
    national_id = serializers.CharField(max_length=50, required=False, default='')
    minimum_score = serializers.IntegerField(default=85, min_value=70, max_value=100)

    def validate(self, data):
        if not normalize_text(data['name']) and not normalize_text(data['national_id']):
            raise serializers.ValidationError('Provide a name or national ID.')
        return data


def normalize_text(value):
    value = unicodedata.normalize('NFKC', value).translate(str.maketrans('كيى', 'کیی'))
    value = ''.join(str(unicodedata.digit(c)) if c.isdigit() else c for c in value)
    return ' '.join(''.join(c if c.isalnum() else ' ' for c in value
                            if not unicodedata.combining(c) and c != '\u200c').split()).casefold()


CONFIG_KEYS = {
    'THRESHOLD': {'amount_threshold', 'daily_count_threshold', 'daily_amount_threshold'},
    'PATTERN': {'structuring_threshold', 'structuring_count', 'lookback_days',
                'rapid_transaction_threshold', 'rapid_transaction_minutes', 'rapid_transaction_count'},
    'BEHAVIORAL': {'amount_increase_threshold', 'lookback_days', 'pattern_change_detection',
                   'pattern_change_threshold'},
    'GEOGRAPHIC': {'high_risk_countries', 'cross_border_threshold'},
}


def validate_configuration(rule_type, config):
    if rule_type not in CONFIG_KEYS:
        raise serializers.ValidationError({'rule_id': 'Simulation supports THRESHOLD, PATTERN, BEHAVIORAL and GEOGRAPHIC rules.'})
    if not isinstance(config, dict) or not config or set(config) - CONFIG_KEYS[rule_type]:
        raise serializers.ValidationError({'configuration': 'Empty or unsupported configuration keys.'})
    for key, value in config.items():
        if key == 'high_risk_countries':
            if not isinstance(value, list) or len(value) > 250 or any(
                not isinstance(c, str) or len(c) != 2 or not c.isascii() or not c.isalpha() or c != c.upper()
                for c in value
            ):
                raise serializers.ValidationError({'configuration': 'Use a list of uppercase ISO-2 country codes.'})
        elif key == 'rapid_transaction_threshold' and isinstance(value, bool):
            continue
        elif key == 'pattern_change_detection':
            if not isinstance(value, bool):
                raise serializers.ValidationError({'configuration': 'pattern_change_detection must be boolean.'})
        else:
            try:
                number = Decimal(str(value))
            except (InvalidOperation, ValueError):
                raise serializers.ValidationError({'configuration': f'{key} must be a positive number.'})
            if isinstance(value, (bool, str)) or not number.is_finite() or not 0 < number <= Decimal('1000000000000000'):
                raise serializers.ValidationError({'configuration': f'{key} is outside the supported range.'})
            if key in {'lookback_days', 'rapid_transaction_minutes', 'daily_count_threshold',
                       'structuring_count', 'rapid_transaction_count'} and number != number.to_integral_value():
                raise serializers.ValidationError({'configuration': f'{key} must be an integer.'})
            if key == 'lookback_days' and number > 365:
                raise serializers.ValidationError({'configuration': 'lookback_days cannot exceed 365.'})
            if key == 'rapid_transaction_minutes' and number > 525600:
                raise serializers.ValidationError({'configuration': 'rapid_transaction_minutes cannot exceed one year.'})
    triggers = {
        'THRESHOLD': CONFIG_KEYS['THRESHOLD'],
        'PATTERN': {'structuring_threshold', 'rapid_transaction_threshold'},
        'BEHAVIORAL': {'amount_increase_threshold', 'pattern_change_detection'},
        'GEOGRAPHIC': CONFIG_KEYS['GEOGRAPHIC'],
    }
    if not any(config.get(key) for key in triggers[rule_type]):
        raise serializers.ValidationError({'configuration': 'Provide at least one detection condition.'})


class IntelligenceViewSet(viewsets.ViewSet):
    permission_classes = [RolePermission]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=False, methods=['post'], permission_classes=[CompliancePermission])
    def simulate(self, request):
        serializer = SimulationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        rule = get_object_or_404(Rule, pk=data['rule_id'])
        validate_configuration(rule.rule_type, data['configuration'])
        validate_configuration(rule.rule_type, rule.configuration)
        now = timezone.now()
        queryset = Transaction.objects.filter(
            transaction_date__gte=now - timedelta(days=data['days']),
            transaction_date__lte=now, status='COMPLETED',
        ).select_related('customer').order_by('-transaction_date', 'transaction_id')
        total = queryset.count()
        engine = RuleEngine()
        candidate = Rule(rule_type=rule.rule_type, configuration=data['configuration'], risk_weight=rule.risk_weight)
        results = []
        for txn in queryset[:data['limit']]:
            baseline = engine._evaluate_rule(rule, txn)
            proposed = engine._evaluate_rule(candidate, txn)
            results.append({
                'transaction_id': txn.transaction_id,
                'baseline_match': baseline['triggered'], 'candidate_match': proposed['triggered'],
                'baseline_score': min(Decimal('100'), Decimal(str(baseline['risk_score'])) * rule.risk_weight),
                'candidate_score': min(Decimal('100'), Decimal(str(proposed['risk_score'])) * rule.risk_weight),
                'reason': proposed['reason'],
            })
        return Response({
            'rule_id': str(rule.pk), 'rule_version': rule.version_number,
            'evaluated_at': now, 'eligible_count': total, 'evaluated_count': len(results),
            'truncated': total > len(results), 'sampling': 'newest_first',
            'baseline_matches': sum(r['baseline_match'] for r in results),
            'candidate_matches': sum(r['candidate_match'] for r in results),
            'new_matches': sum(r['candidate_match'] and not r['baseline_match'] for r in results),
            'removed_matches': sum(r['baseline_match'] and not r['candidate_match'] for r in results),
            'historical_policy': 'Transaction-time windows; current customer attributes and current database history. Not a historical snapshot.',
            'results': results,
        })

    @action(detail=False, methods=['post'], permission_classes=[CompliancePermission])
    def screen(self, request):
        serializer = ScreeningSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        name, national_id = normalize_text(data['name']), normalize_text(data['national_id'])
        entries = WatchlistEntry.objects.filter(is_active=True, entry_type='ENTITY').order_by('pk')
        count = entries.count()
        if count > 5000:
            raise serializers.ValidationError('Watchlist exceeds the synchronous screening limit of 5000 entities. No partial screening was performed; larger lists require indexed or background screening.')
        matches = []
        for entry in entries:
            exact_id = bool(national_id and national_id == normalize_text(entry.national_id))
            entry_name = normalize_text(entry.name)
            score = round(SequenceMatcher(None, name, entry_name, autojunk=False).ratio() * 100) if name and entry_name else 0
            if exact_id or (name and entry_name and score >= data['minimum_score']):
                matches.append({'id': entry.pk, 'name': entry.name, 'source_list': entry.source_list,
                                'match_type': 'national_id' if exact_id else 'name',
                                'score': 100 if exact_id else score})
        matches.sort(key=lambda m: (-m['score'], m['id']))
        return Response({'screened_count': count, 'match_count': len(matches),
                         'matches': matches[:100], 'truncated': len(matches) > 100,
                         'advisory': 'Potential matches require human review; no automatic blocking.'})

    @action(detail=False, methods=['get'])
    def graph(self, request):
        customer = get_object_or_404(Customer, customer_id=request.query_params.get('customer_id', ''))
        serializer = WindowSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        now = timezone.now()
        window = Q(transaction_date__gte=now - timedelta(days=serializer.validated_data['days']), transaction_date__lte=now)
        queryset = Transaction.objects.filter(window, customer=customer, status='COMPLETED').select_related('device', 'merchant').order_by('-transaction_date', 'transaction_id')
        total = queryset.count()
        nodes = {f'customer:{customer.customer_id}': {'id': f'customer:{customer.customer_id}', 'kind': 'customer', 'label': customer.customer_id}}
        edges = Counter()
        device_ids, merchant_ids = set(), set()
        for txn in queryset[:200]:
            entities = [('device', txn.device.device_id if txn.device else ''),
                        ('merchant', txn.merchant.merchant_id if txn.merchant else ''),
                        ('account', txn.receiver_account)]
            if txn.device_id:
                device_ids.add(txn.device_id)
            if txn.merchant_id:
                merchant_ids.add(txn.merchant_id)
            for kind, label in entities:
                if label:
                    node_id = f'{kind}:{label}'
                    nodes[node_id] = {'id': node_id, 'kind': kind, 'label': label}
                    edges[(f'customer:{customer.customer_id}', node_id)] += 1
        linked = Transaction.objects.filter(window, status='COMPLETED').filter(
            Q(device_id__in=device_ids) | Q(merchant_id__in=merchant_ids)
        ).exclude(customer=customer).values('customer__customer_id').annotate(transactions=Count('pk')).order_by('-transactions', 'customer__customer_id')
        peers = list(linked[:51])
        return Response({'customer_id': customer.customer_id, 'nodes': list(nodes.values()),
                         'edges': [{'source': s, 'target': t, 'transactions': c} for (s, t), c in edges.items()],
                         'related_customers': peers[:50], 'related_truncated': len(peers) > 50,
                         'eligible_count': total, 'sampled_count': min(total, 200), 'truncated': total > 200,
                         'note': 'Shared devices or merchants are investigative leads, not proof of fraud.'})

    @action(detail=False, methods=['get'])
    def sla(self, request):
        now = timezone.now()
        hours = get_alert_generator().get_sla_hours()
        deadline = timedelta(hours=float(hours))
        queryset = Alert.objects.filter(status__in=['OPEN', 'UNDER_REVIEW'], assigned_at__isnull=False).exclude(assigned_to='')
        overdue = queryset.filter(assigned_at__lt=now - deadline)
        due_soon = queryset.filter(assigned_at__gte=now - deadline, assigned_at__lte=now - deadline * .8)
        rows = list(queryset.select_related('customer').order_by('assigned_at', 'alert_id')[:200])
        return Response({'as_of': now, 'sla_hours': hours, 'assigned_open': queryset.count(),
                         'overdue': overdue.count(), 'due_soon': due_soon.count(),
                         'unassigned_open': Alert.objects.filter(status__in=['OPEN', 'UNDER_REVIEW'], assigned_to='').count(),
                         'truncated': queryset.count() > len(rows),
                         'results': [{'alert_id': a.alert_id, 'assigned_to': a.assigned_to,
                                      'severity': a.severity, 'due_at': a.assigned_at + deadline,
                                      'overdue': a.assigned_at + deadline < now} for a in rows]})

    @action(detail=False, methods=['get'], url_path='case-export', renderer_classes=[JSONRenderer])
    def case_export(self, request):
        alert = get_object_or_404(Alert.objects.select_related('customer', 'transaction'), alert_id=request.query_params.get('alert_id', ''))
        comments = alert.comments.order_by('created_at', 'pk')
        rules = alert.triggered_rules.order_by('pk').values('id', 'name', 'rule_type', 'version_number', 'configuration')
        count = comments.count()
        if count > 10000:
            raise serializers.ValidationError('Case history exceeds the evidence bundle limit. Export history separately through comments-export; no partial bundle was produced.')
        response = Response({'schema_version': 1, 'exported_at': timezone.now(),
                             'exported_by': request.user.get_username(),
                             'alert': AlertSerializer(alert).data,
                             'rules_current_snapshot': list(rules),
                             'history_count': count,
                             'history': AlertCommentSerializer(comments, many=True).data,
                             'notice': 'Current rule snapshot, not a reconstruction of rule versions at alert creation. Review applicable submission requirements before filing.'})
        response['Content-Disposition'] = 'attachment; filename="case-evidence.json"'
        response['Cache-Control'] = 'no-store'
        return response
