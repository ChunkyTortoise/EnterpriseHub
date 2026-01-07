/**
 * Example App.jsx
 * 
 * Complete working example of the Portal Swipe interface.
 * Copy this file to your React project and customize as needed.
 */

import React, { useState, useEffect } from 'react';
import SwipeDeck from '../components/portal/SwipeDeck';
import { mockProperties, mockLead } from '../utils/mockData';

function App() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lead, setLead] = useState(null);

  useEffect(() => {
    // Simulate fetching data
    // In production, replace with real API calls
    setTimeout(() => {
      setProperties(mockProperties);
      setLead(mockLead);
      setLoading(false);
    }, 500);
  }, []);

  const handleComplete = () => {
    console.log('All properties reviewed!');
    // Redirect to next step or show completion screen
    alert('🎉 You\'ve reviewed all available properties! We\'ll send you new listings as they arrive.');
  };

  const handleError = (error) => {
    console.error('Swipe error:', error);
    // Show error message to user
    alert('Something went wrong. Please refresh the page and try again.');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading properties...</p>
        </div>
      </div>
    );
  }

  if (!lead || properties.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-6xl mb-4">🏠</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            No Properties Available
          </h2>
          <p className="text-gray-600 mb-6">
            We're searching for homes that match your preferences.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm py-4 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Find Your Dream Home
            </h1>
            <p className="text-sm text-gray-600">
              Swipe right to like, left to pass
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Welcome back,</p>
            <p className="font-semibold text-gray-900">{lead.name}</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex items-center justify-center py-8 px-4">
        <SwipeDeck 
          properties={properties}
          leadId={lead.id}
          locationId={lead.location_id}
          apiBaseUrl={process.env.REACT_APP_API_URL || '/api'}
          onComplete={handleComplete}
          onError={handleError}
        />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t py-4 px-6 mt-8">
        <div className="max-w-7xl mx-auto text-center text-sm text-gray-600">
          <p>Having trouble? <a href="/support" className="text-blue-600 hover:underline">Contact Support</a></p>
        </div>
      </footer>
    </div>
  );
}

export default App;
