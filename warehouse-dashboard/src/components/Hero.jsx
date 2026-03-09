import { useEffect, useRef, useState } from 'react';
import AuroraBackground from './AuroraBackground';

/* Fade-up style helper */
const fadeUp = (visible) => ({
  opacity: visible ? 1 : 0,
  transform: visible ? 'translateY(0)' : 'translateY(20px)',
  transition: 'opacity 0.8s ease, transform 0.8s ease',
});

const ChevronDown = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
    <path d="M6 9l6 6 6-6" stroke="rgba(167,139,250,0.6)" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const ORBS = [
  {
    size: '600px',
    pos: { top: '-10%', left: '-10%' },
    bg: 'radial-gradient(circle, rgba(167,139,250,0.23) 0%, transparent 70%)',
    blur: '80px', dur: '10s', dir: 'normal', delay: '0s',
  },
  {
    size: '400px',
    pos: { top: '40%', right: '-8%' },
    bg: 'radial-gradient(circle, rgba(236,72,153,0.18) 0%, transparent 70%)',
    blur: '60px', dur: '14s', dir: 'reverse', delay: '0s',
  },
  {
    size: '300px',
    pos: { top: '20%', left: '40%' },
    bg: 'radial-gradient(circle, rgba(96,165,250,0.15) 0%, transparent 70%)',
    blur: '50px', dur: '8s', dir: 'normal', delay: '2s',
  },
];

const STATS = ['4,191 Customers', '£4.3M Revenue', '3,392 Products', '338,151 Transactions'];
const STAT_KEYS = ['s0', 's1', 's2', 's3'];

export default function Hero() {
  const bgRef      = useRef(null);
  const contentRef = useRef(null);

  const [vis, setVis] = useState({
    badge: false, h1: false, sub: false,
    s0: false, s1: false, s2: false, s3: false,
    cta: false, scroll: false,
  });

  /* Staggered fade-up on mount */
  useEffect(() => {
    const schedule = [
      [0,    'badge'],
      [200,  'h1'],
      [500,  'sub'],
      [700,  's0'],
      [800,  's1'],
      [900,  's2'],
      [1000, 's3'],
      [1100, 'cta'],
      [1300, 'scroll'],
    ];
    const timers = schedule.map(([delay, key]) =>
      setTimeout(() => setVis(v => ({ ...v, [key]: true })), delay)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  /* Parallax — orb layer at 0.25x scroll speed */
  useEffect(() => {
    const onScroll = () => {
      if (bgRef.current)
        bgRef.current.style.transform = `translateY(${window.scrollY * 0.25}px)`;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  /* Cursor-reactive content shift */
  useEffect(() => {
    const onMove = (e) => {
      if (!contentRef.current) return;
      const x = (e.clientX / window.innerWidth  - 0.5) * 0.15 * 30;
      const y = (e.clientY / window.innerHeight - 0.5) * 0.15 * 30;
      contentRef.current.style.transform = `translate(${x}px, ${y}px)`;
    };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  const scrollToDashboard = () =>
    document.getElementById('dashboard')?.scrollIntoView({ behavior: 'smooth' });

  return (
    <AuroraBackground>

      {/* Floating orbs — parallax layer */}
      <div ref={bgRef} style={{
        position: 'absolute', inset: 0,
        willChange: 'transform', pointerEvents: 'none', zIndex: 2,
      }}>
        {ORBS.map((o, i) => (
          <div key={i} style={{
            position: 'absolute',
            width: o.size, height: o.size,
            ...o.pos,
            borderRadius: '50%',
            background: o.bg,
            filter: `blur(${o.blur})`,
            animation: `float ${o.dur} ease-in-out infinite`,
            animationDirection: o.dir,
            animationDelay: o.delay,
            pointerEvents: 'none',
          }} />
        ))}
      </div>

      {/* Main content — cursor reactive */}
      <div ref={contentRef} style={{
        position: 'relative', zIndex: 3,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', textAlign: 'center',
        padding: '0 24px', maxWidth: '960px',
        transition: 'transform 0.1s ease',
      }}>

        {/* Pill badge */}
        <div style={{
          ...fadeUp(vis.badge),
          border: '1px solid rgba(255,255,255,0.15)',
          borderRadius: '999px',
          padding: '7px 22px',
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          fontFamily: "'Inter', sans-serif",
          fontWeight: 400,
          fontSize: '0.75rem',
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          color: 'rgba(255,255,255,0.6)',
          marginBottom: '32px',
        }}>
          Unsupervised Learning · UCI Online Retail Dataset
        </div>

        {/* Main title — CSS class handles gradient clip, inline handles fade + glow */}
        <h1
          style={{
            opacity: vis.h1 ? 1 : 0,
            transform: vis.h1 ? 'translateY(0)' : 'translateY(20px)',
            transition: 'opacity 0.8s ease, transform 0.8s ease',
            fontFamily: 'Syne, sans-serif',
            fontWeight: 800,
            fontSize: 'clamp(4rem, 10vw, 9rem)',
            lineHeight: 0.9,
            marginBottom: '24px',
            color: '#ffffff',
            filter: 'drop-shadow(0 0 40px rgba(167,139,250,0.6)) drop-shadow(0 0 80px rgba(236,72,153,0.3))',
          }}
        >
          Online Retail
        </h1>

        {/* Subtitle */}
        <p style={{
          ...fadeUp(vis.sub),
          fontFamily: "'Inter', sans-serif",
          fontWeight: 300,
          fontSize: 'clamp(1rem, 2.5vw, 1.4rem)',
          color: 'rgba(255,255,255,0.55)',
          letterSpacing: '0.02em',
          marginBottom: '44px',
        }}>
          Market Basket Analysis &amp; Customer Clustering
        </p>

        {/* Stat pills */}
        <div style={{
          display: 'flex', gap: '12px',
          flexWrap: 'wrap', justifyContent: 'center',
          marginBottom: '44px',
        }}>
          {STATS.map((label, i) => (
            <div key={label} style={{
              ...fadeUp(vis[STAT_KEYS[i]]),
              background: 'rgba(255,255,255,0.05)',
              backdropFilter: 'blur(10px)',
              WebkitBackdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '999px',
              padding: '9px 22px',
              fontFamily: "'Inter', sans-serif",
              fontWeight: 400,
              fontSize: '0.85rem',
              color: 'rgba(255,255,255,0.75)',
            }}>
              {label}
            </div>
          ))}
        </div>

        {/* CTA button */}
        <button
          style={{
            ...fadeUp(vis.cta),
            background: 'linear-gradient(135deg, #a78bfa, #f472b6, #60a5fa)',
            backgroundSize: '200% 200%',
            animation: `holoShift 4s ease infinite`,
            color: '#000',
            fontFamily: "'Syne', sans-serif",
            fontWeight: 700,
            fontSize: '1rem',
            borderRadius: '999px',
            padding: '14px 44px',
            border: 'none',
            cursor: 'pointer',
            transition: 'opacity 0.8s ease, transform 0.3s cubic-bezier(0.23,1,0.32,1), box-shadow 0.3s cubic-bezier(0.23,1,0.32,1)',
            marginBottom: '60px',
          }}
          onClick={scrollToDashboard}
          onMouseEnter={e => {
            e.currentTarget.style.transform = 'scale(1.05)';
            e.currentTarget.style.boxShadow = '0 0 40px rgba(167,139,250,0.5)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          Explore Analysis
        </button>
      </div>

      {/* Scroll indicator */}
      <div
        onClick={scrollToDashboard}
        style={{
          position: 'absolute', bottom: '32px', left: '50%', zIndex: 3,
          opacity: vis.scroll ? 1 : 0,
          transform: `translateX(-50%) translateY(${vis.scroll ? 0 : 20}px)`,
          transition: 'opacity 0.8s ease, transform 0.8s ease',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', gap: '8px',
          cursor: 'pointer', userSelect: 'none',
        }}
      >
        <span style={{
          fontFamily: "'Inter', sans-serif",
          fontWeight: 300,
          fontSize: '0.7rem',
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          color: 'rgba(255,255,255,0.3)',
        }}>
          Scroll to Explore
        </span>
        <div style={{ animation: 'bounce-chevron 2s ease-in-out infinite' }}>
          <ChevronDown />
        </div>
      </div>
    </AuroraBackground>
  );
}
