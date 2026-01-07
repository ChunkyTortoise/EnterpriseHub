import React, { useState, useEffect, useRef } from 'react';
import TinderCard from 'react-tinder-card';
import PropertyCard from './PropertyCard';
import FeedbackModal from './FeedbackModal';
import { Heart, X, RotateCcw, Zap } from 'lucide-react';
import axios from 'axios';

/**
 * SwipeDeck Component
 * 
 * The "Engine" that connects UI to Python backend.
 * Handles swipe gestures, feedback collection, and high-intent alerts.
 * 
 * Features:
 * - Tinder-style card stack with gesture controls
 * - Manual like/pass buttons for desktop users
 * - High-intent detection with visual feedback
 * - Tracks time spent on each card
 * - Integrates with backend /api/portal/swipe endpoint
 */
const SwipeDeck = ({ 
  properties, 
  leadId, 
  locationId,
  apiBaseUrl = '/api', 
  onComplete,
  onError 
}) => {
  const [currentIndex, setCurrentIndex] = useState(properties.length - 1);
  const [lastDirection, setLastDirection] = useState();
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [currentPassProperty, setCurrentPassProperty] = useState(null);
  const [highIntentAlert, setHighIntentAlert] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  
  // Track time spent on card
  const cardStartTime = useRef(Date.now());
  const childRefs = useRef(properties.map(() => React.createRef()));

  useEffect(() => {
    // Reset timer when card changes
    cardStartTime.current = Date.now();
  }, [currentIndex]);

  // Calculate time spent on current card
  const getTimeOnCard = () => {
    return (Date.now() - cardStartTime.current) / 1000; // seconds
  };

  // Handle the physical swipe gesture
  const onSwipe = (direction, propertyId) => {
    console.log(`Swiped ${direction} on property ${propertyId}`);
    setLastDirection(direction);
    
    const property = properties.find(p => p.id === propertyId);
    const timeOnCard = getTimeOnCard();
    
    if (direction === 'left') {
      // LEFT = PASS - Collect feedback first
      setCurrentPassProperty({ ...property, timeOnCard });
      setShowFeedbackModal(true);
    } else if (direction === 'right') {
      // RIGHT = LIKE - Immediate submission
      handleInteraction(property, 'like', null, timeOnCard);
      setLikeCount(prev => prev + 1);
    }
  };

  // Handle card leaving screen
  const onCardLeftScreen = (propertyId) => {
    console.log(`Property ${propertyId} left the screen`);
    setCurrentIndex(prevIndex => prevIndex - 1);
  };

  // Submit interaction to backend
  const handleInteraction = async (property, action, feedbackCategory = null, timeOnCard = null) => {
    if (isProcessing) return;
    
    setIsProcessing(true);
    
    try {
      const payload = {
        lead_id: leadId,
        property_id: property.id || property.property_id,
        action: action, // 'like' or 'pass'
        location_id: locationId,
        time_on_card: timeOnCard || getTimeOnCard(),
        feedback: feedbackCategory ? { category: feedbackCategory } : null
      };

      console.log('Submitting swipe:', payload);

      // Call Python Backend
      const response = await axios.post(`${apiBaseUrl}/portal/swipe`, payload);

      console.log('Swipe response:', response.data);

      // Check for High Intent Flag from Backend
      if (response.data.trigger_sms || response.data.high_intent) {
        setHighIntentAlert(true);
        
        // Auto-hide alert after 5 seconds
        setTimeout(() => setHighIntentAlert(false), 5000);
      }

      // If preferences were adjusted, log it
      if (response.data.adjustments && response.data.adjustments.length > 0) {
        console.log('Preferences adjusted:', response.data.adjustments);
      }

    } catch (error) {
      console.error("Failed to log swipe:", error);
      if (onError) {
        onError(error);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle feedback modal submission
  const onFeedbackSubmit = (feedbackCategory) => {
    if (currentPassProperty) {
      handleInteraction(
        currentPassProperty, 
        'pass', 
        feedbackCategory,
        currentPassProperty.timeOnCard
      );
    }
    setShowFeedbackModal(false);
    setCurrentPassProperty(null);
  };

  // Manual swipe (for desktop users or accessibility)
  const swipe = async (dir) => {
    if (currentIndex >= 0 && currentIndex < properties.length) {
      await childRefs.current[currentIndex].current.swipe(dir);
    }
  };

  // Check if all cards are swiped
  useEffect(() => {
    if (currentIndex < 0 && onComplete) {
      onComplete();
    }
  }, [currentIndex, onComplete]);

  const canSwipe = currentIndex >= 0;

  return (
    <div className="relative w-full max-w-md mx-auto h-[700px] sm:h-[750px] flex flex-col justify-center items-center">
      
      {/* High Intent Alert Banner */}
      {highIntentAlert && (
        <div className="absolute top-4 left-4 right-4 z-50 bg-gradient-to-r from-green-500 to-emerald-600 text-white px-6 py-4 rounded-2xl shadow-2xl animate-bounce flex items-center gap-3">
          <Zap size={24} className="text-yellow-300" />
          <div>
            <p className="font-bold text-lg">High Interest Detected! 🔥</p>
            <p className="text-sm text-green-100">We've notified your agent - expect a call soon!</p>
          </div>
        </div>
      )}

      {/* Card Stack Container */}
      <div className="card-container w-full h-[600px] sm:h-[650px] relative mb-6">
        {properties.map((property, index) => (
          <TinderCard
            ref={childRefs.current[index]}
            className="absolute inset-0 p-4"
            key={property.id || index}
            onSwipe={(dir) => onSwipe(dir, property.id || property.property_id)}
            onCardLeftScreen={() => onCardLeftScreen(property.id || property.property_id)}
            preventSwipe={['up', 'down']}
            swipeRequirementType="position"
            swipeThreshold={100}
          >
            <PropertyCard property={property} />
          </TinderCard>
        ))}

        {/* Empty State */}
        {!canSwipe && (
          <div className="absolute inset-0 flex items-center justify-center p-8">
            <div className="text-center">
              <div className="text-6xl mb-4">🎉</div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">
                All done!
              </h3>
              <p className="text-gray-600 mb-4">
                You've reviewed all available properties.
              </p>
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-3 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition-colors"
              >
                Show me more properties
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons (Desktop/Accessibility) */}
      {canSwipe && (
        <div className="flex gap-6 items-center justify-center">
          {/* Pass Button */}
          <button
            onClick={() => swipe('left')}
            disabled={isProcessing}
            className="w-16 h-16 rounded-full bg-white shadow-lg flex items-center justify-center hover:bg-red-50 hover:scale-110 transition-all active:scale-95 disabled:opacity-50"
            aria-label="Pass on this property"
          >
            <X size={28} className="text-red-500" />
          </button>

          {/* Property Counter */}
          <div className="px-4 py-2 bg-gray-100 rounded-full">
            <span className="text-sm font-semibold text-gray-600">
              {currentIndex + 1} / {properties.length}
            </span>
          </div>

          {/* Like Button */}
          <button
            onClick={() => swipe('right')}
            disabled={isProcessing}
            className="w-16 h-16 rounded-full bg-white shadow-lg flex items-center justify-center hover:bg-green-50 hover:scale-110 transition-all active:scale-95 disabled:opacity-50"
            aria-label="Like this property"
          >
            <Heart size={28} className="text-green-500" />
          </button>
        </div>
      )}

      {/* Swipe Instructions (First time users) */}
      {canSwipe && currentIndex === properties.length - 1 && (
        <div className="absolute bottom-24 left-0 right-0 text-center pointer-events-none">
          <p className="text-sm text-gray-500 animate-pulse">
            Swipe left to pass • Swipe right to like
          </p>
        </div>
      )}

      {/* Feedback Modal */}
      <FeedbackModal 
        isOpen={showFeedbackModal} 
        onClose={() => {
          // If they close without feedback, submit pass without reason
          if (currentPassProperty) {
            handleInteraction(currentPassProperty, 'pass', null, currentPassProperty.timeOnCard);
          }
          setShowFeedbackModal(false);
          setCurrentPassProperty(null);
        }}
        onSubmit={onFeedbackSubmit} 
      />
    </div>
  );
};

export default SwipeDeck;
