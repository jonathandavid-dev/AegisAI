import React, { useEffect, useRef, useState } from 'react';
import { useKnowledgeUniverse, UniverseNode } from '../context/KnowledgeUniverseContext';

export const LivingKnowledgeUniverse: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const { nodes, edges, queryOrb, pulseWave, satellites, searchStep } = useKnowledgeUniverse();
  
  // Parallax offsets
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [smoothMouse, setSmoothMouse] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      // Normalize mouse coords (-1 to 1)
      const nx = (e.clientX / window.innerWidth) * 2 - 1;
      const ny = (e.clientY / window.innerHeight) * 2 - 1;
      setMousePos({ x: nx, y: ny });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Smooth mouse movements using linear interpolation (LERP)
  useEffect(() => {
    const handle = requestAnimationFrame(function animateLerp() {
      setSmoothMouse((prev) => ({
        x: prev.x + (mousePos.x - prev.x) * 0.05,
        y: prev.y + (mousePos.y - prev.y) * 0.05,
      }));
      requestAnimationFrame(animateLerp);
    });
    return () => cancelAnimationFrame(handle);
  }, [mousePos]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let frameId: number;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Energy packet flows along edges
    const flows: Array<{
      fromId: number;
      toId: number;
      progress: number;
      speed: number;
    }> = [];

    const getClusterCenterCoords = (cluster: UniverseNode['cluster']) => {
      const clusters = ['HR', 'Finance', 'Security', 'Engineering', 'Legal', 'Compliance', 'Marketing'];
      const angle = (clusters.indexOf(cluster) / clusters.length) * Math.PI * 2;
      const radius = 180;
      return {
        x: window.innerWidth / 2 + Math.cos(angle) * radius,
        y: window.innerHeight / 2 + Math.sin(angle) * radius
      };
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const centerX = canvas.width / 2 + smoothMouse.x * 40;
      const centerY = canvas.height / 2 + smoothMouse.y * 30;
      const zoom = Math.min(canvas.width, canvas.height) / 220;

      // Project 3D coordinates onto 2D screen
      const projected = nodes.map((node) => {
        const d = 160; // depth constant
        
        // Dynamic search positioning: pulls active nodes to the center
        let nodeX = node.x;
        let nodeY = node.y;
        let nodeZ = node.z;

        if (searchStep >= 5) {
          if (node.status === 'active') {
            // Draw nodes closer in a neat central layout ring
            const index = nodes.filter(n => n.status === 'active').indexOf(node);
            const activeCount = nodes.filter(n => n.status === 'active').length;
            const angle = (index / activeCount) * Math.PI * 2 + (Date.now() * 0.0003);
            
            nodeX = Math.cos(angle) * 30;
            nodeY = Math.sin(angle) * 30;
            nodeZ = 0;
          } else {
            // Dimmed nodes drift far away
            nodeZ += 80;
          }
        }

        const scale = d / (d + nodeZ);
        const screenX = centerX + nodeX * scale * zoom;
        const screenY = centerY + nodeY * scale * zoom;

        return {
          id: node.id,
          name: node.name,
          cluster: node.cluster,
          x: screenX,
          y: screenY,
          size: node.size * scale,
          opacity: node.status === 'dimmed' ? 0.08 : node.opacity * scale,
          glowing: node.glowing,
          status: node.status
        };
      });

      // 1. Draw connecting semantic edges
      edges.forEach((edge) => {
        const fromNode = projected.find((p) => p.id === edge.from);
        const toNode = projected.find((p) => p.id === edge.to);

        if (!fromNode || !toNode) return;
        if (fromNode.status === 'dimmed' || toNode.status === 'dimmed') return;

        // Gradient line connecting the nodes
        ctx.beginPath();
        ctx.moveTo(fromNode.x, fromNode.y);
        ctx.lineTo(toNode.x, toNode.y);
        ctx.strokeStyle = `rgba(16, 185, 129, ${Math.min(fromNode.opacity, toNode.opacity) * 0.12})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
      });

      // Seed edge traffic flow packets randomly
      if (Math.random() < 0.08 && edges.length > 0) {
        const randomEdge = edges[Math.floor(Math.random() * edges.length)];
        // Check if both nodes are active before flowing
        const fromProj = projected.find(p => p.id === randomEdge.from);
        if (fromProj && fromProj.status !== 'dimmed') {
          flows.push({
            fromId: randomEdge.from,
            toId: randomEdge.to,
            progress: 0,
            speed: Math.random() * 0.015 + 0.008
          });
        }
      }

      // Update and draw traffic packets
      ctx.fillStyle = '#34D399';
      flows.forEach((flow, index) => {
        flow.progress += flow.speed;
        
        const fromNode = projected.find((p) => p.id === flow.fromId);
        const toNode = projected.find((p) => p.id === flow.toId);

        if (fromNode && toNode && fromNode.status !== 'dimmed') {
          // LERP packet coordinate along edge line
          const px = fromNode.x * (1 - flow.progress) + toNode.x * flow.progress;
          const py = fromNode.y * (1 - flow.progress) + toNode.y * flow.progress;

          ctx.beginPath();
          ctx.arc(px, py, 1.2, 0, Math.PI * 2);
          ctx.fill();
        }

        if (flow.progress >= 1) {
          flows.splice(index, 1);
        }
      });

      // 2. Draw nodes (Constellations)
      projected.forEach((p) => {
        let alpha = p.opacity;

        // Base node dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        
        const isMatchedNode = p.id > 0 && p.status === 'active';
        
        if (p.glowing) {
          ctx.fillStyle = '#10B981';
          ctx.shadowBlur = 12;
          ctx.shadowColor = '#10B981';
          
          // Draw radiating aura ring
          const auraRadius = p.size * (2 + Math.sin(Date.now() * 0.008) * 0.5);
          ctx.beginPath();
          ctx.arc(p.x, p.y, auraRadius, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(52, 211, 153, ${0.15 * Math.max(0, 1 - auraRadius / 15)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        } else if (isMatchedNode) {
          ctx.fillStyle = '#34D399';
        } else {
          ctx.fillStyle = '#1F2937'; // charcoal/dark gray seed stars
          ctx.shadowBlur = 0;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0; // reset

        // Label matching/active documents
        if (p.glowing || (isMatchedNode && searchStep >= 5)) {
          ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
          ctx.font = '7px monospace';
          ctx.fillText(p.name, p.x + 8, p.y + 2);
        }
      });

      // 3. Draw query orb (Search Step 2 & 3)
      if (queryOrb.active) {
        ctx.beginPath();
        ctx.arc(queryOrb.x, queryOrb.y, 8, 0, Math.PI * 2);
        const grad = ctx.createRadialGradient(queryOrb.x, queryOrb.y, 1, queryOrb.x, queryOrb.y, 8);
        grad.addColorStop(0, '#FFFFFF');
        grad.addColorStop(0.3, '#34D399');
        grad.addColorStop(1, 'rgba(16, 185, 129, 0)');
        ctx.fillStyle = grad;
        ctx.fill();
        
        ctx.beginPath();
        ctx.arc(queryOrb.x, queryOrb.y, 20, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(16, 185, 129, 0.05)';
        ctx.fill();
      }

      // 4. Draw pulse wave (Search Step 4)
      if (pulseWave.active) {
        ctx.beginPath();
        ctx.arc(pulseWave.x, pulseWave.y, pulseWave.radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(52, 211, 153, ${0.4 * (1 - pulseWave.radius / pulseWave.maxRadius)})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // 5. Draw satellite uploads (Ingestion)
      satellites.forEach((sat) => {
        const dest = getClusterCenterCoords('Engineering'); // default to Engineering cluster coordinates
        const curX = sat.startX * (1 - sat.progress) + dest.x * sat.progress;
        const curY = sat.startY * (1 - sat.progress) + dest.y * sat.progress;

        // Draw satellite dot with trajectory trail
        ctx.beginPath();
        ctx.arc(curX, curY, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#34D399';
        ctx.shadowBlur = 8;
        ctx.shadowColor = '#10B981';
        ctx.fill();
        ctx.shadowBlur = 0;

        // Satellite details text
        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.font = '8px monospace';
        ctx.fillText(`${sat.name} (${sat.stage.toUpperCase()})`, curX + 8, curY - 4);
      });

      frameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(frameId);
    };
  }, [nodes, edges, queryOrb, pulseWave, satellites, searchStep, smoothMouse]);

  return (
    <canvas 
      ref={canvasRef} 
      className="absolute inset-0 w-full h-full pointer-events-none z-0" 
      style={{ mixBlendMode: 'screen' }}
    />
  );
};
