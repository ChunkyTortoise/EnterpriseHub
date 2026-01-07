import React from 'react';
import { X, DollarSign, MapPin, Ruler, Home, Maximize2, Minimize2 } from 'lucide-react';

/**
 * FeedbackModal Component
 * 
 * Captures WHY a lead passed on a property, turning a negative signal into actionable data.
 * This is the "Intelligence Layer" that makes the AI smarter over time.
 * 
 * Features:
 * - Mobile-first design with slide-up animation
 * - Icon-based buttons for quick feedback
 * - Maps to backend FeedbackCategory enum
 * - Optional text feedback field (can be added)
 */
const FeedbackModal = ({ isOpen, onClose, onSubmit }) => {
  if (!isOpen) return null;

  const reasons = [
    { 
      id: 'price_too_high', 
      label: 'Too Expensive', 
      icon: <DollarSign size={20} />,
      color: 'hover:border-red-500 hover:bg-red-50'
    },
    { 
      id: 'location', 
      label: 'Bad Location', 
      icon: <MapPin size={20} />,
      color: 'hover:border-orange-500 hover:bg-orange-50'
    },
    { 
      id: 'size_too_small', 
      label: 'Too Small', 
      icon: <Minimize2 size={20} />,
      color: 'hover:border-blue-500 hover:bg-blue-50'
    },
    { 
      id: 'size_too_large', 
      label: 'Too Large', 
      icon: <Maximize2 size={20} />,
      color: 'hover:border-purple-500 hover:bg-purple-50'
    },
    { 
      id: 'style', 
      label: 'Wrong Style', 
      icon: <Home size={20} />,
      color: 'hover:border-green-500 hover:bg-green-50'
    },
    { 
      id: 'other', 
      label: 'Other', 
      icon: <Ruler size={20} />,
      color: 'hover:border-gray-500 hover:bg-gray-50'
    },
  ];

  return (
    <div 
      className="fixed inset-0 bg-black/80 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
      onClick={onClose}
    >
      <div 
        className="bg-white w-full sm:max-w-md sm:rounded-2xl rounded-t-3xl p-6 animate-slide-up shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900">
            Why didn't you like it?
          </h3>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Close"
          >
            <X size={20} className="text-gray-600" />
          </button>
        </div>
        
        {/* Subtitle */}
        <p className="text-sm text-gray-600 mb-4">
          Your feedback helps us show you better matches
        </p>

        {/* Feedback Options Grid */}
        <div className="grid grid-cols-2 gap-3">
          {reasons.map((reason) => (
            <button
              key={reason.id}
              onClick={() => onSubmit(reason.id)}
              className={`flex flex-col items-center justify-center p-4 border-2 border-gray-200 rounded-xl transition-all active:scale-95 ${reason.color}`}
            >
              <div className="mb-2 text-gray-600">{reason.icon}</div>
              <span className="text-sm font-medium text-gray-700 text-center">
                {reason.label}
              </span>
            </button>
          ))}
        </div>

        {/* Skip Option */}
        <button
          onClick={() => onSubmit(null)}
          className="w-full mt-4 py-3 text-sm text-gray-500 hover:text-gray-700 font-medium"
        >
          Skip feedback
        </button>
      </div>
    </div>
  );
};

export default FeedbackModal;
