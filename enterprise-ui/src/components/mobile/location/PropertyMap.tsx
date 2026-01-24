'use client';

import { motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import {
  MapPinIcon,
  HomeIcon,
  BuildingOffice2Icon,
  UserGroupIcon,
  PhoneIcon,
  NavigationIcon,
  AdjustmentsHorizontalIcon,
  MagnifyingGlassIcon,
  LayersIcon,
  CompassIcon,
  CrosshairsIcon,
} from "@heroicons/react/24/outline";

import useLocationServices from "@/hooks/useLocationServices";

interface PropertyMapProps {
  initialCenter?: { lat: number; lng: number };
  initialZoom?: number;
  showControls?: boolean;
  onPropertySelect?: (propertyId: string) => void;
  onLocationChange?: (location: { lat: number; lng: number }) => void;
}

interface MapProperty {
  id: string;
  coordinates: { lat: number; lng: number };
  type: 'listing' | 'recent_sale' | 'lead_property' | 'hot_lead' | 'showing';
  title: string;
  subtitle: string;
  price?: number;
  distance: number;
  priority: 'high' | 'medium' | 'low';
  leadId?: string;
  alertActive?: boolean;
  metadata: {
    bedrooms?: number;
    bathrooms?: number;
    squareFootage?: number;
    daysOnMarket?: number;
    leadName?: string;
    showingTime?: string;
  };
}

interface MapLayer {
  id: string;
  name: string;
  visible: boolean;
  color: string;
  icon: React.ComponentType<any>;
}

export function PropertyMap({
  initialCenter,
  initialZoom = 15,
  showControls = true,
  onPropertySelect,
  onLocationChange,
}: PropertyMapProps) {
  const {
    currentLocation,
    activeGeofences,
    recentAlerts,
    marketInsight,
    createPropertyGeofence,
    getCurrentLocation,
    getComparableSales,
  } = useLocationServices();

  // Map state
  const [mapCenter, setMapCenter] = useState(
    initialCenter || { lat: 25.7617, lng: -80.1918 } // Default to Miami
  );
  const [zoom, setZoom] = useState(initialZoom);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<MapProperty | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Map layers
  const [layers, setLayers] = useState<MapLayer[]>([
    { id: 'listings', name: 'Active Listings', visible: true, color: 'jorge-glow', icon: HomeIcon },
    { id: 'sales', name: 'Recent Sales', visible: true, color: 'jorge-gold', icon: BuildingOffice2Icon },
    { id: 'leads', name: 'Lead Properties', visible: true, color: 'jorge-electric', icon: UserGroupIcon },
    { id: 'geofences', name: 'Alert Areas', visible: true, color: 'purple-400', icon: CompassIcon },
  ]);

  // Mock properties data - in production, fetch from API
  const [properties, setProperties] = useState<MapProperty[]>([
    {
      id: 'prop-1',
      coordinates: { lat: 25.7627, lng: -80.1907 },
      type: 'hot_lead',
      title: '1250 Brickell Ave #2A',
      subtitle: 'Sarah Mitchell - Hot Lead',
      price: 725000,
      distance: 150,
      priority: 'high',
      leadId: 'lead-sarah',
      alertActive: true,
      metadata: {
        bedrooms: 2,
        bathrooms: 2,
        squareFootage: 1200,
        leadName: 'Sarah Mitchell',
        showingTime: '2:00 PM',
      },
    },
    {
      id: 'prop-2',
      coordinates: { lat: 25.7607, lng: -80.1928 },
      type: 'listing',
      title: '1180 Brickell Ave #15B',
      subtitle: 'New Luxury Condo',
      price: 685000,
      distance: 200,
      priority: 'medium',
      metadata: {
        bedrooms: 2,
        bathrooms: 2,
        squareFootage: 1100,
        daysOnMarket: 5,
      },
    },
    {
      id: 'prop-3',
      coordinates: { lat: 25.7637, lng: -80.1897 },
      type: 'recent_sale',
      title: '1300 Brickell Ave #8C',
      subtitle: 'Sold 12 days ago',
      price: 650000,
      distance: 300,
      priority: 'low',
      metadata: {
        bedrooms: 1,
        bathrooms: 1,
        squareFootage: 950,
        daysOnMarket: 18,
      },
    },
    {
      id: 'prop-4',
      coordinates: { lat: 25.7647, lng: -80.1887 },
      type: 'showing',
      title: '1350 Brickell Ave #10A',
      subtitle: 'David Kim - Showing Today',
      price: 780000,
      distance: 400,
      priority: 'high',
      leadId: 'lead-david',
      metadata: {
        bedrooms: 3,
        bathrooms: 2,
        squareFootage: 1400,
        leadName: 'David Kim',
        showingTime: '4:30 PM',
      },
    },
  ]);

  const mapRef = useRef<HTMLDivElement>(null);

  // Update map center when current location changes
  useEffect(() => {
    if (currentLocation && !initialCenter) {
      setMapCenter({
        lat: currentLocation.lat,
        lng: currentLocation.lng,
      });
    }
  }, [currentLocation, initialCenter]);

  // Get current location and center map
  const centerOnCurrentLocation = async () => {
    setIsLoading(true);
    try {
      const location = await getCurrentLocation();
      setMapCenter({ lat: location.lat, lng: location.lng });
      setZoom(16);
    } catch (error) {
      console.error('Failed to get current location:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle property selection
  const handlePropertySelect = (property: MapProperty) => {
    setSelectedProperty(property);
    setMapCenter(property.coordinates);
    setZoom(17);
    onPropertySelect?.(property.id);

    // Haptic feedback
    if ('vibrate' in navigator) {
      navigator.vibrate(50);
    }
  };

  // Create geofence for property
  const handleCreateGeofence = (property: MapProperty) => {
    if (!property) return;

    const alertType = property.type === 'hot_lead' ? 'hot_lead_match' :
                     property.type === 'showing' ? 'showing_scheduled' :
                     property.type === 'listing' ? 'new_listing' : 'new_listing';

    createPropertyGeofence(
      property.id,
      property.coordinates,
      alertType,
      {
        propertyAddress: property.title,
        leadId: property.leadId,
        leadName: property.metadata.leadName,
        listingPrice: property.price,
        propertyType: property.type,
      },
      {
        radius: property.priority === 'high' ? 300 : 200,
        priority: property.priority,
      }
    );

    console.log(`Created geofence for ${property.title}`);
  };

  // Get property icon and color
  const getPropertyIcon = (type: string) => {
    switch (type) {
      case 'hot_lead':
      case 'lead_property':
        return UserGroupIcon;
      case 'showing':
        return PhoneIcon;
      case 'recent_sale':
        return BuildingOffice2Icon;
      case 'listing':
      default:
        return HomeIcon;
    }
  };

  const getPropertyColor = (type: string, priority: string) => {
    if (priority === 'high') return 'text-red-400 bg-red-500/20 border-red-500/30';

    switch (type) {
      case 'hot_lead':
      case 'lead_property':
        return 'text-jorge-electric bg-jorge-electric/20 border-jorge-electric/30';
      case 'showing':
        return 'text-jorge-gold bg-jorge-gold/20 border-jorge-gold/30';
      case 'recent_sale':
        return 'text-jorge-glow bg-jorge-glow/20 border-jorge-glow/30';
      case 'listing':
      default:
        return 'text-blue-400 bg-blue-500/20 border-blue-500/30';
    }
  };

  // Filter properties based on search and layer visibility
  const filteredProperties = properties.filter(property => {
    // Search filter
    if (searchTerm && !property.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !property.subtitle.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }

    // Layer filter
    const layerMap = {
      'listing': 'listings',
      'recent_sale': 'sales',
      'lead_property': 'leads',
      'hot_lead': 'leads',
      'showing': 'leads',
    };

    const layerId = layerMap[property.type as keyof typeof layerMap];
    const layer = layers.find(l => l.id === layerId);

    return layer?.visible !== false;
  });

  // Toggle layer visibility
  const toggleLayer = (layerId: string) => {
    setLayers(prev => prev.map(layer =>
      layer.id === layerId ? { ...layer, visible: !layer.visible } : layer
    ));
  };

  return (
    <div className="relative h-full flex flex-col">
      {/* Map Header */}
      {showControls && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-shrink-0 p-4 bg-jorge-dark/95 backdrop-blur border-b border-white/10"
        >
          <div className="flex items-center justify-between mb-3">
            <h2 className="jorge-heading text-lg">Property Map</h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`p-2 rounded-lg jorge-haptic ${
                  showFilters ? 'bg-jorge-electric/20 text-jorge-electric' : 'bg-white/10 text-gray-400'
                }`}
              >
                <LayersIcon className="w-4 h-4" />
              </button>
              <button
                onClick={centerOnCurrentLocation}
                disabled={isLoading}
                className="p-2 bg-jorge-glow/20 text-jorge-glow rounded-lg jorge-haptic disabled:opacity-50"
              >
                {isLoading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-4 h-4 border border-jorge-glow border-t-transparent rounded-full"
                  />
                ) : (
                  <CrosshairsIcon className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search properties, addresses, or leads..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/20 rounded-lg text-sm text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-jorge-electric/50"
            />
          </div>

          {/* Layer Controls */}
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-3 grid grid-cols-2 gap-2"
            >
              {layers.map(layer => {
                const IconComponent = layer.icon;
                return (
                  <button
                    key={layer.id}
                    onClick={() => toggleLayer(layer.id)}
                    className={`flex items-center gap-2 p-2 rounded-lg text-xs font-medium jorge-haptic ${
                      layer.visible
                        ? `bg-${layer.color}/20 text-${layer.color}`
                        : 'bg-white/5 text-gray-500'
                    }`}
                  >
                    <IconComponent className="w-3 h-3" />
                    {layer.name}
                  </button>
                );
              })}
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Map Container */}
      <div className="flex-1 relative overflow-hidden">
        <div
          ref={mapRef}
          className="w-full h-full bg-gradient-to-br from-jorge-dark via-gray-900 to-black relative"
        >
          {/* Mock Map Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-gray-800 to-gray-900">
            {/* Grid overlay for map effect */}
            <div className="absolute inset-0 opacity-10"
              style={{
                backgroundImage: `
                  linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
                `,
                backgroundSize: '20px 20px'
              }}
            />
          </div>

          {/* Current Location Indicator */}
          {currentLocation && (
            <motion.div
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10"
            >
              <div className="relative">
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="w-4 h-4 bg-jorge-electric rounded-full border-2 border-white shadow-lg"
                />
                <motion.div
                  animate={{ scale: [1, 2, 1], opacity: [0.6, 0, 0.6] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="absolute inset-0 bg-jorge-electric rounded-full"
                />
              </div>
            </motion.div>
          )}

          {/* Geofence Areas */}
          {layers.find(l => l.id === 'geofences')?.visible && activeGeofences.map(geofence => (
            <motion.div
              key={geofence.id}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 0.3, scale: 1 }}
              className="absolute border-2 border-purple-400 rounded-full pointer-events-none"
              style={{
                width: `${(geofence.radius / 10)}px`,
                height: `${(geofence.radius / 10)}px`,
                left: '50%',
                top: '50%',
                transform: `translate(${(geofence.center.lng - mapCenter.lng) * 1000}px, ${(mapCenter.lat - geofence.center.lat) * 1000}px) translate(-50%, -50%)`,
              }}
            />
          ))}

          {/* Property Markers */}
          {filteredProperties.map((property, index) => {
            const PropertyIcon = getPropertyIcon(property.type);
            const colorClasses = getPropertyColor(property.type, property.priority);

            // Calculate position relative to map center (mock positioning)
            const offsetX = (property.coordinates.lng - mapCenter.lng) * 1000;
            const offsetY = (mapCenter.lat - property.coordinates.lat) * 1000;

            return (
              <motion.div
                key={property.id}
                initial={{ opacity: 0, scale: 0, y: -50 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="absolute z-20"
                style={{
                  left: '50%',
                  top: '50%',
                  transform: `translate(${offsetX}px, ${offsetY}px) translate(-50%, -100%)`,
                }}
              >
                <button
                  onClick={() => handlePropertySelect(property)}
                  className={`relative group jorge-haptic`}
                >
                  {/* Alert Pulse for High Priority */}
                  {property.alertActive && property.priority === 'high' && (
                    <motion.div
                      animate={{ scale: [1, 1.5, 1], opacity: [0.8, 0, 0.8] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                      className="absolute inset-0 bg-red-500 rounded-full -m-2"
                    />
                  )}

                  {/* Marker */}
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${colorClasses} shadow-lg`}>
                    <PropertyIcon className="w-4 h-4" />
                  </div>

                  {/* Price Label */}
                  {property.price && (
                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/80 text-white text-xs font-semibold rounded whitespace-nowrap">
                      ${(property.price / 1000).toFixed(0)}K
                    </div>
                  )}

                  {/* Hover Info */}
                  <div className="absolute -bottom-20 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
                    <div className="px-3 py-2 bg-black/90 text-white text-xs rounded-lg whitespace-nowrap border border-white/20">
                      <div className="font-semibold">{property.title}</div>
                      <div className="text-gray-300">{property.subtitle}</div>
                      <div className="text-jorge-electric mt-1">{Math.round(property.distance)}m away</div>
                    </div>
                  </div>
                </button>
              </motion.div>
            );
          })}
        </div>

        {/* Map Controls */}
        <div className="absolute bottom-4 right-4 flex flex-col gap-2">
          <button
            onClick={() => setZoom(prev => Math.min(20, prev + 1))}
            className="w-10 h-10 bg-black/80 border border-white/20 text-white rounded-lg flex items-center justify-center jorge-haptic"
          >
            +
          </button>
          <button
            onClick={() => setZoom(prev => Math.max(10, prev - 1))}
            className="w-10 h-10 bg-black/80 border border-white/20 text-white rounded-lg flex items-center justify-center jorge-haptic"
          >
            −
          </button>
        </div>

        {/* Zoom Level Indicator */}
        <div className="absolute bottom-4 left-4 px-2 py-1 bg-black/80 border border-white/20 text-white text-xs rounded">
          Zoom: {zoom}
        </div>
      </div>

      {/* Selected Property Details */}
      {selectedProperty && (
        <motion.div
          initial={{ opacity: 0, y: 100 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-shrink-0 p-4 bg-jorge-dark/95 backdrop-blur border-t border-white/10"
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <h3 className="jorge-code text-sm font-medium text-white mb-1">
                {selectedProperty.title}
              </h3>
              <p className="text-xs text-gray-400">{selectedProperty.subtitle}</p>
              {selectedProperty.price && (
                <p className="property-value text-base mt-1">
                  ${selectedProperty.price.toLocaleString()}
                </p>
              )}
            </div>
            <button
              onClick={() => setSelectedProperty(null)}
              className="p-1 text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>

          {/* Property Details */}
          <div className="grid grid-cols-3 gap-3 mb-3 text-xs">
            {selectedProperty.metadata.bedrooms && (
              <div className="text-center">
                <div className="text-white font-medium">{selectedProperty.metadata.bedrooms}</div>
                <div className="text-gray-400">Beds</div>
              </div>
            )}
            {selectedProperty.metadata.bathrooms && (
              <div className="text-center">
                <div className="text-white font-medium">{selectedProperty.metadata.bathrooms}</div>
                <div className="text-gray-400">Baths</div>
              </div>
            )}
            {selectedProperty.metadata.squareFootage && (
              <div className="text-center">
                <div className="text-white font-medium">
                  {selectedProperty.metadata.squareFootage.toLocaleString()}
                </div>
                <div className="text-gray-400">SqFt</div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => {
                const url = `https://maps.google.com/maps?q=${selectedProperty.coordinates.lat},${selectedProperty.coordinates.lng}`;
                window.open(url, '_blank');
              }}
              className="flex items-center justify-center gap-1 py-2 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic"
            >
              <NavigationIcon className="w-3 h-3" />
              Navigate
            </button>

            {selectedProperty.leadId && (
              <button
                onClick={() => console.log('Call lead:', selectedProperty.leadId)}
                className="flex items-center justify-center gap-1 py-2 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic"
              >
                <PhoneIcon className="w-3 h-3" />
                Call
              </button>
            )}

            <button
              onClick={() => handleCreateGeofence(selectedProperty)}
              className="flex items-center justify-center gap-1 py-2 bg-jorge-gold/20 text-jorge-gold text-xs font-semibold rounded jorge-haptic"
            >
              <CompassIcon className="w-3 h-3" />
              Alert
            </button>
          </div>
        </motion.div>
      )}

      {/* Properties Summary */}
      {!selectedProperty && showControls && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex-shrink-0 p-4 bg-jorge-dark/95 backdrop-blur border-t border-white/10"
        >
          <div className="flex items-center justify-center gap-6 text-xs">
            <div className="text-center">
              <div className="property-value text-sm">
                {filteredProperties.length}
              </div>
              <div className="text-gray-400">Properties</div>
            </div>
            <div className="text-center">
              <div className="property-value text-sm">
                {filteredProperties.filter(p => p.priority === 'high').length}
              </div>
              <div className="text-gray-400">High Priority</div>
            </div>
            <div className="text-center">
              <div className="property-value text-sm">
                {activeGeofences.length}
              </div>
              <div className="text-gray-400">Alerts Active</div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}