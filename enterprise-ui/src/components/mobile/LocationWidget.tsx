'use client';

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import {
  MapPinIcon,
  BuildingOffice2Icon,
  HomeIcon,
  ClockIcon,
  ArrowUpIcon,
  SignalIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

interface LocationData {
  address: string;
  neighborhood: string;
  coordinates: { lat: number; lng: number };
  accuracy: number;
}

interface NearbyProperty {
  id: string;
  address: string;
  type: 'listing' | 'recent_sale' | 'lead_property';
  distance: number;
  price?: number;
  status: string;
  daysAgo?: number;
}

interface NearbyLead {
  id: string;
  name: string;
  address: string;
  distance: number;
  status: 'active' | 'scheduled' | 'contacted';
  lastContact: string;
}

export function LocationWidget() {
  const [location, setLocation] = useState<LocationData | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [nearbyProperties, setNearbyProperties] = useState<NearbyProperty[]>([]);
  const [nearbyLeads, setNearbyLeads] = useState<NearbyLead[]>([]);

  useEffect(() => {
    requestLocation();
  }, []);

  const requestLocation = () => {
    setIsLoading(true);
    setLocationError(null);

    if (!navigator.geolocation) {
      setLocationError('Geolocation not supported');
      setIsLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;

          // Simulate reverse geocoding
          const locationData: LocationData = {
            address: '1200 Brickell Avenue',
            neighborhood: 'Brickell',
            coordinates: { lat: latitude, lng: longitude },
            accuracy: position.coords.accuracy,
          };

          setLocation(locationData);

          // Simulate nearby properties
          const properties: NearbyProperty[] = [
            {
              id: 'nearby-1',
              address: '1250 Brickell Avenue #2A',
              type: 'listing',
              distance: 0.1,
              price: 725000,
              status: 'Active',
            },
            {
              id: 'nearby-2',
              address: '1180 Brickell Avenue #15B',
              type: 'recent_sale',
              distance: 0.2,
              price: 680000,
              status: 'Sold',
              daysAgo: 12,
            },
            {
              id: 'nearby-3',
              address: '1350 Brickell Avenue',
              type: 'lead_property',
              distance: 0.3,
              status: 'Interest',
            },
          ];

          const leads: NearbyLead[] = [
            {
              id: 'lead-nearby-1',
              name: 'Sarah Mitchell',
              address: '1400 Brickell Avenue',
              distance: 0.4,
              status: 'scheduled',
              lastContact: '2 hours ago',
            },
            {
              id: 'lead-nearby-2',
              name: 'David Kim',
              address: '1100 Brickell Avenue',
              distance: 0.6,
              status: 'active',
              lastContact: '1 day ago',
            },
          ];

          setNearbyProperties(properties);
          setNearbyLeads(leads);
        } catch (error) {
          setLocationError('Failed to get location details');
        } finally {
          setIsLoading(false);
        }
      },
      (error) => {
        let errorMessage = 'Location access denied';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location permission denied';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information unavailable';
            break;
          case error.TIMEOUT:
            errorMessage = 'Location request timed out';
            break;
        }
        setLocationError(errorMessage);
        setIsLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000, // 5 minutes
      }
    );
  };

  const getPropertyTypeIcon = (type: string) => {
    switch (type) {
      case 'listing':
        return HomeIcon;
      case 'recent_sale':
        return BuildingOffice2Icon;
      case 'lead_property':
        return MapPinIcon;
      default:
        return HomeIcon;
    }
  };

  const getPropertyTypeClasses = (type: string) => {
    switch (type) {
      case 'listing':
        return { bg: 'bg-jorge-glow/20', text: 'text-jorge-glow' };
      case 'recent_sale':
        return { bg: 'bg-jorge-gold/20', text: 'text-jorge-gold' };
      case 'lead_property':
        return { bg: 'bg-jorge-electric/20', text: 'text-jorge-electric' };
      default:
        return { bg: 'bg-gray-400/20', text: 'text-gray-400' };
    }
  };

  const getLeadStatusClasses = (status: string) => {
    switch (status) {
      case 'scheduled':
        return { text: 'text-jorge-electric' };
      case 'active':
        return { text: 'text-jorge-glow' };
      case 'contacted':
        return { text: 'text-jorge-gold' };
      default:
        return { text: 'text-gray-400' };
    }
  };

  const openMaps = (address: string) => {
    if ('vibrate' in navigator) {
      navigator.vibrate(50);
    }

    const encodedAddress = encodeURIComponent(address);
    const mapsUrl = `https://maps.apple.com/?q=${encodedAddress}`;
    window.open(mapsUrl, '_blank');
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ArrowUpIcon className="w-5 h-5 text-jorge-electric" />
          <h2 className="jorge-heading text-lg">Location Services</h2>
        </div>
        <div className="flex items-center gap-1">
          {location && (
            <>
              <SignalIcon className="w-4 h-4 text-jorge-glow" />
              <span className="text-xs jorge-code text-jorge-glow">GPS ACTIVE</span>
            </>
          )}
        </div>
      </div>

      {/* Current Location */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-card"
      >
        {isLoading && (
          <div className="flex items-center justify-center gap-3 py-4">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-5 h-5 border-2 border-jorge-electric border-t-transparent rounded-full"
            />
            <span className="text-sm jorge-code text-gray-400">Getting location...</span>
          </div>
        )}

        {locationError && (
          <div className="flex items-center justify-between p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
            <div className="flex items-center gap-2">
              <ExclamationTriangleIcon className="w-4 h-4 text-red-400" />
              <span className="text-sm text-red-400">{locationError}</span>
            </div>
            <button
              onClick={requestLocation}
              className="px-3 py-1 bg-red-500/20 text-red-400 text-xs font-semibold rounded jorge-haptic"
            >
              RETRY
            </button>
          </div>
        )}

        {location && (
          <div className="space-y-3">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-jorge-electric/20 rounded-lg">
                  <MapPinIcon className="w-5 h-5 text-jorge-electric" />
                </div>
                <div>
                  <h3 className="jorge-code text-sm font-medium text-white">
                    Current Location
                  </h3>
                  <p className="text-xs text-gray-400 mt-1">{location.address}</p>
                  <p className="text-xs text-jorge-glow">{location.neighborhood}</p>
                </div>
              </div>
              <button
                onClick={() => openMaps(location.address)}
                className="px-2 py-1 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic"
              >
                OPEN
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-white/10">
              <div className="text-center">
                <div className="text-sm text-white font-semibold">
                  {location.accuracy < 50 ? 'High' : location.accuracy < 100 ? 'Medium' : 'Low'}
                </div>
                <div className="text-xs text-gray-400">Accuracy</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-jorge-glow font-semibold">
                  {Math.round(location.accuracy)}m
                </div>
                <div className="text-xs text-gray-400">Radius</div>
              </div>
            </div>
          </div>
        )}
      </motion.div>

      {/* Nearby Properties */}
      {nearbyProperties.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="space-y-2"
        >
          <h3 className="jorge-heading text-base flex items-center gap-2">
            <HomeIcon className="w-4 h-4 text-jorge-glow" />
            Nearby Properties
          </h3>

          {nearbyProperties.map((property, index) => {
            const PropertyIcon = getPropertyTypeIcon(property.type);
            const classes = getPropertyTypeClasses(property.type);

            return (
              <motion.div
                key={property.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + index * 0.05 }}
                className="jorge-card jorge-card-hover cursor-pointer"
                onClick={() => openMaps(property.address)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 ${classes.bg} rounded-lg`}>
                      <PropertyIcon className={`w-4 h-4 ${classes.text}`} />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-white truncate">
                        {property.address}
                      </h4>
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <span>{property.distance} mi</span>
                        <span>•</span>
                        <span className={`${classes.text} font-semibold`}>
                          {property.status}
                        </span>
                        {property.daysAgo && (
                          <>
                            <span>•</span>
                            <span>{property.daysAgo}d ago</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  {property.price && (
                    <div className="property-value text-sm">
                      ${(property.price / 1000).toFixed(0)}K
                    </div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      )}

      {/* Nearby Leads */}
      {nearbyLeads.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-2"
        >
          <h3 className="jorge-heading text-base flex items-center gap-2">
            <ClockIcon className="w-4 h-4 text-jorge-electric" />
            Nearby Leads
          </h3>

          {nearbyLeads.map((lead, index) => {
            const statusClasses = getLeadStatusClasses(lead.status);

            return (
              <motion.div
                key={lead.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + index * 0.05 }}
                className="jorge-card jorge-card-hover cursor-pointer"
                onClick={() => openMaps(lead.address)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-jorge-gradient rounded-full flex items-center justify-center">
                      <span className="text-white text-xs font-semibold">
                        {lead.name.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-white">{lead.name}</h4>
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <span>{lead.distance} mi</span>
                        <span>•</span>
                        <span className={`${statusClasses.text} font-semibold`}>
                          {lead.status.toUpperCase()}
                        </span>
                        <span>•</span>
                        <span>{lead.lastContact}</span>
                      </div>
                    </div>
                  </div>
                  <ArrowUpIcon className="w-4 h-4 text-gray-400" />
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      )}

      {/* Location Stats */}
      {location && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="jorge-card text-center"
        >
          <div className="grid grid-cols-3 gap-3">
            <div>
              <div className="property-value text-lg">
                {nearbyProperties.length}
              </div>
              <div className="text-xs text-gray-400">Properties</div>
            </div>
            <div>
              <div className="property-value text-lg">
                {nearbyLeads.length}
              </div>
              <div className="text-xs text-gray-400">Leads</div>
            </div>
            <div>
              <div className="property-value text-lg">
                {location.neighborhood.split(' ').length > 1 ?
                  location.neighborhood.split(' ').map(w => w[0]).join('').toUpperCase() :
                  location.neighborhood.substring(0, 3).toUpperCase()
                }
              </div>
              <div className="text-xs text-gray-400">Area</div>
            </div>
          </div>

          {/* Enhanced Controls */}
          <button
            onClick={() => window.location.href = '/field-agent/location'}
            className="w-full mt-3 py-2 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic"
          >
            OPEN LOCATION INTELLIGENCE →
          </button>
        </motion.div>
      )}
    </div>
  );
}