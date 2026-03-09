import { useEffect, useRef, useState, useCallback } from 'react';
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale,
  LinearScale, BarElement, LineElement, PointElement, Filler,
} from 'chart.js';
import { Doughnut, Bar, Line } from 'react-chartjs-2';

ChartJS.register(
  ArcElement, Tooltip, Legend, CategoryScale,
  LinearScale, BarElement, LineElement, PointElement, Filler,
);
ChartJS.defaults.color = 'rgba(255,255,255,0.6)';
ChartJS.defaults.font.family = 'Syne';

// ─── Injected CSS (keyframes + grid utilities) ────────────────────────────────
const DASH_CSS = `
  @keyframes pulseGlow {
    0%, 100% { box-shadow: inset 0 0 0 1px rgba(201,160,203,0.3), 0 0 20px rgba(201,160,203,0.2); }
    50%       { box-shadow: inset 0 0 0 1px rgba(201,160,203,0.5), 0 0 40px rgba(201,160,203,0.4); }
  }
  .dash-grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 20px;
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
  }
  @media (max-width: 768px) {
    .dash-grid > * { grid-column: span 12 !important; }
  }
  .dash-section { padding: 80px 0; }
  .glass-hover {
    transition: transform 0.4s cubic-bezier(0.23,1,0.32,1),
                box-shadow  0.4s cubic-bezier(0.23,1,0.32,1);
  }
  .glass-hover:hover {
    transform:  translateY(-4px) scale(1.01);
    box-shadow: 0 20px 60px rgba(201,160,203,0.15);
  }
`;

// ─── Style constants ──────────────────────────────────────────────────────────
const glass = {
  background:           'rgba(10, 8, 16, 0.88)',
  backdropFilter:       'blur(20px)',
  WebkitBackdropFilter: 'blur(20px)',
  borderRadius:         '24px',
  position:             'relative',
  overflow:             'hidden',
  padding:              '28px',
  boxShadow:            'inset 0 0 0 1px rgba(201,160,203,0.25)',
};

const holoStyle = {
  color: '#fff',
};

const easeOutQuart = t => 1 - Math.pow(1 - t, 4);

// ─── Hooks ────────────────────────────────────────────────────────────────────
const useReveal = () => {
  useEffect(() => {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          setTimeout(() => {
            e.target.style.opacity   = '1';
            e.target.style.transform = 'translateY(0)';
          }, parseInt(e.target.dataset.delay) || 0);
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.reveal').forEach((el, i) => {
      el.style.opacity    = '0';
      el.style.transform  = 'translateY(28px)';
      el.style.transition = 'opacity 0.7s ease, transform 0.7s ease';
      el.dataset.delay    = (i % 5) * 110;
      obs.observe(el);
    });
    return () => obs.disconnect();
  }, []);
};

const useCountUp = (target, duration = 2000) => {
  const [val, setVal]   = useState(0);
  const triggered       = useRef(false);
  const elRef           = useRef(null);

  useEffect(() => {
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !triggered.current) {
        triggered.current = true;
        const start = performance.now();
        const step = (now) => {
          const t = Math.min((now - start) / duration, 1);
          setVal(Math.floor(easeOutQuart(t) * target));
          if (t < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
        obs.disconnect();
      }
    }, { threshold: 0.3 });
    if (elRef.current) obs.observe(elRef.current);
    return () => obs.disconnect();
  }, [target, duration]);

  return [val, elRef];
};

// ─── Small components ─────────────────────────────────────────────────────────
const SectionLabel = ({ children }) => (
  <div style={{
    fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.75rem',
    letterSpacing: '0.15em', color: 'rgba(255,255,255,0.35)',
    textTransform: 'uppercase', marginBottom: '8px',
  }}>
    {children}
  </div>
);

const SectionTitle = ({ children }) => (
  <h2 style={{
    ...holoStyle,
    fontFamily: "'Syne', sans-serif", fontWeight: 700,
    fontSize: '2rem', marginBottom: '40px',
  }}>
    {children}
  </h2>
);

// KPI card with count-up
const KPICard = ({ num, prefix = '', suffix = '', label }) => {
  const [val, elRef] = useCountUp(num);
  return (
    <div
      ref={elRef}
      className="reveal glass-hover"
      style={{
        ...glass,
        gridColumn: 'span 3',
        background: 'linear-gradient(135deg, rgba(22,12,34,0.95), rgba(12,18,38,0.95))',
      }}
    >
      <div style={{ height: '2px', width: '40px', background: 'linear-gradient(90deg,#C9A0CB,#9FCEEE)', marginBottom: '16px', borderRadius: '999px' }} />
      <div style={{
        ...holoStyle,
        fontFamily: "'Syne', sans-serif", fontWeight: 800,
        fontSize: 'clamp(1.8rem,3vw,2.6rem)', whiteSpace: 'nowrap', overflow: 'hidden',
      }}>
        {prefix}{val.toLocaleString()}{suffix}
      </div>
      <div style={{
        fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.78rem',
        textTransform: 'uppercase', letterSpacing: '0.12em',
        color: 'rgba(255,255,255,0.45)', marginTop: '8px',
      }}>
        {label}
      </div>
    </div>
  );
};

// Progress bar with scroll-triggered animation
const ProgressBar = ({ label, pct, gradient, delay = 0 }) => {
  const [width, setWidth] = useState('0%');
  const barRef = useRef(null);

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        setTimeout(() => setWidth(pct), delay);
        obs.disconnect();
      }
    }, { threshold: 0.3 });
    if (barRef.current) obs.observe(barRef.current);
    return () => obs.disconnect();
  }, [pct, delay]);

  return (
    <div ref={barRef} style={{ marginBottom: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.78rem', color: 'rgba(255,255,255,0.55)' }}>{label}</span>
        <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, fontSize: '0.85rem', color: '#fff' }}>{pct}</span>
      </div>
      <div style={{ height: '8px', borderRadius: '999px', background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
        <div style={{
          height: '100%', width, borderRadius: '999px', background: gradient,
          transition: `width 1s cubic-bezier(0.23,1,0.32,1) ${delay}ms`,
        }} />
      </div>
    </div>
  );
};

// Segment card with magnetic hover
const MagneticCard = ({ seg }) => {
  const cardRef = useRef(null);

  const onMouseMove = useCallback((e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const dx = Math.max(-8, Math.min(8, (e.clientX - (rect.left + rect.width  / 2)) * 0.05));
    const dy = Math.max(-8, Math.min(8, (e.clientY - (rect.top  + rect.height / 2)) * 0.05));
    cardRef.current.style.transform = `translate(${dx}px,${dy}px)`;
  }, []);

  const onMouseLeave = useCallback(() => {
    if (cardRef.current) cardRef.current.style.transform = 'translate(0,0)';
  }, []);

  return (
    <div
      ref={cardRef}
      className="reveal"
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      style={{ ...glass, gridColumn: 'span 3', transition: 'transform 0.3s ease' }}
    >
      <div style={{ height: '3px', width: '100%', background: seg.stripe, marginBottom: '20px' }} />
      <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: '1.15rem', color: '#fff', marginBottom: '12px' }}>
        {seg.name}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        {[
          { label: 'Count',      value: seg.count.toLocaleString() },
          { label: 'Share',      value: seg.pct                   },
          { label: 'Recency',    value: seg.recency               },
          { label: 'Avg Orders', value: seg.orders                },
        ].map(c => (
          <div key={c.label}>
            <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{c.label}</div>
            <div style={{ fontFamily: "'Syne', sans-serif",  fontWeight: 600, fontSize: '0.95rem', color: '#fff' }}>{c.value}</div>
          </div>
        ))}
      </div>

      <div style={{ ...holoStyle, fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: '2rem', marginTop: '16px' }}>
        {seg.rev}
      </div>
      <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
        Revenue Share
      </div>

      <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '12px', marginTop: '4px', fontFamily: "'Inter', sans-serif", fontStyle: 'italic', fontWeight: 300, fontSize: '0.78rem', color: 'rgba(255,255,255,0.45)', lineHeight: 1.5 }}>
        {seg.strategy}
      </div>
    </div>
  );
};

// Insight flip card
const FlipCard = ({ seg }) => {
  const [flipped, setFlipped] = useState(false);
  const faceBase = {
    position: 'absolute', inset: 0, borderRadius: '24px', padding: '28px',
    backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden',
    display: 'flex', flexDirection: 'column', justifyContent: 'center',
  };

  return (
    <div
      className="reveal"
      style={{ perspective: '1000px', height: '240px', cursor: 'pointer', gridColumn: 'span 6' }}
      onMouseEnter={() => setFlipped(true)}
      onMouseLeave={() => setFlipped(false)}
    >
      <div style={{
        position: 'relative', width: '100%', height: '100%',
        transformStyle: 'preserve-3d',
        transition: 'transform 0.7s cubic-bezier(0.23,1,0.32,1)',
        transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
      }}>
        {/* Front */}
        <div style={{ ...faceBase, background: 'rgba(255,255,255,0.06)', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)', boxShadow: 'inset 0 0 0 1px rgba(201,160,203,0.3)' }}>
          <div style={{ height: '3px', width: '100%', background: seg.stripe, marginBottom: '20px' }} />
          <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: '1.3rem', color: '#fff' }}>{seg.name}</div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '10px', flexWrap: 'wrap' }}>
            <span style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '999px', padding: '4px 12px', fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.78rem', color: 'rgba(255,255,255,0.6)' }}>
              {seg.count.toLocaleString()} customers
            </span>
            <span style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '999px', padding: '4px 12px', fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.78rem', color: 'rgba(255,255,255,0.6)' }}>
              {seg.rev} revenue
            </span>
          </div>
          <div style={{ marginTop: 'auto', fontFamily: "'Inter', sans-serif", fontStyle: 'italic', fontWeight: 300, fontSize: '0.75rem', color: 'rgba(255,255,255,0.3)', paddingTop: '16px' }}>
            Hover to reveal strategy →
          </div>
        </div>

        {/* Back */}
        <div style={{ ...faceBase, transform: 'rotateY(180deg)', background: 'linear-gradient(135deg, rgba(28,14,42,0.97), rgba(14,22,48,0.97))', border: '1px solid rgba(201,160,203,0.35)' }}>
          <div style={{ ...holoStyle, fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: '1rem', marginBottom: '12px' }}>{seg.name}</div>
          <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.9rem', color: 'rgba(255,255,255,0.85)', lineHeight: 1.6 }}>{seg.strategy}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '16px' }}>
            {seg.actions.map(a => (
              <span key={a} style={{ background: 'rgba(255,255,255,0.1)', borderRadius: '999px', padding: '4px 14px', fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.75rem', color: '#fff' }}>
                {a}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── Data ─────────────────────────────────────────────────────────────────────
const SEGMENT_DATA = [
  {
    name: 'Platinum', stripe: '#C9A0CB', count: 679,  pct: '16.2%', recency: '20 days',  orders: 12.9, rev: '56.9%',
    strategy: 'Launch VIP loyalty program with early product access. Bundle Regency Teacup sets (lift 21.23×). Personal outreach for accounts averaging £3,620+.',
    actions: ['VIP Program', 'Teacup Bundle', 'Early Access'],
  },
  {
    name: 'Loyal',     stripe: '#9FCEEE', count: 1406, pct: '33.5%', recency: '49 days',  orders: 3.7,  rev: '30.9%',
    strategy: 'Deploy automated Lunch Bag bundle recommendations (lift 16×). Target 545 borderline customers before they slide to At Risk.',
    actions: ['Bundle Recs', 'Borderline Alert', 'Frequency Push'],
  },
  {
    name: 'At Risk',   stripe: '#F4BBD7', count: 1212, pct: '28.9%', recency: '60 days',  orders: 1.4,  rev: '6.8%',
    strategy: 'Trigger win-back email at day 45 of inactivity. Offer 15% bundle discount. Highest single-rule lift 32.2× — strong re-entry signal.',
    actions: ['Day 45 Email', '15% Discount', 'Bundle Win-back'],
  },
  {
    name: 'Lost',      stripe: '#A98BD1', count: 894,  pct: '21.3%', recency: '261 days', orders: 1.3,  rev: '5.4%',
    strategy: 'Reactivation campaign targeting high-confidence rules (0.71 confidence). Last purchase 8+ months ago — price incentive is key re-entry.',
    actions: ['Price Incentive', 'Reactivation', 'High Confidence Rules'],
  },
];

const NAV_LINKS = [
  { id: 'overview',   label: 'Overview'   },
  { id: 'segments',   label: 'Segments'   },
  { id: 'algorithms', label: 'Algorithms' },
  { id: 'reduction',  label: 'Reduction'  },
  { id: 'revenue',    label: 'Revenue'    },
  { id: 'basket',     label: 'Basket'     },
  { id: 'insights',   label: 'Insights'   },
];

const RULES = [
  ['Green Regency Teacup + Roses → Pink Regency Teacup', '0.022', '0.812', '21.23'],
  ['Pink Regency Teacup → Green + Roses Regency Teacup',  '0.022', '0.798', '21.23'],
  ['Pink + Roses Teacup → Green Regency Teacup',          '0.021', '0.791', '21.11'],
  ['Lunch Bag Red Retrospot → Lunch Bag Spaceboy',        '0.031', '0.634', '16.20'],
  ['Lunch Bag Spaceboy → Lunch Bag Cars Blue',            '0.028', '0.612', '14.85'],
];

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function Dashboard() {
  useReveal();
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    const sections = NAV_LINKS.map(l => document.getElementById(l.id)).filter(Boolean);
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) setActiveSection(e.target.id); });
    }, { threshold: 0, rootMargin: '-30% 0px -60% 0px' });
    sections.forEach(s => obs.observe(s));
    return () => obs.disconnect();
  }, []);

  const scrollTo = id => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });

  return (
    <div style={{ position: 'relative', background: '#000' }}>
      <style>{DASH_CSS}</style>

      {/* Aurora layers — fixed so they blend with Story section above */}
      <div className="aurora-layer-1" style={{ position: 'fixed', inset: '-10px', zIndex: 0, pointerEvents: 'none' }} />
      <div className="aurora-layer-2" style={{ position: 'fixed', inset: '-10px', zIndex: 1, pointerEvents: 'none' }} />

      <div style={{ position: 'relative', zIndex: 2 }}>

        {/* ── Sticky Nav ─────────────────────────────────────────────────── */}
        <nav style={{
          position: 'sticky', top: 0, zIndex: 100,
          background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          padding: '14px 40px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div style={{ ...holoStyle, fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: '1.3rem' }}>
            RetailML
          </div>

          <div style={{ display: 'flex', alignItems: 'center' }}>
            {NAV_LINKS.map(l => (
              <a key={l.id} onClick={() => scrollTo(l.id)} style={{
                fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem',
                color: activeSection === l.id ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.5)',
                margin: '0 16px', textDecoration: 'none', cursor: 'pointer',
                borderBottom: activeSection === l.id ? '2px solid #C9A0CB' : '2px solid transparent',
                paddingBottom: '2px',
                transition: 'color 0.3s ease, border-color 0.3s ease',
              }}>
                {l.label}
              </a>
            ))}
          </div>

          <div style={{
            background: 'rgba(255,255,255,0.06)', backdropFilter: 'blur(10px)',
            borderRadius: '999px', padding: '6px 16px',
            boxShadow: 'inset 0 0 0 1px rgba(201,160,203,0.3)',
            fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)',
          }}>
            UCI Online Retail Dataset
          </div>
        </nav>

        {/* ══ SECTION 1 — Overview ══════════════════════════════════════════ */}
        <section id="overview" className="dash-section">
          <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 24px', marginBottom: '40px' }}>
            <SectionLabel>Executive Overview</SectionLabel>
            <SectionTitle>Key Performance Indicators</SectionTitle>
          </div>
          <div className="dash-grid">
            <KPICard num={4191}    prefix=""  label="Total Customers" />
            <KPICard num={4318862} prefix="£" label="Total Revenue"   />
            <KPICard num={3392}    prefix=""  label="Unique Products"  />
            <KPICard num={338151}  prefix=""  label="Transactions"    />
          </div>
        </section>

        {/* ══ SECTION 2 — Segments ══════════════════════════════════════════ */}
        <section id="segments" className="dash-section">
          <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 24px', marginBottom: '40px' }}>
            <SectionLabel>Customer Segmentation</SectionLabel>
            <SectionTitle>RFM-Based Customer Segments</SectionTitle>
          </div>

          <div className="dash-grid" style={{ marginBottom: '20px' }}>
            {/* Doughnut */}
            <div className="reveal glass-hover" style={{ ...glass, gridColumn: 'span 7', height: '360px' }}>
              <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: '0.9rem', color: 'rgba(255,255,255,0.6)', marginBottom: '16px' }}>
                Segment Distribution
              </div>
              <div style={{ height: 'calc(100% - 40px)' }}>
                <Doughnut
                  data={{
                    labels: ['Platinum', 'Loyal', 'At Risk', 'Lost'],
                    datasets: [{
                      data: [679, 1406, 1212, 894],
                      backgroundColor: ['#C9A0CB', '#9FCEEE', '#F4BBD7', '#A98BD1'],
                      borderColor: 'rgba(0,0,0,0)', borderWidth: 0,
                    }],
                  }}
                  options={{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {
                      legend: { position: 'bottom', labels: { color: 'rgba(255,255,255,0.6)', padding: 16, font: { family: 'Inter', size: 12 } } },
                      tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed.toLocaleString()}` } },
                    },
                  }}
                />
              </div>
            </div>

            {/* Bar — avg spend */}
            <div className="reveal glass-hover" style={{ ...glass, gridColumn: 'span 5', height: '360px' }}>
              <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: '0.9rem', color: 'rgba(255,255,255,0.6)', marginBottom: '16px' }}>
                Avg Spend by Segment
              </div>
              <div style={{ height: 'calc(100% - 40px)' }}>
                <Bar
                  data={{
                    labels: ['Platinum', 'Loyal', 'At Risk', 'Lost'],
                    datasets: [{
                      data: [3620, 948, 242, 262],
                      backgroundColor: ['#C9A0CB', '#9FCEEE', '#F4BBD7', '#A98BD1'],
                      borderRadius: 8,
                    }],
                  }}
                  options={{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false },
                      tooltip: { callbacks: { label: ctx => ` £${ctx.parsed.y.toLocaleString()}` } },
                    },
                    scales: {
                      x: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: 'rgba(255,255,255,0.6)' } },
                      y: { display: false },
                    },
                  }}
                />
              </div>
            </div>
          </div>

          {/* Segment detail cards */}
          <div className="dash-grid">
            {SEGMENT_DATA.map(seg => <MagneticCard key={seg.name} seg={seg} />)}
          </div>
        </section>

        {/* ══ SECTION 3 — Algorithms ════════════════════════════════════════ */}
        <section id="algorithms" className="dash-section">
          <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 24px', marginBottom: '40px' }}>
            <SectionLabel>Algorithm Comparison</SectionLabel>
            <SectionTitle>Clustering Performance</SectionTitle>
          </div>

          <div className="dash-grid" style={{ marginBottom: '20px' }}>
            {/* Grouped bar */}
            <div className="reveal glass-hover" style={{ ...glass, gridColumn: 'span 7', height: '340px' }}>
              <div style={{ height: '100%' }}>
                <Bar
                  data={{
                    labels: ['Silhouette (×10)', 'Davies-Bouldin (inv)', 'CH Index (÷1000)'],
                    datasets: [
                      { label: 'K-Means',      data: [4.343, 9.271, 5.662], backgroundColor: 'rgba(201,160,203,0.85)', borderRadius: 6 },
                      { label: 'DBSCAN',       data: [0.1,   0,     0.1  ], backgroundColor: 'rgba(159,206,238,0.6)',  borderRadius: 6 },
                      { label: 'Hierarchical', data: [3.6,   8.11,  4.821], backgroundColor: 'rgba(169,139,209,0.7)',  borderRadius: 6 },
                    ],
                  }}
                  options={{
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { position: 'top', labels: { color: 'rgba(255,255,255,0.6)' } } },
                    scales: {
                      x: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: 'rgba(255,255,255,0.6)' } },
                      y: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: 'rgba(255,255,255,0.6)' } },
                    },
                  }}
                />
              </div>
            </div>

            {/* Distance metrics table */}
            <div className="reveal glass-hover" style={{ ...glass, gridColumn: 'span 5' }}>
              <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: '0.9rem', color: 'rgba(255,255,255,0.6)', marginBottom: '20px' }}>
                Distance Metric Comparison
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr 1fr 1fr' }}>
                {['Metric', 'Silhouette', 'DB Index', 'CH'].map(h => (
                  <div key={h} style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.72rem', letterSpacing: '0.1em', color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', paddingBottom: '10px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                    {h}
                  </div>
                ))}
                {[
                  { metric: 'Euclidean',     best: true,  sil: '0.4273', db: '0.7447', ch: '5,600' },
                  { metric: 'Manhattan',     best: false, sil: '0.4238', db: '0.7613', ch: '5,435' },
                  { metric: 'Minkowski p=3', best: false, sil: '0.4255', db: '0.7454', ch: '5,581' },
                ].flatMap(row => [
                  <div key={row.metric + 'm'} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem', color: '#fff', padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                    {row.metric}
                    {row.best && <span style={{ background: 'linear-gradient(135deg,#C9A0CB,#9FCEEE)', color: '#000', fontFamily: "'Syne', sans-serif", fontWeight: 600, fontSize: '0.65rem', borderRadius: '999px', padding: '2px 8px', whiteSpace: 'nowrap' }}>BEST</span>}
                  </div>,
                  <div key={row.metric + 's'} style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem', color: '#fff', padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>{row.sil}</div>,
                  <div key={row.metric + 'd'} style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem', color: '#fff', padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>{row.db}</div>,
                  <div key={row.metric + 'c'} style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem', color: '#fff', padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>{row.ch}</div>,
                ])}
              </div>
            </div>
          </div>

          {/* Winner banner */}
          <div className="dash-grid">
            <div className="reveal" style={{
              gridColumn: 'span 12', borderRadius: '24px', padding: '28px',
              background: 'rgba(10, 8, 16, 0.92)',
              border: '1px solid rgba(201,160,203,0.25)',
              animation: 'pulseGlow 3s infinite',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px',
            }}>
              <div style={{ ...holoStyle, fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: '1.4rem' }}>
                K-Means + Euclidean Distance
              </div>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                {['Silhouette: 0.4343', 'DB: 0.7294', 'CH: 5,662'].map(pill => (
                  <div key={pill} style={{ background: 'rgba(255,255,255,0.08)', backdropFilter: 'blur(10px)', borderRadius: '999px', padding: '8px 18px', fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.82rem', color: '#fff' }}>
                    {pill}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ══ SECTION 4 — Reduction ═════════════════════════════════════════ */}
        <section id="reduction" className="dash-section">
          <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 24px', marginBottom: '40px' }}>
            <SectionLabel>Dimensionality Reduction</SectionLabel>
            <SectionTitle>PCA & LDA Analysis</SectionTitle>
          </div>

          <div className="dash-grid">
            <div className="reveal glass-hover" style={{ ...glass, gridColumn: 'span 6' }}>
              <div style={{ ...holoStyle, fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: '1.1rem', marginBottom: '6px' }}>
                Principal Component Analysis
              </div>
              <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)', marginBottom: '24px' }}>
                Unsupervised · No label leakage
              </div>
              <ProgressBar label="Frequency / Monetary axis" pct="71.78%" gradient="linear-gradient(90deg,#C9A0CB,#9FCEEE)" delay={0}   />
              <ProgressBar label="Recency axis"              pct="20.97%" gradient="linear-gradient(90deg,#C9A0CB,#9FCEEE)" delay={150} />
              <ProgressBar label="Residual variance"         pct="7.25%"  gradient="linear-gradient(90deg,#C9A0CB,#9FCEEE)" delay={300} />
              <div style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(201,160,203,0.2)', borderRadius: '12px', padding: '14px', marginTop: '8px' }}>
                <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem', color: '#fff' }}>
                  92.75% variance captured in just 2 components
                </span>
              </div>
            </div>

            <div className="reveal glass-hover" style={{ ...glass, gridColumn: 'span 6' }}>
              <div style={{ ...holoStyle, fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: '1.1rem', marginBottom: '6px' }}>
                Linear Discriminant Analysis
              </div>
              <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)', marginBottom: '24px' }}>
                Applied post-clustering · visualization only
              </div>
              <ProgressBar label="Primary segment separator" pct="95.39%" gradient="linear-gradient(90deg,#F4BBD7,#A98BD1)" delay={0}   />
              <ProgressBar label="Secondary separation"      pct="4.60%"  gradient="linear-gradient(90deg,#F4BBD7,#A98BD1)" delay={150} />
              <div style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(201,160,203,0.2)', borderRadius: '12px', padding: '14px', marginTop: '8px' }}>
                <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem', color: '#fff' }}>
                  LD1 alone separates all 4 customer segments
                </span>
              </div>
              <div style={{ fontFamily: "'Inter', sans-serif", fontStyle: 'italic', fontWeight: 300, fontSize: '0.75rem', color: 'rgba(255,255,255,0.3)', marginTop: '12px' }}>
                No label leakage — LDA applied after K-Means clustering
              </div>
            </div>
          </div>
        </section>

        {/* ══ SECTION 5 — Revenue ══════════════════════════════════════════ */}
        <section id="revenue" className="dash-section">
          <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 24px', marginBottom: '40px' }}>
            <SectionLabel>Revenue Analysis</SectionLabel>
            <SectionTitle>Monthly Revenue Trend</SectionTitle>
          </div>

          <div className="dash-grid">
            <div className="reveal glass-hover" style={{ ...glass, gridColumn: 'span 12', height: '420px', position: 'relative' }}>
              <div style={{
                position: 'absolute', right: '160px', top: '30px', zIndex: 10,
                background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)',
                border: '1px solid rgba(255,255,255,0.2)', borderRadius: '12px', padding: '10px 16px', textAlign: 'center',
              }}>
                <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, fontSize: '0.85rem', color: '#fff' }}>Peak: £647,874</div>
                <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>November 2011</div>
                <div style={{ width: '2px', height: '30px', background: 'rgba(255,255,255,0.3)', margin: '8px auto 0' }} />
              </div>

              <div style={{ height: '100%' }}>
                <Line
                  data={{
                    labels: ['Dec 10','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov 11','Dec 11'],
                    datasets: [{
                      data: [48,52,45,62,55,68,58,61,63,98,124,648,43],
                      borderColor: '#C9A0CB', borderWidth: 2.5, tension: 0.4, fill: true,
                      backgroundColor: (ctx) => {
                        const { chart } = ctx;
                        const { chartArea } = chart;
                        if (!chartArea) return 'rgba(201,160,203,0.2)';
                        const g = chart.ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                        g.addColorStop(0, 'rgba(201,160,203,0.4)');
                        g.addColorStop(1, 'rgba(201,160,203,0)');
                        return g;
                      },
                      pointRadius:          [3,3,3,3,3,3,3,3,3,3,3,10,3],
                      pointBackgroundColor: ['#C9A0CB','#C9A0CB','#C9A0CB','#C9A0CB','#C9A0CB','#C9A0CB','#C9A0CB','#C9A0CB','#C9A0CB','#C9A0CB','#C9A0CB','#ffffff','#C9A0CB'],
                    }],
                  }}
                  options={{
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'rgba(255,255,255,0.4)' } },
                      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'rgba(255,255,255,0.4)' } },
                    },
                  }}
                />
              </div>
            </div>
          </div>
        </section>

        {/* ══ SECTION 6 — Market Basket ════════════════════════════════════ */}
        <section id="basket" className="dash-section">
          <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 24px', marginBottom: '40px' }}>
            <SectionLabel>Market Basket Analysis</SectionLabel>
            <SectionTitle>Association Rules</SectionTitle>
          </div>

          <div className="dash-grid" style={{ marginBottom: '20px' }}>
            {/* Horizontal bar chart */}
            <div className="reveal glass-hover" style={{ ...glass, gridColumn: 'span 7', height: '320px' }}>
              <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: '0.9rem', color: 'rgba(255,255,255,0.6)', marginBottom: '12px' }}>
                Top Association Rules by Lift
              </div>
              <div style={{ height: 'calc(100% - 36px)' }}>
                <Bar
                  data={{
                    labels: ['Green+Roses→Pink Teacup','Pink→Green+Roses Teacup','Pink+Roses→Green Teacup','Bag Red→Bag Spaceboy','Bag Spaceboy→Bag Cars'],
                    datasets: [{
                      data: [21.23, 21.23, 21.11, 16.20, 14.85],
                      backgroundColor: (ctx) => {
                        const { chart } = ctx;
                        const { chartArea } = chart;
                        if (!chartArea) return 'rgba(201,160,203,0.9)';
                        const g = chart.ctx.createLinearGradient(chartArea.right, 0, chartArea.left, 0);
                        g.addColorStop(0, 'rgba(201,160,203,0.9)');
                        g.addColorStop(1, 'rgba(159,206,238,0.6)');
                        return g;
                      },
                      borderRadius: 6,
                    }],
                  }}
                  options={{
                    indexAxis: 'y',
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                      x: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: 'rgba(255,255,255,0.4)' } },
                      y: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: 'rgba(255,255,255,0.4)', font: { size: 11 } } },
                    },
                  }}
                />
              </div>
            </div>

            {/* Lift callout */}
            <div className="reveal glass-hover" style={{
              ...glass, gridColumn: 'span 5',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center',
              animation: 'pulseGlow 3s infinite',
              border: '1px solid rgba(201,160,203,0.25)',
            }}>
              <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: '1.1rem', color: '#fff', marginBottom: '8px' }}>
                Regency Teacup Bundle
              </div>
              <div style={{ ...holoStyle, fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: '4rem', filter: 'drop-shadow(0 0 30px rgba(201,160,203,0.5))' }}>
                21.23×
              </div>
              <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)', marginBottom: '16px' }}>
                Lift Score
              </div>
              <div style={{ width: '100%', height: '1px', background: 'rgba(255,255,255,0.08)', marginBottom: '16px' }} />
              <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.82rem', color: 'rgba(255,255,255,0.55)', lineHeight: 1.6 }}>
                Strongest product association found consistently across all 4 customer segments
              </div>
            </div>
          </div>

          {/* Rules table */}
          <div className="dash-grid">
            <div className="reveal glass-hover" style={{ ...glass, gridColumn: 'span 12' }}>
              <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, fontSize: '1rem', color: '#fff', marginBottom: '16px' }}>
                Complete Rule Set
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr 1fr 1fr', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '10px', marginBottom: '4px' }}>
                {['Antecedent → Consequent', 'Support', 'Confidence', 'Lift'].map(h => (
                  <div key={h} style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.72rem', letterSpacing: '0.1em', color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase' }}>{h}</div>
                ))}
              </div>
              {RULES.map((row, i) => (
                <div key={i} className="reveal" style={{
                  display: 'grid', gridTemplateColumns: '3fr 1fr 1fr 1fr', alignItems: 'center',
                  background: i % 2 === 0 ? 'rgba(255,255,255,0.03)' : 'transparent',
                  borderBottom: '1px solid rgba(255,255,255,0.04)',
                  padding: '14px 0',
                }}>
                  <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem', color: '#fff', paddingRight: '12px' }}>{row[0]}</div>
                  <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem', color: '#fff' }}>{row[1]}</div>
                  <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem', color: '#fff' }}>{row[2]}</div>
                  <div style={{ ...holoStyle, fontFamily: "'Syne', sans-serif", fontWeight: 600, fontSize: '0.9rem' }}>{row[3]}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ══ SECTION 7 — Insights ═════════════════════════════════════════ */}
        <section id="insights" className="dash-section">
          <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 24px', marginBottom: '40px' }}>
            <SectionLabel>Business Insights</SectionLabel>
            <SectionTitle>Action Plan by Segment</SectionTitle>
          </div>

          <div className="dash-grid">
            {SEGMENT_DATA.map(seg => <FlipCard key={seg.name} seg={seg} />)}
          </div>
        </section>

        {/* ══ Footer ═══════════════════════════════════════════════════════ */}
        <footer style={{ borderTop: '1px solid rgba(255,255,255,0.06)', padding: '48px 24px', textAlign: 'center', background: 'rgba(0,0,0,0.3)' }}>
          <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 400, fontSize: '0.9rem', color: 'rgba(255,255,255,0.3)', letterSpacing: '0.1em' }}>
            Woxsen University · ML PBL
          </div>
          <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.8rem', color: 'rgba(255,255,255,0.2)', marginTop: '8px' }}>
            Sai Rishitha · 24WU0101123 &nbsp;·&nbsp; Dumpati Vedha Sri · 24WU0104032 &nbsp;·&nbsp; Poojitha Arigela · 24WU0101144 &nbsp;·&nbsp; Sanjana Jain · 24WU0104094T
          </div>
          <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.75rem', color: 'rgba(255,255,255,0.15)', marginTop: '4px' }}>
            Online Retail Market Basket Analysis & Customer Clustering
          </div>
        </footer>

      </div>
    </div>
  );
}
