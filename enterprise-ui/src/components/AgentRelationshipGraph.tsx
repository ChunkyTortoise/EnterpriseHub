"use client";

import React, { useRef, useEffect, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Sphere, Line } from "@react-three/drei";
import * as THREE from "three";
import { makeAuthenticatedRequest } from "@/lib/api";

// Real data for agent relationships including Phase 7 bots
const initialAgentRelationships = {
  nodes: [
    { id: "Orchestrator", position: [0, 0, 0], color: "#6f42c1", data: { status: "Active" } },
    { id: "SalesBot-Alpha", position: [0, 2, 0], color: "#007bff", data: { status: "Active" } },
    { id: "SellerBot-Beta", position: [-2, 0, 0], color: "#28a745", data: { status: "Active" } },
    { id: "LeadScorer", position: [2, 0, 0], color: "#ffc107", data: { status: "Active" } },
    { id: "MarketBot", position: [0, -2, 0], color: "#dc3545", data: { status: "Active" } },
    { id: "SMSBot", position: [3, 1, 0], color: "#17a2b8", data: { status: "Idle" } },
    { id: "EmailBot", position: [-3, 1, 0], color: "#fd7e14", data: { status: "Idle" } },
    { id: "WhatsAppBot", position: [1, 2.5, 0], color: "#25D366", data: { status: "Active" } },
    { id: "ObjectionBot", position: [-2.5, 2, 0], color: "#e83e8c", data: { status: "Active" } },
    { id: "ComplianceBot", position: [0, 3.5, 0], color: "#20c997", data: { status: "Active" } },
    { id: "RevenueBot", position: [2.5, -2, 0], color: "#fd7e14", data: { status: "Active" } },
  ],
  links: [
    { source: "Orchestrator", target: "SalesBot-Alpha", color: "#6c757d" },
    { source: "Orchestrator", target: "SellerBot-Beta", color: "#6c757d" },
    { source: "Orchestrator", target: "LeadScorer", color: "#6c757d" },
    { source: "Orchestrator", target: "MarketBot", color: "#6c757d" },
    { source: "Orchestrator", target: "WhatsAppBot", color: "#6c757d" },
    { source: "Orchestrator", target: "ObjectionBot", color: "#6c757d" },
    { source: "Orchestrator", target: "ComplianceBot", color: "#6c757d" },
    { source: "Orchestrator", target: "RevenueBot", color: "#6c757d" },
    { source: "SalesBot-Alpha", target: "ComplianceBot", color: "#6c757d" },
    { source: "ObjectionBot", target: "SalesBot-Alpha", color: "#6c757d" },
  ],
};

interface AgentNodeProps {
  position: [number, number, number];
  color: string;
  agentId: string;
  status: string;
  onSelect: (agentId: string) => void;
  isSelected: boolean;
}

function AgentNode({ position, color, agentId, status, onSelect, isSelected }: AgentNodeProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);
  const { camera } = useThree();

  useFrame(() => {
    if (meshRef.current) {
      // Make agents face the camera
      meshRef.current.lookAt(camera.position);
    }
  });

  return (
    <Sphere
      ref={meshRef}
      position={position}
      args={[0.2, 32, 32]} // Radius, widthSegments, heightSegments
      onClick={() => onSelect(agentId)}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      <meshStandardMaterial color={hovered || isSelected ? "hotpink" : color} transparent opacity={status === "Maintenance" ? 0.5 : 1} />
      {/* Agent ID Text */}
      {/* @ts-ignore */}
      <Text
        position={[0, 0.3, 0]}
        fontSize={0.15}
        color="black"
        anchorX="center"
        anchorY="middle"
      >
        {agentId}
      </Text>
      {/* Status indicator */}
      {status === "Active" && <pointLight position={[0.3, 0.3, 0]} color="green" intensity={1} />}
      {status === "Maintenance" && <pointLight position={[0.3, 0.3, 0]} color="red" intensity={1} />}
    </Sphere>
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
        console.error("3D Sync Error:", err);
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
    <Canvas camera={{ position: [0, 0, 5], fov: 75 }}>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <pointLight position={[-10, -10, -10]} />

      {relationships.nodes.map((node) => (
        <AgentNode 
          key={node.id}
          position={node.position as [number, number, number]}
          color={node.color}
          agentId={node.id}
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
            <Line
              key={index}
              points={[start, end]}
              color={link.color}
              lineWidth={1}
            />
          );
        }
        return null;
      })}

      <OrbitControls />
    </Canvas>
  );
}
