'use client';

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import {
  HomeIcon,
  BuildingOffice2Icon,
  UserGroupIcon,
  MapPinIcon,
  NavigationIcon,
  PhoneIcon,
  EyeIcon,
  ClockIcon,
  BoltIcon,
  FireIcon,
  ChartBarIcon,
} from "@heroicons/react/24/outline";

import useLocationServices from "@/hooks/useLocationServices";

interface NearbyProperty {
  id: string;
  address: string;
  distance: number; // meters
  type: 'listing' | 'recent_sale' | 'lead_interest' | 'showing_scheduled';
  matchScore?: number;
  leadId?: string;
  leadName?: string;
  alertPriority: 'high' | 'medium' | 'low';
  price?: number;
  squareFootage?: number;
  bedrooms?: number;
  bathrooms?: number;
  daysOnMarket?: number;
  mlScore?: number;
  showingTime?: string;
  metadata: {
    neighborhood?: string;
    propertyType?: string;
    listingAgent?: string;
    lastActivity?: string;
    hotLeadMatch?: boolean;
    urgentAction?: boolean;
  };
}

interface NearbyPropertiesWidgetProps {
  maxProperties?: number;
  showFilters?: boolean;
  onPropertySelect?: (propertyId: string) => void;
  onNavigateToProperty?: (propertyId: string) => void;
  onCreateAlert?: (propertyId: string) => void;
}

export function NearbyPropertiesWidget({
  maxProperties = 5,
  showFilters = true,
  onPropertySelect,
  onNavigateToProperty,
  onCreateAlert,
}: NearbyPropertiesWidgetProps) {
  const {
    currentLocation,
    createPropertyGeofence,
    getComparableSales,
    isTracking,
  } = useLocationServices();

  const [properties, setProperties] = useState<NearbyProperty[]>([]);
  const [filter, setFilter] = useState<'all' | 'hot' | 'urgent' | 'nearby'>('all');
  const [isLoading, setIsLoading] = useState(false);
  const [sortBy, setSortBy] = useState<'distance' | 'price' | 'match_score'>('distance');

  // Mock properties data - in production, fetch from API based on currentLocation
  useEffect(() => {
    if (!currentLocation) return;

    const mockProperties: NearbyProperty[] = [
      {
        id: 'nearby-1',
        address: '1250 Brickell Avenue #2A',
        distance: 150,
        type: 'lead_interest',
        matchScore: 95,
        leadId: 'lead-sarah',
        leadName: 'Sarah Mitchell',
        alertPriority: 'high',
        price: 725000,
        squareFootage: 1200,
        bedrooms: 2,
        bathrooms: 2,
        daysOnMarket: 3,
        mlScore: 87,
        metadata: {
          neighborhood: 'Brickell',
          propertyType: 'Luxury Condo',
          hotLeadMatch: true,
          urgentAction: true,
          lastActivity: '2 hours ago',
        },
      },
      {
        id: 'nearby-2',
        address: '1180 Brickell Avenue #15B',
        distance: 250,
        type: 'listing',
        alertPriority: 'medium',
        price: 685000,
        squareFootage: 1100,
        bedrooms: 2,
        bathrooms: 2,
        daysOnMarket: 8,
        metadata: {
          neighborhood: 'Brickell',
          propertyType: 'Modern Condo',
          listingAgent: 'Maria Rodriguez',
          lastActivity: '1 day ago',
        },
      },
      {
        id: 'nearby-3',
        address: '1350 Brickell Avenue #10A',
        distance: 320,
        type: 'showing_scheduled',
        leadId: 'lead-david',
        leadName: 'David Kim',
        alertPriority: 'high',
        price: 780000,
        squareFootage: 1400,
        bedrooms: 3,
        bathrooms: 2,
        showingTime: '4:30 PM Today',
        metadata: {
          neighborhood: 'Brickell',
          propertyType: 'Penthouse',
          urgentAction: true,
          lastActivity: '30 minutes ago',
        },
      },
      {
        id: 'nearby-4',
        address: '1300 Brickell Avenue #8C',
        distance: 410,
        type: 'recent_sale',
        alertPriority: 'low',
        price: 650000,
        squareFootage: 950,
        bedrooms: 1,
        bathrooms: 1,
        daysOnMarket: 18,
        metadata: {
          neighborhood: 'Brickell',
          propertyType: 'Studio Plus',
          lastActivity: '12 days ago',
        },
      },
      {
        id: 'nearby-5',
        address: '1400 Brickell Avenue #5F',
        distance: 520,
        type: 'listing',
        matchScore: 78,
        alertPriority: 'medium',
        price: 695000,
        squareFootage: 1050,
        bedrooms: 2,
        bathrooms: 1,
        daysOnMarket: 15,
        mlScore: 72,
        metadata: {
          neighborhood: 'Brickell',
          propertyType: 'Classic Condo',
          listingAgent: 'Robert Chen',
          lastActivity: '3 hours ago',
        },
      },
    ];

    setProperties(mockProperties);
  }, [currentLocation]);

  // Filter and sort properties
  const filteredProperties = properties
    .filter(property => {
      switch (filter) {
        case 'hot':
          return property.matchScore && property.matchScore > 80;
        case 'urgent':
          return property.metadata.urgentAction;
        case 'nearby':
          return property.distance <= 300;
        default:
          return true;
      }
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'distance':
          return a.distance - b.distance;
        case 'price':
          return (b.price || 0) - (a.price || 0);
        case 'match_score':
          return (b.matchScore || 0) - (a.matchScore || 0);
        default:
          return a.distance - b.distance;
      }
    })
    .slice(0, maxProperties);

  const getPropertyTypeIcon = (type: string) => {
    switch (type) {
      case 'lead_interest':
      case 'showing_scheduled':
        return UserGroupIcon;
      case 'recent_sale':
        return BuildingOffice2Icon;
      case 'listing':
      default:
        return HomeIcon;
    }
  };

  const getPropertyTypeColor = (type: string, priority: string) => {
    if (priority === 'high') return 'text-red-400 bg-red-500/20';

    switch (type) {
      case 'lead_interest':
        return 'text-jorge-electric bg-jorge-electric/20';
      case 'showing_scheduled':
        return 'text-jorge-gold bg-jorge-gold/20';
      case 'recent_sale':
        return 'text-jorge-glow bg-jorge-glow/20';
      case 'listing':
      default:
        return 'text-blue-400 bg-blue-500/20';
    }
  };

  const getPropertyTypeLabel = (type: string) => {
    switch (type) {
      case 'lead_interest':
        return 'Lead Match';
      case 'showing_scheduled':
        return 'Showing';
      case 'recent_sale':
        return 'Recent Sale';
      case 'listing':
        return 'Active Listing';
      default:
        return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
  };

  const formatDistance = (distance: number) => {
    if (distance >= 1000) {
      return `${(distance / 1000).toFixed(1)}km`;
    }
    return `${Math.round(distance)}m`;
  };

  const handleCreateAlert = (property: NearbyProperty) => {
    if (!currentLocation) return;

    const alertType = property.type === 'lead_interest' ? 'hot_lead_match' :
                     property.type === 'showing_scheduled' ? 'showing_scheduled' :
                     property.type === 'listing' ? 'new_listing' : 'new_listing';

    createPropertyGeofence(
      property.id,
      { lat: currentLocation.lat + (Math.random() - 0.5) * 0.01, lng: currentLocation.lng + (Math.random() - 0.5) * 0.01 },
      alertType,
      {
        propertyAddress: property.address,
        leadId: property.leadId,
        leadName: property.leadName,
        listingPrice: property.price,
        propertyType: property.metadata.propertyType,
        mlScore: property.mlScore,
      },
      {
        radius: property.alertPriority === 'high' ? 300 : 200,
        priority: property.alertPriority,
      }
    );

    onCreateAlert?.(property.id);

    // Haptic feedback
    if ('vibrate' in navigator) {
      navigator.vibrate(100);
    }
  };

  const handleNavigateToProperty = (property: NearbyProperty) => {
    const url = `https://maps.google.com/maps?q=${encodeURIComponent(property.address)}`;
    window.open(url, '_blank');
    onNavigateToProperty?.(property.id);

    // Haptic feedback
    if ('vibrate' in navigator) {
      navigator.vibrate(50);
    }
  };

  if (!currentLocation || !isTracking) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-card text-center py-6"
      >
        <MapPinIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-sm text-gray-400 mb-2">
          {!currentLocation ? 'Location required for nearby properties' : 'Location tracking disabled'}
        </p>
        <p className="text-xs text-gray-500">
          Enable GPS tracking to discover properties around you
        </p>
      </motion.div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MapPinIcon className="w-5 h-5 text-jorge-electric" />
          <h2 className="jorge-heading text-lg">Nearby Properties</h2>
        </div>
        <div className="flex items-center gap-1 text-xs jorge-code text-gray-400">
          <BoltIcon className="w-3 h-3" />
          <span>{filteredProperties.length} FOUND</span>
        </div>
      </div>

      {/* Filters and Sorting */}
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-3"
        >
          {/* Filter Tabs */}
          <div className="flex bg-white/5 rounded-lg p-1">
            {[
              { id: 'all', label: 'All', count: properties.length },
              { id: 'hot', label: 'Hot Leads', count: properties.filter(p => p.matchScore && p.matchScore > 80).length },
              { id: 'urgent', label: 'Urgent', count: properties.filter(p => p.metadata.urgentAction).length },
              { id: 'nearby', label: '<300m', count: properties.filter(p => p.distance <= 300).length },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setFilter(tab.id as any)}
                className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-semibold transition-colors jorge-haptic ${
                  filter === tab.id
                    ? 'bg-jorge-electric/20 text-jorge-electric'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab.label}
                {tab.count > 0 && (
                  <span className="ml-1 text-xs opacity-75">({tab.count})</span>
                )}
              </button>
            ))}
          </div>

          {/* Sort Options */}
          <div className="flex gap-2">
            {[
              { id: 'distance', label: 'Distance', icon: MapPinIcon },
              { id: 'price', label: 'Price', icon: ChartBarIcon },
              { id: 'match_score', label: 'Match', icon: FireIcon },
            ].map(option => (
              <button
                key={option.id}
                onClick={() => setSortBy(option.id as any)}
                className={`flex items-center gap-1 px-3 py-1 rounded text-xs font-medium jorge-haptic ${
                  sortBy === option.id
                    ? 'bg-jorge-glow/20 text-jorge-glow'
                    : 'bg-white/5 text-gray-400'
                }`}
              >
                <option.icon className="w-3 h-3" />
                {option.label}
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Properties List */}
      <div className="space-y-3">
        {filteredProperties.length === 0 ? (
          <div className="jorge-card text-center py-6">
            <HomeIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-400">
              No properties found matching your filters
            </p>
            <button
              onClick={() => setFilter('all')}
              className="mt-2 px-3 py-1 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic"
            >
              Show All
            </button>
          </div>
        ) : (
          filteredProperties.map((property, index) => {
            const PropertyIcon = getPropertyTypeIcon(property.type);
            const colorClasses = getPropertyTypeColor(property.type, property.alertPriority);

            return (
              <motion.div
                key={property.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="jorge-card jorge-card-hover cursor-pointer relative"
                onClick={() => onPropertySelect?.(property.id)}
              >
                {/* Urgent/Hot Lead Badge */}
                {(property.metadata.urgentAction || property.metadata.hotLeadMatch) && (
                  <div className="absolute -top-1 -right-1 z-10">
                    <motion.div
                      animate={{ scale: [1, 1.1, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className={`w-3 h-3 rounded-full ${
                        property.metadata.hotLeadMatch ? 'bg-red-500' : 'bg-jorge-gold'
                      }`}
                    />
                  </div>
                )}

                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${colorClasses} flex-shrink-0`}>
                    <PropertyIcon className="w-4 h-4" />
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-white truncate">
                          {property.address}
                        </h4>
                        <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
                          <span className={colorClasses.split(' ')[0]}>
                            {getPropertyTypeLabel(property.type)}
                          </span>
                          <span>•</span>
                          <span>{formatDistance(property.distance)}</span>
                          {property.metadata.neighborhood && (
                            <>
                              <span>•</span>
                              <span>{property.metadata.neighborhood}</span>
                            </>
                          )}
                        </div>
                      </div>
                      {property.price && (
                        <div className="property-value text-sm ml-2">
                          ${(property.price / 1000).toFixed(0)}K
                        </div>
                      )}
                    </div>

                    {/* Lead Information */}
                    {property.leadName && (
                      <div className="flex items-center gap-2 mb-2 p-2 bg-jorge-electric/10 rounded text-xs">
                        <UserGroupIcon className="w-3 h-3 text-jorge-electric" />
                        <span className="text-jorge-electric font-medium">{property.leadName}</span>
                        {property.matchScore && (
                          <span className="ml-auto text-jorge-electric">
                            {property.matchScore}% match
                          </span>
                        )}
                      </div>
                    )}

                    {/* Showing Time */}
                    {property.showingTime && (
                      <div className="flex items-center gap-2 mb-2 p-2 bg-jorge-gold/10 rounded text-xs">
                        <ClockIcon className="w-3 h-3 text-jorge-gold" />
                        <span className="text-jorge-gold font-medium">
                          Showing: {property.showingTime}
                        </span>
                      </div>
                    )}

                    {/* Property Details */}
                    <div className="grid grid-cols-3 gap-3 text-xs mb-3">
                      {property.bedrooms && (
                        <div className="text-center">
                          <div className="text-white font-medium">{property.bedrooms}</div>
                          <div className="text-gray-400">Beds</div>
                        </div>
                      )}
                      {property.bathrooms && (
                        <div className="text-center">
                          <div className="text-white font-medium">{property.bathrooms}</div>
                          <div className="text-gray-400">Baths</div>
                        </div>
                      )}
                      {property.squareFootage && (
                        <div className="text-center">
                          <div className="text-white font-medium">
                            {property.squareFootage.toLocaleString()}
                          </div>
                          <div className="text-gray-400">SqFt</div>
                        </div>
                      )}
                    </div>

                    {/* ML Score and Days on Market */}
                    {(property.mlScore || property.daysOnMarket) && (
                      <div className="flex items-center gap-4 text-xs text-gray-400 mb-3">
                        {property.mlScore && (
                          <div className="flex items-center gap-1">
                            <BoltIcon className="w-3 h-3 text-jorge-electric" />
                            <span>ML Score: </span>
                            <span className="text-jorge-electric font-medium">{property.mlScore}/100</span>
                          </div>
                        )}
                        {property.daysOnMarket && (
                          <div className="flex items-center gap-1">
                            <ClockIcon className="w-3 h-3" />
                            <span>{property.daysOnMarket} days on market</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Last Activity */}
                    {property.metadata.lastActivity && (
                      <div className="text-xs text-gray-500 mb-3">
                        Last activity: {property.metadata.lastActivity}
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleNavigateToProperty(property);
                        }}
                        className="flex items-center justify-center gap-1 py-2 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic"
                      >
                        <NavigationIcon className="w-3 h-3" />
                        Navigate
                      </button>

                      {property.leadId ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            console.log('Call lead:', property.leadId);
                          }}
                          className="flex items-center justify-center gap-1 py-2 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic"
                        >
                          <PhoneIcon className="w-3 h-3" />
                          Call
                        </button>
                      ) : (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            console.log('View property details:', property.id);
                          }}
                          className="flex items-center justify-center gap-1 py-2 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic"
                        >
                          <EyeIcon className="w-3 h-3" />
                          View
                        </button>
                      )}

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCreateAlert(property);
                        }}
                        className="flex items-center justify-center gap-1 py-2 bg-jorge-gold/20 text-jorge-gold text-xs font-semibold rounded jorge-haptic"
                      >
                        <BoltIcon className="w-3 h-3" />
                        Alert
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>

      {/* Load More */}
      {properties.length > maxProperties && filteredProperties.length === maxProperties && (
        <button
          onClick={() => {
            // In production, load more properties from API
            console.log('Load more properties...');
          }}
          className="w-full py-3 text-xs jorge-code text-gray-400 hover:text-jorge-electric transition-colors border border-white/10 rounded-lg jorge-haptic"
        >
          LOAD MORE PROPERTIES →
        </button>
      )}
    </div>
  );
}