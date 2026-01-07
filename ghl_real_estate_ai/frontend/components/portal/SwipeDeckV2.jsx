import React, { useState, useEffect } from 'react';
import axios from 'axios';
// Note: Ensure these components exist in your project or replace with standard HTML/CSS
// import { Card, CardContent } from '@/components/ui/card'; 
// import { Button } from '@/components/ui/button';
import { Loader2, ThumbsUp, ThumbsDown, Info } from 'lucide-react';

// CONFIG: Point this to your FastAPI Backend (Railway URL later, localhost now)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const SwipeDeck = ({ contactId }) => {
  const [properties, setProperties] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 1. Fetch the Personalized Deck on Mount
  useEffect(() => {
    if (!contactId) return;

    const fetchDeck = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/portal/deck`, {
          params: { contact_id: contactId }
        });
        setProperties(response.data.deck || []);
      } catch (err) {
        console.error("Failed to load deck:", err);
        setError("Could not load properties. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchDeck();
  }, [contactId]);

  // 2. Handle Swipe Action (Like/Pass)
  const handleSwipe = async (direction) => {
    if (currentIndex >= properties.length) return;

    const currentProperty = properties[currentIndex];
    const action = direction === 'right' ? 'like' : 'pass';

    // Optimistic UI Update: Move to next card immediately
    setCurrentIndex((prev) => prev + 1);

    try {
      // 3. Fire & Forget to Backend (Triple-Action Trigger)
      await axios.post(`${API_BASE_URL}/portal/swipe`, {
        contact_id: contactId,
        property_id: currentProperty.id,
        action: action
      });
      console.log(`Swiped ${action} on ${currentProperty.address}`);
    } catch (err) {
      console.error("Swipe failed to sync:", err);
    }
  };

  if (!contactId) return <div className="text-center p-10">Missing Contact ID</div>;
  if (loading) return <div className="flex justify-center p-10"><Loader2 className="animate-spin" /></div>;
  if (error) return <div className="text-red-500 text-center p-10">{error}</div>;

  if (currentIndex >= properties.length) {
    return (
      <div className="text-center p-10 bg-gray-50 rounded-xl">
        <h3 className="text-xl font-bold mb-2">All Caught Up!</h3>
        <p className="text-gray-600">We'll notify you when new matches arrive.</p>
      </div>
    );
  }

  const property = properties[currentIndex];

  return (
    <div className="max-w-md mx-auto p-4">
      <div className="bg-white overflow-hidden shadow-xl rounded-2xl h-[500px] flex flex-col relative border border-gray-200">
        {/* Image Section */}
        <div className="h-2/3 bg-gray-200 relative">
          <img 
            src={property.image_url || '/placeholder-house.jpg'} 
            alt={property.address}
            className="w-full h-full object-cover"
          />
          <div className="absolute bottom-2 left-2 bg-black/60 text-white px-3 py-1 rounded-full text-sm font-semibold">
            ${property.price?.toLocaleString()}
          </div>
        </div>

        {/* Info Section */}
        <div className="flex-1 p-5 flex flex-col justify-between">
          <div>
            <h2 className="text-xl font-bold truncate">{property.address}</h2>
            <div className="flex items-center gap-2 text-gray-500 text-sm mt-1">
              <span>{property.beds} Beds</span> • 
              <span>{property.baths} Baths</span> • 
              <span>{property.sqft} Sqft</span>
            </div>
            <p className="text-gray-600 text-sm mt-3 line-clamp-2">
              {property.description}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-between items-center mt-4 gap-4">
            <button 
              className="rounded-full w-14 h-14 border-2 border-red-500 text-red-500 hover:bg-red-50 flex items-center justify-center transition-colors"
              onClick={() => handleSwipe('left')}
            >
              <ThumbsDown size={24} />
            </button>
            
            <button 
              className="text-gray-400 flex items-center gap-1 text-sm hover:text-gray-600 transition-colors"
              onClick={() => window.open(property.link, '_blank')}
            >
              <Info size={18} /> Details
            </button>

            <button 
              className="rounded-full w-14 h-14 bg-green-600 hover:bg-green-700 text-white shadow-lg flex items-center justify-center transition-colors"
              onClick={() => handleSwipe('right')}
            >
              <ThumbsUp size={24} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SwipeDeck;
