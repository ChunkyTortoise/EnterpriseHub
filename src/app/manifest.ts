// PWA Manifest for Jorge's Real Estate AI Platform
import { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Jorge's Real Estate AI Platform",
    short_name: "Jorge AI",
    description: "Professional AI-powered real estate command center with enterprise-grade bot ecosystem",
    start_url: "/jorge",
    scope: "/",
    display: "standalone",
    background_color: "#ffffff", 
    theme_color: "#2563eb", // blue-600
    orientation: "portrait-primary",
    categories: ["business", "productivity", "real-estate"],
    
    icons: [
      {
        src: "/icon-192x192.png",
        sizes: "192x192", 
        type: "image/png",
        purpose: "any maskable"
      },
      {
        src: "/icon-512x512.png",
        sizes: "512x512",
        type: "image/png"
      },
      {
        src: "/icon-384x384.png", 
        sizes: "384x384",
        type: "image/png"
      }
    ],
    
    shortcuts: [
      {
        name: "Jorge Command Center",
        short_name: "Command Center",
        description: "Access Jorge's bot dashboard",
        url: "/jorge",
        icons: [
          {
            src: "/shortcut-jorge.png",
            sizes: "96x96"
          }
        ]
      },
      {
        name: "Start Chat",
        short_name: "Chat",
        description: "Begin conversation with Jorge Seller Bot",
        url: "/jorge?tab=chat",
        icons: [
          {
            src: "/shortcut-chat.png", 
            sizes: "96x96"
          }
        ]
      }
    ],
    
    screenshots: [
      {
        src: "/screenshot-jorge-desktop.png",
        sizes: "1280x720",
        type: "image/png",
        form_factor: "wide",
        label: "Jorge Command Center Desktop View"
      },
      {
        src: "/screenshot-jorge-mobile.png",
        sizes: "390x844",
        type: "image/png", 
        form_factor: "narrow",
        label: "Jorge Mobile Interface"
      }
    ],
    
    // Real estate agent specific features
    related_applications: [
      {
        platform: "webapp",
        url: "https://gohighlevel.com",
        id: "ghl-integration"
      }
    ],
    
    // PWA capabilities for field agents
    prefer_related_applications: false,
    
    // Enterprise features
    iarc_rating_id: "business-app"
  }
}