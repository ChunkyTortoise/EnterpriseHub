"use client";

import React, { useRef, useEffect, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Sphere, Line } from "@react-three/drei";
import * as THREE from "three";
import { makeAuthenticatedRequest } from "@/lib/api";

// Mock data for agent relationships
// In a real scenario, this would come from a backend API
const mockAgentRelationships = {
  nodes: [
    { id: "SalesBot-Alpha", position: [0, 2, 0], color: "#007bff", data: { status: "Active" } },
    { id: "SellerBot-Beta", position: [-2, 0, 0], color: "#28a745", data: { status: "Active" } },
    { id: "LeadScorer", position: [2, 0, 0], color: "#ffc107", data: { status: "Active" } },
    { id: "MarketBot", position: [0, -2, 0], color: "#dc3545", data: { status: "Maintenance" } },
    { id: "Orchestrator", position: [0, 0, 0], color: "#6f42c1", data: { status: "Active" } },
    { id: "SMSBot", position: [3, 1, 0], color: "#17a2b8", data: { status: "Idle" } },
    { id: "EmailBot", position: [-3, 1, 0], color: "#fd7e14", data: { status: "Idle" } },
  ],
  links: [
    { source: "Orchestrator", target: "SalesBot-Alpha", color: "#6c757d" },
    { source: "Orchestrator", target: "SellerBot-Beta", color: "#6c757d" },
    { source: "Orchestrator", target: "LeadScorer", color: "#6c757d" },
    { source: "Orchestrator", target: "MarketBot", color: "#6c757d" },
    { source: "SalesBot-Alpha", target: "LeadScorer", color: "#6c757d" },
    { source: "SellerBot-Beta", target: "LeadScorer", color: "#6c757d" },
    { source: "Orchestrator", target: "SMSBot", color: "#6c757d" },
    { source: "Orchestrator", target: "EmailBot", color: "#6c757d" },
    { source: "SMSBot", target: "EmailBot", color: "#6c757d" },
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
  const [relationships, setRelationships] = useState(mockAgentRelationships);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // In a real application, you might fetch real-time data here
  // useEffect(() => {
  //   const fetchRelationships = async () => {
  //     const data = await makeAuthenticatedRequest("/api/agent-relationships");
  //     setRelationships(data);
  //   };
  //   fetchRelationships();
  // }, []);

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
