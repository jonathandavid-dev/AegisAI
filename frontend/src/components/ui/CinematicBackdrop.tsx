import React, { useEffect, useRef } from 'react';

export const CinematicBackdrop: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: Array<{
      x: number;
      y: number;
      size: number;
      speedY: number;
      speedX: number;
      opacity: number;
      maxOpacity: number;
      fadeSpeed: number;
    }> = [];

    const resizeCanvas = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      initParticles();
    };

    const initParticles = () => {
      particles = [];
      const count = Math.min(Math.floor((canvas.width * canvas.height) / 25000), 70);
      for (let i = 0; i < count; i++) {
        const maxOpacity = Math.random() * 0.2 + 0.05;
        particles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          size: Math.random() * 2 + 0.5,
          speedY: -(Math.random() * 0.3 + 0.1),
          speedX: (Math.random() * 0.2 - 0.1),
          opacity: Math.random() * maxOpacity,
          maxOpacity,
          fadeSpeed: Math.random() * 0.005 + 0.002,
        });
      }
    };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Update and draw particles
      particles.forEach((p) => {
        p.y += p.speedY;
        p.x += p.speedX;

        // Wrap around horizontally
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;

        // Reset if drifted off top
        if (p.y < 0) {
          p.y = canvas.height;
          p.x = Math.random() * canvas.width;
          p.opacity = 0;
        }

        // Fade in/out cycle
        if (p.opacity < p.maxOpacity) {
          p.opacity += p.fadeSpeed;
        }

        // Draw particle with green glow
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(52, 211, 153, ${Math.min(p.opacity, p.maxOpacity)})`;
        ctx.shadowBlur = 8;
        ctx.shadowColor = '#10B981';
        ctx.fill();
        ctx.shadowBlur = 0; // reset
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none z-0 bg-black select-none">
      {/* Layer 5: Volumetric Green Lighting */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#010c07] via-black to-black opacity-80" />
      
      {/* Volumetric Emerald radial highlights */}
      <div className="absolute top-[-10%] left-[20%] w-[600px] h-[600px] rounded-full bg-gradient-to-br from-emerald-500/10 to-transparent blur-[120px]" />
      <div className="absolute bottom-[10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-gradient-to-tl from-emerald-400/5 to-transparent blur-[120px]" />

      {/* Layer 2: Slow Moving Fog / Clouds */}
      <div className="absolute inset-0 opacity-20 mix-blend-screen pointer-events-none">
        <div className="absolute top-1/4 left-0 right-0 h-96 bg-gradient-to-r from-transparent via-[#032014] to-transparent blur-[100px] animate-pulse" style={{ animationDuration: '12s' }} />
        <div className="absolute bottom-10 left-1/4 right-0 h-64 bg-gradient-to-l from-transparent via-[#06301d] to-transparent blur-[80px] animate-pulse" style={{ animationDuration: '18s' }} />
      </div>

      {/* Layer 3 & 4: Floating Particles Canvas */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full block" />

      {/* Layer 1: Volcanic Black Terrain (Stylized bottom mesh/silhouette) */}
      <div className="absolute bottom-0 left-0 right-0 h-48 pointer-events-none select-none opacity-40">
        <svg viewBox="0 0 1440 200" fill="none" xmlns="http://www.w3.org/2000/svg" className="absolute bottom-0 w-full h-full text-black">
          <path 
            d="M0,160 L40,150 C80,140 160,120 240,110 C320,100 400,100 480,115 C560,130 640,160 720,165 C800,170 880,150 960,135 C1040,120 1120,110 1200,115 C1280,120 1360,140 1400,150 L1440,160 L1440,200 L1400,200 C1360,200 1280,200 1200,200 C1120,200 1040,200 960,200 C880,200 800,200 720,200 C640,200 560,200 480,200 C400,200 320,200 240,200 C160,200 80,200 40,200 L0,200 Z" 
            fill="#050505" 
          />
          <path 
            d="M0,175 L60,170 C120,165 240,155 360,150 C480,145 600,145 720,155 C840,165 960,185 1080,185 C1200,185 1320,165 1380,155 L1440,145 L1440,200 L1380,200 C1320,200 1200,200 1080,200 C960,200 840,200 720,200 C600,200 480,200 360,200 C240,200 120,200 60,200 L0,200 Z" 
            fill="#000000" 
          />
        </svg>
      </div>

      {/* Cybernetic Subtle Overlay Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(rgba(16,185,129,0.03)_1px,transparent_1px)] bg-[size:32px_32px] opacity-60" />
    </div>
  );
};
