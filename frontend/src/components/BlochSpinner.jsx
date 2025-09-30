import React from 'react';
import './BlochSpinner.css';

const BlochSpinner = ({ 
  size = 48, 
  color = '#64d2ff', 
  stroke = '#9aa8ff', 
  ring = '#7b86ff', 
  speed = 1.8, 
  ariaLabel = 'Processing quantum optimization...',
  className = ''
}) => {
  const style = {
    '--bloch-size': `${size}px`,
    '--bloch-accent': color,
    '--bloch-stroke': stroke,
    '--bloch-ring': ring,
    '--bloch-speed': `${speed}s`,
  };

  return (
    <div 
      className={`bloch-spinner-wrapper ${className}`} 
      style={style} 
      role="img" 
      aria-label={ariaLabel}
    >
      <svg className="bloch-spinner" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="bloch-gradient" cx="40%" cy="30%">
            <stop offset="0%" stopColor="rgba(255,255,255,0.4)"/>
            <stop offset="100%" stopColor="rgba(255,255,255,0)"/>
          </radialGradient>
        </defs>
        
        {/* Sphere base with rings */}
        <g className="bloch-base">
          <circle 
            className="sphere-outline" 
            cx="50" 
            cy="50" 
            r="30" 
            fill="none" 
            stroke="var(--bloch-stroke)" 
            strokeWidth="2"
          />
          {/* Equator (horizontal) */}
          <ellipse 
            className="equator" 
            cx="50" 
            cy="50" 
            rx="30" 
            ry="8" 
            fill="none" 
            stroke="var(--bloch-ring)" 
            strokeWidth="1.5"
          />
          {/* Meridian (vertical, drawn as rotated ellipse) */}
          <ellipse 
            className="meridian" 
            cx="50" 
            cy="50" 
            rx="8" 
            ry="30" 
            fill="none" 
            stroke="var(--bloch-ring)" 
            strokeWidth="1.5" 
            transform="rotate(90 50 50)"
          />
          {/* Depth shading */}
          <circle 
            cx="46" 
            cy="44" 
            r="20" 
            fill="url(#bloch-gradient)" 
            opacity="0.25"
          />
        </g>

        {/* Orbiting qubit */}
        <g className="orbit" transform="translate(50,50)">
          <circle cx="0" cy="0" r="30" fill="none" stroke="none"/>
          <g className="dot-group" transform="translate(0,-30)">
            <circle 
              className="qubit-core" 
              cx="0" 
              cy="0" 
              r="2.8" 
              fill="var(--bloch-accent)"
            />
            <circle 
              className="qubit-glow" 
              cx="0" 
              cy="0" 
              r="6" 
              fill="var(--bloch-accent)" 
              opacity="0.12"
            />
          </g>
        </g>
      </svg>
    </div>
  );
};

export default BlochSpinner;