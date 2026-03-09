import { useEffect } from 'react';
import Hero from './components/Hero';
import Story from './components/Story';
import Dashboard from './components/Dashboard';

export default function App() {
  /* Sparkle particle system — injected once on mount */
  useEffect(() => {
    const created = [];

    /* 40 small dot sparkles */
    for (let i = 0; i < 40; i++) {
      const el = document.createElement('div');
      const size = 2 + Math.random() * 2;
      el.style.cssText = `
        position:fixed;
        width:${size}px;height:${size}px;
        background:white;border-radius:50%;
        opacity:0;
        top:${Math.random() * 100}%;left:${Math.random() * 100}%;
        pointer-events:none;z-index:0;
        animation:sparkle-fade ${2 + Math.random() * 2}s ease-in-out ${Math.random() * 8}s infinite;
      `;
      document.body.appendChild(el);
      created.push(el);
    }

    /* 8 four-pointed star sparkles */
    for (let i = 0; i < 8; i++) {
      const el = document.createElement('div');
      el.textContent = '✦';
      el.style.cssText = `
        position:fixed;
        font-size:${10 + Math.random() * 10}px;
        color:rgba(255,255,255,0.4);
        opacity:0;
        top:${Math.random() * 100}%;left:${Math.random() * 100}%;
        pointer-events:none;z-index:0;
        animation:sparkle-fade ${2 + Math.random() * 2}s ease-in-out ${Math.random() * 8}s infinite;
      `;
      document.body.appendChild(el);
      created.push(el);
    }

    return () => created.forEach(el => el.remove());
  }, []);

  return (
    <div style={{ background: '#000', minHeight: '100vh' }}>
      <Hero />
      <Story />
      <div id="dashboard"><Dashboard /></div>
    </div>
  );
}
