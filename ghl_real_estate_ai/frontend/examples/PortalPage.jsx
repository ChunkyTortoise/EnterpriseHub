import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { RefreshCw, Sparkles } from 'lucide-react';
import SwipeDeck from '../components/portal/SwipeDeck';
import '../styles/lyrio-theme.css';

const PortalPage = ({ leadId, locationId }) => {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deckInfo, setDeckInfo] = useState(null);

  const loadSmartDeck = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/portal/deck/${leadId}`, {
        params: { location_id: locationId, limit: 10, min_score: 0.5 },
      });
      setProperties(response.data.properties || []);
      setDeckInfo({
        seenCount: response.data.seen_count || 0,
        totalMatches: response.data.total_matches || 0,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load your matches right now.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSmartDeck();
  }, [leadId, locationId]);

  if (loading) {
    return (
      <div className="lyrio-portal-shell min-h-screen flex items-center justify-center px-4">
        <div className="rounded-2xl border p-6 max-w-md w-full" style={{ borderColor: 'var(--lyr-color-border)', background: 'var(--lyr-color-surface)' }}>
          <p className="lyrio-heading text-xl m-0">Curating your matches</p>
          <p className="text-sm mt-2 mb-0" style={{ color: 'var(--lyr-color-text-muted)' }}>Our AI is ranking homes around your preferences.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="lyrio-portal-shell min-h-screen flex items-center justify-center px-4">
        <div className="rounded-2xl border p-6 max-w-md w-full" style={{ borderColor: 'var(--lyr-color-border)', background: 'var(--lyr-color-surface)' }}>
          <p className="lyrio-heading text-xl m-0">Unable to load matches</p>
          <p className="text-sm mt-2" style={{ color: 'var(--lyr-color-text-muted)' }}>{error}</p>
          <button onClick={loadSmartDeck} className="lyrio-focus rounded-xl px-4 py-2 text-sm font-semibold border" style={{ borderColor: 'var(--lyr-color-border)' }}>
            <RefreshCw size={14} className="inline mr-2" />Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="lyrio-portal-shell min-h-screen px-4 py-6">
      <header className="max-w-5xl mx-auto mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="lyrio-heading text-2xl sm:text-3xl m-0">Your Daily Matches</h1>
          <p className="text-sm m-0" style={{ color: 'var(--lyr-color-text-muted)' }}>Curated for your goals and budget.</p>
        </div>
        <div className="lyrio-chip flex items-center gap-2">
          <Sparkles size={14} />
          {deckInfo?.totalMatches || properties.length} matches
          <span style={{ color: 'var(--lyr-color-text-muted)' }}>• {deckInfo?.seenCount || 0} reviewed</span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto">
        <SwipeDeck
          properties={properties}
          leadId={leadId}
          locationId={locationId}
          apiBaseUrl="/api"
          onComplete={() => setTimeout(loadSmartDeck, 800)}
          onError={(swipeError) => setError(swipeError.message)}
        />
      </main>
    </div>
  );
};

export default PortalPage;
