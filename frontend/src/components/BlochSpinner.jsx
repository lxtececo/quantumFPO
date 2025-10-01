import React, { useEffect, useRef } from 'react';
import './BlochSpinner.css';

const BlochSpinner = ({ 
  size = 48, 
  color = '#64d2ff', 
  stroke = 'currentColor', 
  speed = 1.8, 
  ariaLabel = 'Processing quantum optimization...',
  className = '',
  animateQubit = true
}) => {
  const svgRef = useRef(null);
  const animationRef = useRef(null);

  const style = {
    '--bloch-size': `${size}px`,
    '--bloch-speed': `${speed}s`,
    width: `${size}px`,
    height: `${size}px`,
    background: 'transparent'
  };

  useEffect(() => {
    if (!animateQubit || !svgRef.current) return;

    const qubitDot = svgRef.current.querySelector('#qubitDot');
    const stateVector = svgRef.current.querySelector('#stateVector');
    const qubitGlow = svgRef.current.querySelector('#qubitGlow');
    
    if (!qubitDot || !stateVector || !qubitGlow) return;

    const setQubit = (theta, phi) => {
      const R = 30; // radius of Bloch sphere
      const centerX = 50;
      const centerY = 50;
      
      // Calculate 3D position on Bloch sphere
      const x = centerX + R * Math.sin(theta) * Math.cos(phi);
      const y = centerY - R * Math.cos(theta); // SVG y is inverted
      
      // Update qubit dot position
      qubitDot.setAttribute('cx', x);
      qubitDot.setAttribute('cy', y);
      
      // Update glow position
      qubitGlow.setAttribute('cx', x);
      qubitGlow.setAttribute('cy', y);
      
      // Update state vector
      stateVector.setAttribute('x2', x);
      stateVector.setAttribute('y2', y);
    };

    // Animate qubit through various quantum states
    let t = 0;
    const animate = () => {
      t += 0.03 * speed; // Increased to 0.03 for faster animation
      
      // Create complex quantum state transitions covering full sphere
      const theta = Math.PI * (0.5 + 0.45 * Math.sin(t * 0.6 + Math.PI/4)); // Full polar range with offset
      const phi = 2 * Math.PI * t * 0.25 + 0.3 * Math.sin(t * 0.8); // Slower rotation with slight wobble
      
      setQubit(theta, phi);
      
      animationRef.current = requestAnimationFrame(animate);
    };
    
    animate();
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [speed, animateQubit]);

  return (
    <div 
      className={`bloch-spinner-wrapper ${className}`} 
      style={style} 
      role="img" 
      aria-label={ariaLabel}
    >
      <svg 
        ref={svgRef}
        className="bloch-spinner" 
        viewBox="0 0 100 100" 
        xmlns="http://www.w3.org/2000/svg" 
        style={{width: '100%', height: '100%', background: 'transparent'}}
      >
        {/* Bloch sphere */}
        <circle
          cx="50"
          cy="50"
          r="30"
          fill="none"
          stroke={stroke}
          strokeWidth="2"
          opacity="0.6"
        />
        
        {/* Equatorial circle */}
        <ellipse
          cx="50"
          cy="50"
          rx="30"
          ry="10"
          fill="none"
          stroke={stroke}
          strokeWidth="1.5"
          opacity="0.4"
        />
        
        {/* Vertical axis */}
        <line
          x1="50"
          y1="20"
          x2="50"
          y2="80"
          stroke={stroke}
          strokeWidth="1.5"
          opacity="0.3"
        />
        
        {/* State vector (from center to qubit) */}
        <line
          id="stateVector"
          x1="50"
          y1="50"
          x2="65"
          y2="35"
          stroke={color}
          strokeWidth="2"
          opacity="0.8"
        />
        
        {/* Qubit glow effect */}
        <circle
          id="qubitGlow"
          cx="65"
          cy="35"
          r="5"
          fill={color}
          opacity="0.3"
        />
        
        {/* Qubit state (moving dot) */}
        <circle
          id="qubitDot"
          cx="65"
          cy="35"
          r="3"
          fill={color}
          opacity="0.9"
        />
      </svg>
    </div>
  );
};

export default BlochSpinner;