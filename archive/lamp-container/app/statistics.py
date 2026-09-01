"""
통계 및 분석 모듈
"""

from django_app.models import Pothole
from django.db.models import Count, Avg, Max, Q
from datetime import datetime, timedelta

def get_statistics(days=0, min_priority=0.0, risk_levels=None, location_types=None):
    """통계 데이터 조회"""
    try:
        today = datetime.now().date()
        
        if days == 0:
            start_date = today
        else:
            start_date = today - timedelta(days=days)
        
        queryset = Pothole.objects.filter(
            detected_at__date__gte=start_date,
            detected_at__date__lte=today
        )
        
        # 필터 적용
        if min_priority > 0:
            queryset = queryset.filter(priority_score__gte=min_priority)
        
        if risk_levels:
            queryset = queryset.filter(risk_level__in=risk_levels)
        
        if location_types:
            queryset = queryset.filter(location_type__in=location_types)
        
        # 통계 계산
        stats = queryset.aggregate(
            total_count=Count('id'),
            validated_count=Count('id', filter=Q(validation_result=True)),
            avg_depth_ratio=Avg('depth_ratio'),
            max_depth_ratio=Max('depth_ratio'),
            avg_priority=Avg('priority_score'),
            max_priority=Max('priority_score'),
            last_detection=Max('detected_at')
        )
        
        # 위험도별 분포
        risk_distribution = queryset.values('risk_level').annotate(
            count=Count('id')
        ).order_by('risk_level')
        
        # 위치 유형별 분포
        location_distribution = queryset.values('location_type').annotate(
            count=Count('id')
        ).order_by('location_type')
        
        # 일별 탐지 수
        daily_counts = queryset.extra(
            select={'day': 'DATE(detected_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        return {
            'total_count': stats['total_count'] or 0,
            'validated_count': stats['validated_count'] or 0,
            'avg_depth_ratio': float(stats['avg_depth_ratio']) if stats['avg_depth_ratio'] else 0.0,
            'max_depth_ratio': float(stats['max_depth_ratio']) if stats['max_depth_ratio'] else 0.0,
            'avg_priority': float(stats['avg_priority']) if stats['avg_priority'] else 0.0,
            'max_priority': float(stats['max_priority']) if stats['max_priority'] else 0.0,
            'last_detection': stats['last_detection'].isoformat() if stats['last_detection'] else None,
            'risk_distribution': list(risk_distribution),
            'location_distribution': list(location_distribution),
            'daily_counts': list(daily_counts)
        }
    except Exception as e:
        return {'error': str(e)}

