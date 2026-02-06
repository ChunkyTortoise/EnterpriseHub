"use client";
import { cn } from "@/lib/utils";
import React, { useEffect, useRef, useState } from "react";

export const BackgroundBeams = ({ className }: { className?: string }) => {
  const beams = [
    {
      initialX: 10,
      translateX: 10,
      duration: 7,
      repeatDelay: 3,
      delay: 2,
    },
    {
      initialX: 600,
      translateX: 600,
      duration: 3,
      repeatDelay: 3,
      delay: 4,
    },
    {
      initialX: 100,
      translateX: 100,
      duration: 7,
      repeatDelay: 7,
      className: "h-20",
    },
    {
      initialX: 400,
      translateX: 400,
      duration: 5,
      repeatDelay: 14,
      delay: 4,
    },
    {
      initialX: 800,
      translateX: 800,
      duration: 11,
      repeatDelay: 2,
      className: "h-20",
    },
    {
      initialX: 1000,
      translateX: 1000,
      duration: 4,
      repeatDelay: 2,
      className: "h-12",
    },
    {
      initialX: 1200,
      translateX: 1200,
      duration: 6,
      repeatDelay: 4,
      delay: 2,
      className: "h-6",
    },
  ];

  return (
    <div
      className={cn(
        "absolute inset-0 [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]",
        className
      )}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 1440 600"
        fill="none"
        className="absolute inset-0 h-full w-full opacity-40"
      >
        <AnimateBeams beams={beams} />
      </svg>
    </div>
  );
};

const AnimateBeams = ({ beams }: { beams: any[] }) => {
  return (
    <>
      {beams.map((beam, index) => (
        <React.Fragment key={index}>
          <path
            d={`M${beam.initialX} -100 L${beam.translateX} 800`}
            stroke="url(#gradient)"
            strokeWidth="1"
            strokeLinecap="round"
            strokeDasharray="100 1000"
            className={cn("animate-beam", beam.className)}
            style={{
              animationDuration: `${beam.duration}s`,
              animationDelay: `${beam.delay || 0}s`,
            }}
          />
        </React.Fragment>
      ))}
      <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="transparent" />
          <stop offset="50%" stopColor="#0052ff" />
          <stop offset="100%" stopColor="transparent" />
        </linearGradient>
      </defs>
    </>
  );
};
