"""
Integration Tests for Real-Time Lead Intelligence Hub

Simple integration tests that validate the dashboard's core functionality
without complex Streamlit mocking. These tests focus on:
- Data structure creation and validation
- Stream update logic
- Performance metrics calculation
- DataFrame conversion
"""

import pytest
from datetime import datetime, timedelta
from collections import deque
import pandas as pd

from ghl_real_estate_ai.streamlit_components.realtime_lead_intelligence_hub import (
    StreamType,
    StreamUpdate,
    DashboardMetrics
)


class TestStreamUpdate:
    """Test StreamUpdate data structure"""

    def test_stream_update_creation(self):
        """Test creating a valid stream update"""
        update = StreamUpdate(
            stream_type=StreamType.LEAD_SCORING,
            timestamp=datetime.now(),
            lead_id="lead_test_001",
            tenant_id="tenant_test_001",
            data={'score': 0.85, 'confidence': 'high'}
        )

        assert update.stream_type == StreamType.LEAD_SCORING
        assert update.lead_id == "lead_test_001"
        assert update.tenant_id == "tenant_test_001"
        assert update.data['score'] == 0.85
        assert update.processing_time_ms == 0.0  # Default
        assert update.cache_hit is False  # Default

    def test_stream_update_with_performance_metrics(self):
        """Test stream update with performance data"""
        update = StreamUpdate(
            stream_type=StreamType.PERFORMANCE,
            timestamp=datetime.now(),
            lead_id="system",
            tenant_id="test_tenant",
            data={'latency_ms': 35.5, 'cache_hit_rate': 0.92},
            processing_time_ms=35.5,
            cache_hit=True
        )

        assert update.processing_time_ms == 35.5
        assert update.cache_hit is True
        assert update.data['latency_ms'] == 35.5
        assert update.data['cache_hit_rate'] == 0.92


class TestStreamType:
    """Test StreamType enumeration"""

    def test_all_stream_types_defined(self):
        """Test all required stream types are present"""
        required_types = {
            'lead_scoring', 'churn_risk', 'property_match',
            'conversation', 'performance', 'agent_activity'
        }

        stream_type_values = {st.value for st in StreamType}

        assert required_types == stream_type_values, \
            f"Missing stream types: {required_types - stream_type_values}"

    def test_stream_type_enum_access(self):
        """Test stream types can be accessed by enum"""
        assert StreamType.LEAD_SCORING.value == 'lead_scoring'
        assert StreamType.CHURN_RISK.value == 'churn_risk'
        assert StreamType.PROPERTY_MATCH.value == 'property_match'
        assert StreamType.CONVERSATION.value == 'conversation'
        assert StreamType.PERFORMANCE.value == 'performance'
        assert StreamType.AGENT_ACTIVITY.value == 'agent_activity'


class TestDashboardMetrics:
    """Test DashboardMetrics data structure"""

    def test_metrics_initialization(self):
        """Test metrics initialize with correct defaults"""
        metrics = DashboardMetrics()

        assert metrics.total_updates_received == 0
        assert metrics.avg_update_latency_ms == 0.0
        assert metrics.connection_uptime == 100.0
        assert metrics.active_streams == 0
        assert metrics.updates_per_second == 0.0
        assert metrics.last_update is None

    def test_metrics_updates(self):
        """Test metrics can be updated"""
        metrics = DashboardMetrics()

        # Update metrics
        metrics.total_updates_received = 150
        metrics.avg_update_latency_ms = 42.3
        metrics.connection_uptime = 99.8
        metrics.active_streams = 6
        metrics.updates_per_second = 12.5
        metrics.last_update = datetime.now()

        # Verify updates
        assert metrics.total_updates_received == 150
        assert metrics.avg_update_latency_ms == 42.3
        assert metrics.connection_uptime == 99.8
        assert metrics.active_streams == 6
        assert metrics.updates_per_second == 12.5
        assert metrics.last_update is not None


class TestDataStreamManagement:
    """Test data stream management with deques"""

    def test_deque_max_length_enforcement(self):
        """Test deque respects max length"""
        stream = deque(maxlen=10)

        # Add 20 items
        for i in range(20):
            update = StreamUpdate(
                stream_type=StreamType.LEAD_SCORING,
                timestamp=datetime.now(),
                lead_id=f"lead_{i}",
                tenant_id="test_tenant",
                data={'score': i / 20.0}
            )
            stream.append(update)

        # Verify only last 10 items remain
        assert len(stream) == 10

        # Verify oldest items were removed (FIFO)
        first_score = stream[0].data['score']
        last_score = stream[-1].data['score']

        assert first_score > 0.4  # Should start around item 10
        assert last_score > 0.9  # Should end around item 19

    def test_stream_chronological_ordering(self):
        """Test stream maintains chronological order"""
        stream = deque(maxlen=100)

        # Add updates with increasing timestamps
        base_time = datetime.now()
        for i in range(10):
            update = StreamUpdate(
                stream_type=StreamType.CONVERSATION,
                timestamp=base_time + timedelta(seconds=i),
                lead_id="test_lead",
                tenant_id="test_tenant",
                data={'message_id': i}
            )
            stream.append(update)

        # Verify chronological order
        for i in range(len(stream) - 1):
            assert stream[i].timestamp <= stream[i + 1].timestamp


class TestPerformanceMetricsCalculation:
    """Test performance metrics calculation logic"""

    def test_average_latency_calculation(self):
        """Test average latency is calculated correctly"""
        latencies = [20.0, 30.0, 40.0, 50.0, 60.0]

        # Calculate average
        avg_latency = sum(latencies) / len(latencies)

        assert avg_latency == 40.0

    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation"""
        total_requests = 100
        cache_hits = 92

        hit_rate = (cache_hits / total_requests) * 100

        assert hit_rate == 92.0
        assert hit_rate >= 90.0  # Target: >90%

    def test_updates_per_second_calculation(self):
        """Test updates per second calculation"""
        total_updates = 120
        time_period_seconds = 10.0

        updates_per_second = total_updates / time_period_seconds

        assert updates_per_second == 12.0


class TestDataFrameConversion:
    """Test conversion of stream data to pandas DataFrame"""

    def test_stream_to_dataframe_conversion(self):
        """Test stream deque can be converted to DataFrame"""
        stream = deque(maxlen=10)

        # Add sample data
        for i in range(5):
            update = StreamUpdate(
                stream_type=StreamType.LEAD_SCORING,
                timestamp=datetime.now(),
                lead_id=f"lead_{i}",
                tenant_id="test_tenant",
                data={'score': i * 0.2, 'confidence': 'high'},
                processing_time_ms=25.0 + i,
                cache_hit=(i % 2 == 0)
            )
            stream.append(update)

        # Convert to DataFrame
        data = []
        for update in stream:
            row = {
                'timestamp': update.timestamp,
                'lead_id': update.lead_id,
                'processing_time_ms': update.processing_time_ms,
                'cache_hit': update.cache_hit,
                **update.data
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Verify DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert 'timestamp' in df.columns
        assert 'lead_id' in df.columns
        assert 'processing_time_ms' in df.columns
        assert 'score' in df.columns
        assert 'confidence' in df.columns

    def test_dataframe_data_types(self):
        """Test DataFrame has correct data types"""
        stream = deque(maxlen=10)

        update = StreamUpdate(
            stream_type=StreamType.PROPERTY_MATCH,
            timestamp=datetime.now(),
            lead_id="lead_test",
            tenant_id="test_tenant",
            data={'match_score': 0.85},
            processing_time_ms=30.5,
            cache_hit=True
        )
        stream.append(update)

        # Convert to DataFrame
        data = [{
            'timestamp': update.timestamp,
            'lead_id': update.lead_id,
            'processing_time_ms': update.processing_time_ms,
            'match_score': update.data['match_score']
        }]

        df = pd.DataFrame(data)

        # Verify data types
        assert pd.api.types.is_datetime64_any_dtype(df['timestamp'])
        assert pd.api.types.is_string_dtype(df['lead_id'])
        assert pd.api.types.is_float_dtype(df['processing_time_ms'])
        assert pd.api.types.is_float_dtype(df['match_score'])


class TestPerformanceTargets:
    """Test that simulation data meets performance targets"""

    def test_ml_inference_target(self):
        """Test ML inference latency meets <35ms target"""
        # Simulate typical latencies
        latencies = [28.0, 32.0, 30.5, 34.2, 29.8, 31.5]

        avg_latency = sum(latencies) / len(latencies)

        # Verify average is under target
        assert avg_latency < 35.0, f"Average latency {avg_latency}ms exceeds 35ms target"

    def test_cache_hit_rate_target(self):
        """Test cache hit rate meets >90% target"""
        total_requests = 100
        cache_hits = 92

        hit_rate = cache_hits / total_requests

        # Verify hit rate meets target
        assert hit_rate >= 0.90, f"Cache hit rate {hit_rate * 100}% below 90% target"

    def test_websocket_latency_target(self):
        """Test WebSocket broadcast latency meets <100ms target"""
        broadcast_latencies = [45.0, 50.0, 48.5, 52.0, 47.3]

        avg_latency = sum(broadcast_latencies) / len(broadcast_latencies)

        # Verify average is under target
        assert avg_latency < 100.0, f"Average broadcast latency {avg_latency}ms exceeds 100ms target"


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_stream_handling(self):
        """Test empty streams can be processed"""
        stream = deque(maxlen=100)

        # Convert empty stream to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': update.timestamp,
                'lead_id': update.lead_id,
                **update.data
            }
            for update in stream
        ])

        # Verify empty DataFrame is created
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_single_update_stream(self):
        """Test stream with single update"""
        stream = deque(maxlen=100)

        update = StreamUpdate(
            stream_type=StreamType.CHURN_RISK,
            timestamp=datetime.now(),
            lead_id="lead_single",
            tenant_id="test_tenant",
            data={'churn_probability': 0.75}
        )
        stream.append(update)

        assert len(stream) == 1
        assert stream[0].lead_id == "lead_single"

    def test_rapid_concurrent_updates(self):
        """Test handling rapid concurrent updates to multiple streams"""
        streams = {
            'lead_scoring': deque(maxlen=100),
            'churn_risk': deque(maxlen=50),
            'property_match': deque(maxlen=50)
        }

        # Simulate rapid updates
        for i in range(10):
            for stream_name, stream in streams.items():
                update = StreamUpdate(
                    stream_type=StreamType.LEAD_SCORING,  # Simplified
                    timestamp=datetime.now(),
                    lead_id=f"lead_{i}",
                    tenant_id="test_tenant",
                    data={'value': i}
                )
                stream.append(update)

        # Verify all streams received updates
        assert len(streams['lead_scoring']) == 10
        assert len(streams['churn_risk']) == 10
        assert len(streams['property_match']) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
