import React, { useEffect, useState } from 'react';
import SwipeDeck from '../components/portal/SwipeDeck';
import { mockLead, mockProperties } from '../utils/mockData';
import '../styles/lyrio-theme.css';

function App() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lead, setLead] = useState(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setProperties(mockProperties);
      setLead(mockLead);
      setLoading(false);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div className="lyrio-portal-shell min-h-screen flex items-center justify-center">
        <p className="lyrio-heading text-xl">Preparing your personalized deck...</p>
      </div>
    );
  }

  if (!lead || properties.length === 0) {
    return (
      <div className="lyrio-portal-shell min-h-screen flex items-center justify-center p-4">
        <div className="rounded-2xl border p-6 text-center" style={{ borderColor: 'var(--lyr-color-border)', background: 'var(--lyr-color-surface)' }}>
          <h2 className="lyrio-heading text-2xl m-0">No listings available</h2>
          <p className="text-sm mt-2 mb-4" style={{ color: 'var(--lyr-color-text-muted)' }}>
            We are still matching inventory to your preferences.
          </p>
          <button className="lyrio-focus rounded-xl px-4 py-2 text-sm font-semibold border" style={{ borderColor: 'var(--lyr-color-border)' }} onClick={() => window.location.reload()}>
            Refresh
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="lyrio-portal-shell min-h-screen px-4 py-6">
      <header className="max-w-5xl mx-auto mb-6">
        <h1 className="lyrio-heading text-3xl m-0">Lyrio Buyer Portal</h1>
        <p className="text-sm m-0" style={{ color: 'var(--lyr-color-text-muted)' }}>
          Welcome back, {lead.name}. Swipe to refine your daily match feed.
        </p>
      </header>
      <main className="max-w-5xl mx-auto">
        <SwipeDeck
          properties={properties}
          leadId={lead.id}
          locationId={lead.location_id}
          apiBaseUrl={process.env.REACT_APP_API_URL || '/api'}
          onComplete={() => alert('You are all caught up. We will notify you when new matches arrive.')}
          onError={(error) => alert(error?.message || 'Something went wrong during swipe sync.')}
        />
      </main>
    </div>
  );
}

export default App;
