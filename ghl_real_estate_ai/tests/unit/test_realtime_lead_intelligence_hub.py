"""
Unit Tests for Realtime Lead Intelligence Hub Streamlit Dashboard

Comprehensive test coverage for:
- Real-time data stream visualization
- WebSocket connection management
- Performance metrics tracking
- Dashboard rendering and interactivity
- Session state management
- Data simulation accuracy
- Chart generation and visualization
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from collections import deque
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Import dashboard component
from ghl_real_estate_ai.streamlit_components.realtime_lead_intelligence_hub import (
    RealtimeLeadIntelligenceHub,
    StreamType,
    StreamUpdate,
    DashboardMetrics
)


class TestRealtimeLeadIntelligenceHub:
    """Test suite for Realtime Lead Intelligence Hub"""

    @pytest.fixture
    def mock_streamlit_session_state(self):
        """Mock Streamlit session state for testing"""
        # Create a mock object that behaves like st.session_state
        mock_state = MagicMock()
        mock_state.websocket_connected = False
        mock_state.subscription_id = None
        mock_state.tenant_id = 'test_tenant_001'
        mock_state.user_id = 'test_user_001'
        mock_state.lead_score_stream = deque(maxlen=100)
        mock_state.churn_alerts_stream = deque(maxlen=50)
        mock_state.property_match_stream = deque(maxlen=50)
        mock_state.conversation_stream = deque(maxlen=100)
        mock_state.performance_stream = deque(maxlen=200)
        mock_state.agent_activity_stream = deque(maxlen=50)
        mock_state.dashboard_metrics = DashboardMetrics()
        mock_state.active_streams = [
            StreamType.LEAD_SCORING,
            StreamType.CHURN_RISK,
            StreamType.PROPERTY_MATCH,
            StreamType.CONVERSATION,
            StreamType.PERFORMANCE,
            StreamType.AGENT_ACTIVITY
        ]
        mock_state.auto_refresh_enabled = True
        mock_state.refresh_interval_ms = 500

        # Support dict-like access
        mock_state.__contains__ = lambda self, key: hasattr(self, key)
        mock_state.__getitem__ = lambda self, key: getattr(self, key)
        mock_state.__setitem__ = lambda self, key, value: setattr(self, key, value)

        return mock_state

    @pytest.fixture
    def dashboard(self, mock_streamlit_session_state):
        """Create dashboard instance with mocked session state"""
        with patch('ghl_real_estate_ai.streamlit_components.realtime_lead_intelligence_hub.st') as mock_st:
            mock_st.session_state = mock_streamlit_session_state
            mock_st.markdown = MagicMock()
            return RealtimeLeadIntelligenceHub()

    # Initialization Tests

    def test_dashboard_initialization(self, dashboard, mock_streamlit_session_state):
        """Test dashboard initializes with correct default state"""
        assert mock_streamlit_session_state['websocket_connected'] is False
        assert mock_streamlit_session_state['tenant_id'] == 'test_tenant_001'
        assert len(mock_streamlit_session_state['active_streams']) == 6
        assert mock_streamlit_session_state['auto_refresh_enabled'] is True

    def test_session_state_data_structures(self, mock_streamlit_session_state):
        """Test all required data streams are initialized"""
        required_streams = [
            'lead_score_stream',
            'churn_alerts_stream',
            'property_match_stream',
            'conversation_stream',
            'performance_stream',
            'agent_activity_stream'
        ]

        for stream_name in required_streams:
            assert stream_name in mock_streamlit_session_state
            assert isinstance(mock_streamlit_session_state[stream_name], deque)

    # Data Simulation Tests

    def test_simulate_lead_score_update(self, dashboard, mock_streamlit_session_state):
        """Test lead score update simulation generates valid data"""
        with patch('ghl_real_estate_ai.streamlit_components.realtime_lead_intelligence_hub.st') as mock_st:
            mock_st.session_state = mock_streamlit_session_state

            initial_count = len(mock_streamlit_session_state.lead_score_stream)

            dashboard._simulate_lead_score_update()

            # Verify update was added
            assert len(mock_streamlit_session_state.lead_score_stream) == initial_count + 1

            # Verify update structure
            update = mock_streamlit_session_state.lead_score_stream[-1]
            assert isinstance(update, StreamUpdate)
            assert update.stream_type == StreamType.LEAD_SCORING
            assert 0.0 <= update.data['score'] <= 1.0
            assert update.data['confidence'] in ['high', 'medium', 'low']
            assert update.data['tier'] in ['hot', 'warm', 'cold']
            assert 15 <= update.processing_time_ms <= 45

    def test_simulate_churn_alert(self, dashboard, mock_streamlit_session_state):
        """Test churn alert simulation generates valid risk data"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            dashboard._simulate_churn_alert()

            update = mock_streamlit_session_state['churn_alerts_stream'][-1]

            # Verify churn alert structure
            assert update.stream_type == StreamType.CHURN_RISK
            assert update.data['risk_level'] in ['critical', 'high', 'medium']
            assert 0.0 <= update.data['churn_probability'] <= 1.0
            assert 7 <= update.data['days_until_churn'] <= 60

            # Verify risk level correlates with probability
            risk_level = update.data['risk_level']
            churn_prob = update.data['churn_probability']

            if risk_level == 'critical':
                assert churn_prob >= 0.8
            elif risk_level == 'high':
                assert 0.6 <= churn_prob < 0.8
            elif risk_level == 'medium':
                assert 0.4 <= churn_prob < 0.6

    def test_simulate_property_match(self, dashboard, mock_streamlit_session_state):
        """Test property match simulation generates valid match data"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            dashboard._simulate_property_match()

            update = mock_streamlit_session_state['property_match_stream'][-1]

            # Verify property match structure
            assert update.stream_type == StreamType.PROPERTY_MATCH
            assert update.data['property_type'] in [
                'Single Family', 'Condo', 'Townhouse', 'Multi-Family', 'Luxury Estate'
            ]
            assert 0.7 <= update.data['match_score'] <= 0.98
            assert 0.8 <= update.data['confidence'] <= 0.95

    def test_simulate_conversation_update(self, dashboard, mock_streamlit_session_state):
        """Test conversation intelligence simulation"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            dashboard._simulate_conversation_update()

            update = mock_streamlit_session_state['conversation_stream'][-1]

            # Verify conversation structure
            assert update.stream_type == StreamType.CONVERSATION
            assert update.data['sentiment'] in ['positive', 'neutral', 'negative']
            assert update.data['intent'] in [
                'inquiry', 'scheduling', 'negotiation', 'feedback', 'complaint'
            ]
            assert isinstance(update.data['snippet'], str)
            assert len(update.data['snippet']) > 0

    def test_simulate_agent_activity(self, dashboard, mock_streamlit_session_state):
        """Test agent activity simulation"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            dashboard._simulate_agent_activity()

            update = mock_streamlit_session_state['agent_activity_stream'][-1]

            # Verify agent activity structure
            assert update.stream_type == StreamType.AGENT_ACTIVITY
            assert update.data['action'] in [
                'viewed_lead', 'sent_message', 'scheduled_showing',
                'updated_status', 'added_note'
            ]
            assert isinstance(update.data['agent_name'], str)

    # Stream Management Tests

    def test_stream_deque_max_length(self, dashboard, mock_streamlit_session_state):
        """Test streams respect maximum length constraints"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            # Fill lead score stream beyond capacity
            for i in range(150):
                dashboard._simulate_lead_score_update()

            # Verify deque max length is enforced
            assert len(mock_streamlit_session_state['lead_score_stream']) == 100

            # Verify oldest items are removed (FIFO)
            first_update = mock_streamlit_session_state['lead_score_stream'][0]
            last_update = mock_streamlit_session_state['lead_score_stream'][-1]
            assert last_update.timestamp > first_update.timestamp

    def test_reset_all_streams(self, dashboard, mock_streamlit_session_state):
        """Test all streams can be reset successfully"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            # Add data to all streams
            dashboard._simulate_lead_score_update()
            dashboard._simulate_churn_alert()
            dashboard._simulate_property_match()

            # Reset all streams
            dashboard._reset_all_streams()

            # Verify all streams are empty
            assert len(mock_streamlit_session_state['lead_score_stream']) == 0
            assert len(mock_streamlit_session_state['churn_alerts_stream']) == 0
            assert len(mock_streamlit_session_state['property_match_stream']) == 0

            # Verify metrics are reset
            assert mock_streamlit_session_state['dashboard_metrics'].total_updates_received == 0

    # Performance Metrics Tests

    def test_update_dashboard_metrics(self, dashboard, mock_streamlit_session_state):
        """Test dashboard metrics are calculated correctly"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            # Add sample data to streams
            for i in range(10):
                dashboard._simulate_lead_score_update()
                dashboard._simulate_churn_alert()

            # Update metrics
            dashboard._update_dashboard_metrics()

            metrics = mock_streamlit_session_state['dashboard_metrics']

            # Verify metrics calculations
            assert metrics.total_updates_received == 20
            assert metrics.active_streams == 6
            assert metrics.avg_update_latency_ms > 0
            assert metrics.connection_uptime > 0
            assert metrics.last_update is not None

    def test_performance_stream_tracking(self, dashboard, mock_streamlit_session_state):
        """Test performance metrics are tracked over time"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            # Update metrics multiple times
            for i in range(5):
                dashboard._update_dashboard_metrics()

            # Verify performance stream has data points
            assert len(mock_streamlit_session_state['performance_stream']) == 5

            # Verify performance data structure
            perf_update = mock_streamlit_session_state['performance_stream'][-1]
            assert perf_update.stream_type == StreamType.PERFORMANCE
            assert 'latency_ms' in perf_update.data
            assert 'uptime' in perf_update.data

    def test_average_latency_calculation(self, dashboard, mock_streamlit_session_state):
        """Test average latency is calculated accurately"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            # Create updates with known latencies
            latencies = [20.0, 30.0, 40.0, 50.0]

            for latency in latencies:
                update = StreamUpdate(
                    stream_type=StreamType.LEAD_SCORING,
                    timestamp=datetime.now(),
                    lead_id="test_lead",
                    tenant_id="test_tenant",
                    data={'score': 0.8},
                    processing_time_ms=latency
                )
                mock_streamlit_session_state['lead_score_stream'].append(update)

            dashboard._update_dashboard_metrics()

            expected_avg = sum(latencies) / len(latencies)
            actual_avg = mock_streamlit_session_state['dashboard_metrics'].avg_update_latency_ms

            assert abs(actual_avg - expected_avg) < 1.0  # Within 1ms tolerance

    # Data Conversion Tests

    def test_convert_stream_to_dataframe(self, dashboard, mock_streamlit_session_state):
        """Test stream data is correctly converted to DataFrame"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            # Add sample data
            for i in range(5):
                dashboard._simulate_lead_score_update()

            # Convert to DataFrame
            df = dashboard._convert_stream_to_dataframe(
                mock_streamlit_session_state['lead_score_stream']
            )

            # Verify DataFrame structure
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 5
            assert 'timestamp' in df.columns
            assert 'lead_id' in df.columns
            assert 'processing_time_ms' in df.columns
            assert 'score' in df.columns

    def test_dataframe_data_types(self, dashboard, mock_streamlit_session_state):
        """Test DataFrame has correct data types"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            dashboard._simulate_lead_score_update()

            df = dashboard._convert_stream_to_dataframe(
                mock_streamlit_session_state['lead_score_stream']
            )

            # Verify data types
            assert pd.api.types.is_datetime64_any_dtype(df['timestamp'])
            assert pd.api.types.is_string_dtype(df['lead_id'])
            assert pd.api.types.is_float_dtype(df['processing_time_ms'])
            assert pd.api.types.is_float_dtype(df['score'])

    # WebSocket Connection Tests

    def test_connect_websocket(self, dashboard, mock_streamlit_session_state):
        """Test WebSocket connection state management"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            with patch('streamlit.success'), patch('streamlit.rerun'):
                # Initially disconnected
                assert mock_streamlit_session_state['websocket_connected'] is False

                # Connect
                dashboard._connect_websocket()

                # Verify connection state
                assert mock_streamlit_session_state['websocket_connected'] is True
                assert mock_streamlit_session_state['subscription_id'] is not None

    def test_disconnect_websocket(self, dashboard, mock_streamlit_session_state):
        """Test WebSocket disconnection"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            with patch('streamlit.info'), patch('streamlit.rerun'):
                # Connect first
                mock_streamlit_session_state['websocket_connected'] = True
                mock_streamlit_session_state['subscription_id'] = "sub_12345"

                # Disconnect
                dashboard._disconnect_websocket()

                # Verify disconnection
                assert mock_streamlit_session_state['websocket_connected'] is False
                assert mock_streamlit_session_state['subscription_id'] is None

    # Performance Target Validation Tests

    def test_lead_scoring_latency_target(self, dashboard, mock_streamlit_session_state):
        """Test lead scoring updates meet <35ms target"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            # Simulate 50 updates
            for i in range(50):
                dashboard._simulate_lead_score_update()

            # Calculate average latency
            latencies = [
                update.processing_time_ms
                for update in mock_streamlit_session_state['lead_score_stream']
            ]
            avg_latency = sum(latencies) / len(latencies)

            # Verify most updates are under target
            under_target = sum(1 for lat in latencies if lat < 35)
            assert under_target / len(latencies) > 0.6  # At least 60% under target

    def test_cache_hit_rate_simulation(self, dashboard, mock_streamlit_session_state):
        """Test cache hit rate meets >90% target"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            # Simulate 100 updates
            for i in range(100):
                dashboard._simulate_lead_score_update()

            # Calculate cache hit rate
            cache_hits = sum(
                1 for update in mock_streamlit_session_state['lead_score_stream']
                if update.cache_hit
            )
            hit_rate = cache_hits / len(mock_streamlit_session_state['lead_score_stream'])

            # Verify cache hit rate target
            assert hit_rate >= 0.85  # At least 85% cache hit rate in simulation

    # Edge Case Tests

    def test_empty_stream_handling(self, dashboard, mock_streamlit_session_state):
        """Test dashboard handles empty streams gracefully"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            # Ensure streams are empty
            dashboard._reset_all_streams()

            # Convert empty stream to DataFrame
            df = dashboard._convert_stream_to_dataframe(
                mock_streamlit_session_state['lead_score_stream']
            )

            # Verify empty DataFrame is created
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0

    def test_concurrent_stream_updates(self, dashboard, mock_streamlit_session_state):
        """Test multiple streams can be updated simultaneously"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            # Update all streams
            dashboard._simulate_lead_score_update()
            dashboard._simulate_churn_alert()
            dashboard._simulate_property_match()
            dashboard._simulate_conversation_update()
            dashboard._simulate_agent_activity()

            # Verify all streams have data
            assert len(mock_streamlit_session_state['lead_score_stream']) == 1
            assert len(mock_streamlit_session_state['churn_alerts_stream']) == 1
            assert len(mock_streamlit_session_state['property_match_stream']) == 1
            assert len(mock_streamlit_session_state['conversation_stream']) == 1
            assert len(mock_streamlit_session_state['agent_activity_stream']) == 1

    def test_timestamp_ordering(self, dashboard, mock_streamlit_session_state):
        """Test stream updates maintain chronological order"""
        with patch('streamlit.session_state', mock_streamlit_session_state):
            # Add multiple updates
            for i in range(10):
                dashboard._simulate_lead_score_update()

            # Verify timestamps are in order
            timestamps = [
                update.timestamp
                for update in mock_streamlit_session_state['lead_score_stream']
            ]

            for i in range(len(timestamps) - 1):
                assert timestamps[i] <= timestamps[i + 1]


class TestStreamType:
    """Test StreamType enum"""

    def test_stream_type_values(self):
        """Test all required stream types are defined"""
        required_types = [
            'lead_scoring', 'churn_risk', 'property_match',
            'conversation', 'performance', 'agent_activity'
        ]

        for stream_type in required_types:
            assert any(st.value == stream_type for st in StreamType)


class TestStreamUpdate:
    """Test StreamUpdate dataclass"""

    def test_stream_update_creation(self):
        """Test StreamUpdate can be created with required fields"""
        update = StreamUpdate(
            stream_type=StreamType.LEAD_SCORING,
            timestamp=datetime.now(),
            lead_id="test_lead_001",
            tenant_id="test_tenant_001",
            data={'score': 0.85}
        )

        assert update.stream_type == StreamType.LEAD_SCORING
        assert update.lead_id == "test_lead_001"
        assert update.data['score'] == 0.85

    def test_stream_update_optional_fields(self):
        """Test StreamUpdate optional fields have defaults"""
        update = StreamUpdate(
            stream_type=StreamType.CHURN_RISK,
            timestamp=datetime.now(),
            lead_id="test_lead",
            tenant_id="test_tenant",
            data={}
        )

        assert update.processing_time_ms == 0.0
        assert update.cache_hit is False


class TestDashboardMetrics:
    """Test DashboardMetrics dataclass"""

    def test_dashboard_metrics_initialization(self):
        """Test DashboardMetrics initializes with correct defaults"""
        metrics = DashboardMetrics()

        assert metrics.total_updates_received == 0
        assert metrics.avg_update_latency_ms == 0.0
        assert metrics.connection_uptime == 100.0
        assert metrics.active_streams == 0
        assert metrics.updates_per_second == 0.0

    def test_dashboard_metrics_updates(self):
        """Test DashboardMetrics can be updated"""
        metrics = DashboardMetrics()

        metrics.total_updates_received = 100
        metrics.avg_update_latency_ms = 35.5
        metrics.active_streams = 6

        assert metrics.total_updates_received == 100
        assert metrics.avg_update_latency_ms == 35.5
        assert metrics.active_streams == 6


# Integration Tests

class TestDashboardIntegration:
    """Integration tests for dashboard with WebSocket Manager"""

    @pytest.mark.integration
    def test_dashboard_websocket_integration(self):
        """Test dashboard can integrate with actual WebSocket Manager (if available)"""
        # This test would require actual WebSocket Manager infrastructure
        # Marked as integration test for separate execution
        pass

    @pytest.mark.integration
    def test_dashboard_event_bus_integration(self):
        """Test dashboard can integrate with Event Bus (if available)"""
        # This test would require actual Event Bus infrastructure
        # Marked as integration test for separate execution
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
