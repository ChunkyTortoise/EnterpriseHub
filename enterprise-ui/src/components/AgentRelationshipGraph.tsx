"use client";

import * as React from "react";
import { useRef, useEffect, useState, useMemo } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Sphere, Line, Html, Float, Stars } from "@react-three/drei";
import * as THREE from "three";
import { cn } from "@/lib/utils";

// Core bots based on Jorge's production ecosystem
const initialAgentRelationships = {
  nodes: [
    { id: "Jorge-Brain", position: [0, 0, 0] as [number, number, number], color: "#0052ff", data: { status: "Active", type: "orchestrator" } },
    { id: "Jorge-Seller-Bot", position: [0, 2.5, 0] as [number, number, number], color: "#00f0ff", data: { status: "Active", type: "agent" } },
    { id: "Lead-Bot", position: [-2.5, -1, 1] as [number, number, number], color: "#ffd700", data: { status: "Active", type: "agent" } },
    { id: "Intent-Decoder", position: [2.5, -1, -1] as [number, number, number], color: "#6f42c1", data: { status: "Active", type: "analytics" } },
    { id: "Retell-Voice", position: [-3, 2, -1.5] as [number, number, number], color: "#ff4757", data: { status: "Idle", type: "voice" } },
    { id: "GHL-Sync", position: [3, 2, 1.5] as [number, number, number], color: "#2ed573", data: { status: "Active", type: "integration" } },
  ],
  links: [
    { source: "Jorge-Brain", target: "Jorge-Seller-Bot", color: "#4a5568" },
    { source: "Jorge-Brain", target: "Lead-Bot", color: "#4a5568" },
    { source: "Jorge-Brain", target: "Intent-Decoder", color: "#4a5568" },
    { source: "Jorge-Brain", target: "GHL-Sync", color: "#4a5568" },
    { source: "Lead-Bot", target: "Retell-Voice", color: "#4a5568" },
    { source: "Jorge-Seller-Bot", target: "Intent-Decoder", color: "#4a5568" },
  ],
};

interface AgentNodeProps {
  key?: string;
  position: [number, number, number];
  color: string;
  agentId: string;
  status: string;
  type: string;
  onSelect: (agentId: string) => void;
  isSelected: boolean;
}

function AgentNode({ position, color, agentId, status, type, onSelect, isSelected }: AgentNodeProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);
  const { camera } = useThree();

  const isOrchestrator = type === 'orchestrator';
  const radius = isOrchestrator ? 0.4 : 0.25;

  useFrame((state) => {
    if (meshRef.current) {
      // Gentle rotation
      meshRef.current.rotation.y += 0.01;
      // Pulse scale if active
      if (status === "Active") {
        const s = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.05;
        meshRef.current.scale.set(s, s, s);
      }
    }
  });

  return (
    <group position={position}>
      <Float speed={1.5} rotationIntensity={0.5} floatIntensity={0.5}>
        <Sphere
          ref={meshRef}
          args={[radius, 32, 32]}
          onClick={(e) => {
            e.stopPropagation();
            onSelect(agentId);
          }}
          onPointerOver={() => setHovered(true)}
          onPointerOut={() => setHovered(false)}
        >
          <meshStandardMaterial 
            color={hovered || isSelected ? "#ffffff" : color} 
            emissive={color}
            emissiveIntensity={hovered || isSelected ? 2 : 0.5}
            metalness={0.8}
            roughness={0.2}
          />
          
          <Html distanceFactor={10} position={[0, radius + 0.4, 0]} center>
            <div className={cn(
              "px-2 py-1 rounded border backdrop-blur-md transition-all duration-300 pointer-events-none select-none",
              isSelected 
                ? "bg-blue-600 border-blue-400 text-white scale-110" 
                : "bg-black/60 border-white/10 text-gray-300",
              "flex flex-col items-center gap-1"
            )}>
              <span className="text-[10px] font-bold jorge-code whitespace-nowrap">{agentId}</span>
              <div className="flex items-center gap-1">
                <div className={cn(
                  "w-1 h-1 rounded-full",
                  status === "Active" ? "bg-green-500 animate-pulse" : "bg-gray-500"
                )} />
                <span className="text-[8px] opacity-60 uppercase">{status}</span>
              </div>
            </div>
          </Html>
        </Sphere>
      </Float>
      
      {/* Dynamic Glow Aura */}
      <Sphere args={[radius * 1.5, 16, 16]}>
        <meshStandardMaterial 
          color={color} 
          transparent 
          opacity={0.1} 
          wireframe
        />
      </Sphere>

      {(status === "Active" || isSelected) && (
        <pointLight color={color} intensity={1.5} distance={2} decay={2} />
      )}
    </group>
  );
}

interface AgentRelationshipGraphProps {
    onAgentSelect?: (agentId: string) => void;
}

export function AgentRelationshipGraph({ onAgentSelect }: AgentRelationshipGraphProps) {
  const [relationships, setRelationships] = useState(initialAgentRelationships);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/agent-sync/state');
        const data = await response.json();
        
        if (data.agents) {
          setRelationships(prev => ({
            ...prev,
            nodes: prev.nodes.map(node => ({
              ...node,
              data: { 
                ...node.data, 
                status: data.agents[node.id]?.status || node.data.status 
              }
            }))
          }));
        }
      } catch (err) {
        // Silently fail if API not available
      }
    };

    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAgentSelect = (agentId: string) => {
    setSelectedAgent(agentId);
    if (onAgentSelect) {
        onAgentSelect(agentId);
    }
  };

  return (
    <div className="w-full h-full bg-[#050505] rounded-xl overflow-hidden border border-white/5 relative group">
      <div className="absolute top-4 left-4 z-10 pointer-events-none">
        <h3 className="text-white font-bold text-xs uppercase tracking-[0.2em] jorge-code opacity-50 group-hover:opacity-100 transition-opacity">
          Neural Agent Mesh
        </h3>
        <p className="text-[10px] text-blue-500 font-mono mt-1">Live Connection Matrix</p>
      </div>

      <Canvas camera={{ position: [0, 0, 7], fov: 45 }}>
        <color attach="background" args={["#050505"]} />
        <fog attach="fog" args={["#050505", 5, 15]} />
        
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        
        <ambientLight intensity={0.2} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <spotLight position={[-10, 10, 10]} angle={0.15} penumbra={1} intensity={1} />

        <group>
          {relationships.nodes.map((node) => (
            <AgentNode 
              key={node.id}
              position={node.position as [number, number, number]}
              color={node.color}
              agentId={node.id}
              type={node.data.type}
              status={node.data.status}
              onSelect={handleAgentSelect}
              isSelected={selectedAgent === node.id}
            />
          ))}

          {relationships.links.map((link, index) => {
            const sourceNode = relationships.nodes.find(node => node.id === link.source);
            const targetNode = relationships.nodes.find(node => node.id === link.target);

            if (sourceNode && targetNode) {
              const start = new THREE.Vector3(sourceNode.position[0], sourceNode.position[1], sourceNode.position[2]);
              const end = new THREE.Vector3(targetNode.position[0], targetNode.position[1], targetNode.position[2]);
              
              return (
                <group key={index}>
                  <Line
                    points={[start, end]}
                    color={link.color}
                    lineWidth={0.5}
                    transparent
                    opacity={0.3}
                  />
                  {/* Animated connection pulses */}
                  <ConnectionPulse start={start} end={end} color={sourceNode.color} />
                </group>
              );
            }
            return null;
          })}
        </group>

        <OrbitControls 
          enablePan={false} 
          minDistance={3} 
          maxDistance={12} 
          autoRotate 
          autoRotateSpeed={0.5}
          enableDamping
        />
      </Canvas>
      
      {/* Legend */}
      <div className="absolute bottom-4 right-4 flex flex-col gap-1.5 pointer-events-none">
        {relationships.nodes.filter(n => n.data.type === 'orchestrator' || n.id.includes('Bot')).map(n => (
          <div key={n.id} className="flex items-center gap-2 justify-end">
            <span className="text-[9px] text-gray-500 font-mono uppercase">{n.id}</span>
            <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: n.color }} />
          </div>
        ))}
      </div>
    </div>
  );
}

function ConnectionPulse({ start, end, color }: { start: THREE.Vector3, end: THREE.Vector3, color: string }) {
  const pulseRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (pulseRef.current) {
      const t = (state.clock.elapsedTime * 0.5) % 1;
      pulseRef.current.position.lerpVectors(start, end, t);
    }
  });

  return (
    <Sphere ref={pulseRef} args={[0.04, 16, 16]}>
      <meshBasicMaterial color={color} transparent opacity={0.8} />
    </Sphere>
  );
}
