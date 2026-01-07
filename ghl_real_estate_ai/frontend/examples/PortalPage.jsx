/**
 * PortalPage.jsx
 * 
 * Complete example showing how to fetch and display the Smart Deck.
 * This transforms the portal from static to DYNAMIC, AI-powered recommendations.
 */

import React, { useEffect, useState } from 'react';
import SwipeDeck from '../components/portal/SwipeDeck';
import axios from 'axios';
import { RefreshCw, Zap } from 'lucide-react';

const PortalPage = ({ leadId, locationId }) => {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deckInfo, setDeckInfo] = useState(null);

  const loadSmartDeck = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch the Smart Deck from Python backend
      const response = await axios.get(
        `/api/portal/deck/${leadId}`,
        {
          params: {
            location_id: locationId,
            limit: 10,
            min_score: 0.5
          }
        }
      );
      
      setProperties(response.data.properties);
      setDeckInfo({
        seenCount: response.data.seen_count,
        totalMatches: response.data.total_matches,
        preferences: response.data.preferences_applied
      });
      
      console.log('Smart deck loaded:', response.data);
      
    } catch (err) {
      console.error("Error loading smart deck:", err);
      setError(err.response?.data?.detail || "Failed to load properties");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSmartDeck();
  }, [leadId, locationId]);

  // Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            Finding your perfect matches...
          </h2>
          <p className="text-gray-600">
            Our AI is curating properties just for you
          </p>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">😕</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Oops! Something went wrong
          </h2>
          <p className="text-gray-600 mb-6">
            {error}
          </p>
          <button
            onClick={loadSmartDeck}
            className="px-6 py-3 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition-colors flex items-center gap-2 mx-auto"
          >
            <RefreshCw size={20} />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Empty State - All Caught Up!
  if (properties.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            You're all caught up!
          </h2>
          <p className="text-gray-600 mb-2">
            You've reviewed all available properties that match your preferences.
          </p>
          {deckInfo && deckInfo.seenCount > 0 && (
            <p className="text-sm text-gray-500 mb-6">
              You've seen {deckInfo.seenCount} {deckInfo.seenCount === 1 ? 'property' : 'properties'} so far
            </p>
          )}
          <div className="bg-blue-50 border-2 border-blue-200 rounded-2xl p-6 mb-6">
            <Zap size={32} className="text-blue-600 mx-auto mb-3" />
            <p className="text-blue-800 font-semibold mb-2">
              We'll text you when new matches hit the market!
            </p>
            <p className="text-sm text-blue-600">
              Our AI is constantly searching for homes that fit your preferences.
            </p>
          </div>
          <button
            onClick={loadSmartDeck}
            className="px-6 py-3 bg-gray-200 text-gray-700 rounded-full font-semibold hover:bg-gray-300 transition-colors flex items-center gap-2 mx-auto"
          >
            <RefreshCw size={18} />
            Check for new properties
          </button>
        </div>
      </div>
    );
  }

  // Main Portal View
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm py-4 px-6 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Zap size={24} className="text-blue-600" />
              Your Daily Matches
            </h1>
            <p className="text-sm text-gray-600">
              Curated by AI based on your preferences
            </p>
          </div>
          
          {/* Stats Badge */}
          {deckInfo && (
            <div className="text-right">
              <div className="bg-blue-50 px-4 py-2 rounded-full">
                <p className="text-xs text-blue-600 font-semibold">
                  {deckInfo.totalMatches} NEW {deckInfo.totalMatches === 1 ? 'MATCH' : 'MATCHES'}
                </p>
              </div>
              {deckInfo.seenCount > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  {deckInfo.seenCount} reviewed
                </p>
              )}
            </div>
          )}
        </div>
      </header>

      {/* AI Learning Indicator (if preferences are being applied) */}
      {deckInfo && deckInfo.preferences && Object.keys(deckInfo.preferences).length > 0 && (
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-start gap-3">
            <Zap size={20} className="text-green-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-green-800 mb-1">
                AI Learning Active
              </p>
              <p className="text-xs text-green-700">
                We're showing you homes based on your feedback.
                {deckInfo.preferences.budget && (
                  <span> Budget: ${deckInfo.preferences.budget.toLocaleString()}</span>
                )}
                {deckInfo.preferences.bedrooms && (
                  <span> • {deckInfo.preferences.bedrooms}+ bedrooms</span>
                )}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Swipe Deck */}
      <main className="flex items-center justify-center py-8 px-4">
        <SwipeDeck 
          properties={properties}
          leadId={leadId}
          locationId={locationId}
          apiBaseUrl={process.env.REACT_APP_API_URL || '/api'}
          onComplete={() => {
            console.log('Deck completed! Reloading...');
            // Reload deck after completion
            setTimeout(loadSmartDeck, 1000);
          }}
          onError={(error) => {
            console.error('Swipe error:', error);
            setError(error.message);
          }}
        />
      </main>

      {/* Footer Info */}
      <footer className="bg-white border-t py-4 px-6 mt-8">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-sm text-gray-600 mb-2">
            💡 <strong>Tip:</strong> The more you swipe, the smarter our recommendations become
          </p>
          <div className="flex items-center justify-center gap-4 text-xs text-gray-500">
            <span>✓ Learns from your feedback</span>
            <span>✓ No duplicate properties</span>
            <span>✓ Updated daily</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PortalPage;
