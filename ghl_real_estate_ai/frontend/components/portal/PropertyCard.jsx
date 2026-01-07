import React from 'react';
import { Heart, MapPin, Bed, Bath, Square } from 'lucide-react';

/**
 * PropertyCard Component
 * 
 * The "Visual Hook" - shows only what matters in a clean, magazine-style layout.
 * Designed to be mobile-first and thumb-friendly.
 * 
 * Key Design Decisions:
 * - Hero image takes 100% to create emotional connection
 * - Price is the LARGEST element (primary decision factor)
 * - Monthly payment is highlighted in green (affordability signal)
 * - Gradient overlay ensures text readability
 * - Minimal info to reduce cognitive load
 */
const PropertyCard = ({ property }) => {
  // Calculate estimated monthly payment (simplified formula)
  const calculateMonthlyPayment = (price) => {
    // Assuming 20% down, 7% interest, 30 years
    const principal = price * 0.8;
    const monthlyRate = 0.07 / 12;
    const numPayments = 30 * 12;
    const payment = principal * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
                    (Math.pow(1 + monthlyRate, numPayments) - 1);
    return Math.round(payment);
  };

  const estPayment = property.est_payment || calculateMonthlyPayment(property.price);

  return (
    <div className="relative w-full h-[600px] sm:h-[650px] bg-white rounded-3xl shadow-2xl overflow-hidden select-none">
      {/* Main Image */}
      <img 
        src={property.image_url || property.photos?.[0] || '/placeholder-property.jpg'} 
        alt={property.address} 
        className="w-full h-full object-cover pointer-events-none"
        draggable="false"
      />
      
      {/* Gradient Overlay - ensures text readability */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />

      {/* Top Badge (Optional: Status) */}
      {property.status && (
        <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm px-3 py-1 rounded-full">
          <span className="text-xs font-semibold text-gray-800 uppercase">
            {property.status}
          </span>
        </div>
      )}

      {/* Info Content - Bottom Card */}
      <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
        {/* Price Section */}
        <div className="flex justify-between items-end mb-3">
          <div>
            <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-1">
              ${(property.price || 0).toLocaleString()}
            </h2>
            <div className="flex items-center gap-2">
              <p className="text-green-400 font-semibold text-lg">
                ~${estPayment.toLocaleString()}/mo
              </p>
              <span className="text-xs text-gray-400">est.</span>
            </div>
          </div>
          
          {/* Property Stats */}
          <div className="text-right">
            <div className="flex items-center gap-3 justify-end mb-1">
              <div className="flex items-center gap-1">
                <Bed size={18} />
                <span className="text-xl font-bold">{property.beds || property.bedrooms || 0}</span>
              </div>
              <div className="flex items-center gap-1">
                <Bath size={18} />
                <span className="text-xl font-bold">{property.baths || property.bathrooms || 0}</span>
              </div>
            </div>
            <div className="flex items-center gap-1 justify-end text-gray-300">
              <Square size={14} />
              <span className="text-sm">{(property.sqft || property.square_feet || 0).toLocaleString()} sqft</span>
            </div>
          </div>
        </div>

        {/* Address */}
        <div className="flex items-start gap-2 mb-2">
          <MapPin size={16} className="text-gray-400 mt-1 flex-shrink-0" />
          <p className="text-gray-200 text-sm leading-snug">
            {property.address || 'Address not available'}
            {property.city && `, ${property.city}`}
            {property.state && `, ${property.state}`}
          </p>
        </div>

        {/* Property Type Badge */}
        {property.property_type && (
          <div className="inline-block">
            <span className="text-xs px-2 py-1 bg-white/20 backdrop-blur-sm rounded-full text-gray-200">
              {property.property_type}
            </span>
          </div>
        )}
      </div>

      {/* Swipe Hint (Optional - can be removed after first use) */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none">
        <div className="flex gap-8 opacity-0 animate-fade-in-delay">
          <div className="text-center">
            <div className="text-4xl mb-2">👈</div>
            <p className="text-white text-sm font-semibold bg-black/50 px-3 py-1 rounded-full">
              Pass
            </p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-2">👉</div>
            <p className="text-white text-sm font-semibold bg-black/50 px-3 py-1 rounded-full">
              Like
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertyCard;
