import { useEffect, useRef, useState } from 'react';

// ─── Reusable sub-components ──────────────────────────────────────────────────

const Pill = ({ children }) => (
  <div style={{
    background: 'rgba(255,255,255,0.1)',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    border: '1px solid rgba(255,255,255,0.2)',
    borderRadius: '999px',
    padding: '6px 18px',
    fontFamily: "'Inter', sans-serif",
    fontWeight: 400,
    fontSize: '0.75rem',
    letterSpacing: '0.1em',
    color: 'rgba(255,255,255,0.7)',
    textTransform: 'uppercase',
    marginBottom: '20px',
  }}>
    {children}
  </div>
);

const HoloTitle = ({ children, style = {} }) => (
  <h2 style={{
    fontFamily: "'Syne', sans-serif",
    fontWeight: 800,
    fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
    lineHeight: 1.1,
    marginBottom: '20px',
    color: '#fff',
    filter: 'drop-shadow(0 0 30px rgba(201,160,203,0.5)) drop-shadow(0 0 60px rgba(159,206,238,0.3))',
    ...style,
  }}>
    {children}
  </h2>
);

const Body = ({ children }) => (
  <p style={{
    fontFamily: "'Inter', sans-serif",
    fontWeight: 300,
    fontSize: 'clamp(1rem, 2vw, 1.2rem)',
    color: 'rgba(255,255,255,0.65)',
    maxWidth: '600px',
    textAlign: 'center',
    lineHeight: 1.7,
    marginBottom: '16px',
  }}>
    {children}
  </p>
);

const Sub = ({ children }) => (
  <p style={{
    fontFamily: "'Inter', sans-serif",
    fontWeight: 300,
    fontSize: '0.85rem',
    color: 'rgba(255,255,255,0.35)',
    letterSpacing: '0.05em',
    textAlign: 'center',
  }}>
    {children}
  </p>
);

const Watermark = ({ num }) => (
  <div style={{
    position: 'absolute',
    bottom: '40px',
    left: '40px',
    fontFamily: "'Syne', sans-serif",
    fontWeight: 800,
    fontSize: '18rem',
    color: '#fff',
    opacity: 0.06,
    lineHeight: 1,
    userSelect: 'none',
    pointerEvents: 'none',
    zIndex: 0,
  }}>
    {num}
  </div>
);

// Stage wrapper — fade + scale on active
const sw = (active) => ({
  position: 'absolute',
  inset: 0,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '40px',
  opacity: active ? 1 : 0,
  transform: active ? 'translateY(0) scale(1)' : 'translateY(30px) scale(0.96)',
  transition: 'opacity 0.7s ease, transform 0.7s ease',
  pointerEvents: active ? 'auto' : 'none',
  zIndex: 2,
});

// ─── Segment data for Stage 03 ─────────────────────────────────────────────
const SEGMENTS = [
  { name: 'Platinum', dot: '#c9972a', stat: '679 · 56.9% rev' },
  { name: 'Loyal',     dot: '#4a8a4a', stat: '1,174 · 29.3% rev' },
  { name: 'At Risk',   dot: '#c97a2a', stat: '891 · 10.5% rev' },
  { name: 'Lost',      dot: '#8a3a3a', stat: '1,447 · 3.3% rev' },
];

// ─── Metric card data for Stage 04 ────────────────────────────────────────
const CARDS = [
  { name: 'K-Means',      score: '0.4343', winner: true,  alpha: 1.0 },
  { name: 'DBSCAN',       score: '-0.02',  winner: false, alpha: 0.4 },
  { name: 'Hierarchical', score: '0.36',   winner: false, alpha: 0.6 },
];

// ─── easeOutQuart ──────────────────────────────────────────────────────────
const easeOutQuart = (t) => 1 - Math.pow(1 - t, 4);

// ══════════════════════════════════════════════════════════════════════════════
export default function Story() {
  const wrapperRef = useRef(null);

  const [active, setActive]   = useState(0);
  const [inStory, setInStory] = useState(false);

  // Stage 01 — animated counter
  const [counter, setCounter] = useState(0);

  // Stage 02 — bar widths
  const [barsIn, setBarsIn] = useState(false);

  // Stage 03 — segment pill stagger
  const [pillVis, setPillVis] = useState([false, false, false, false]);

  // Stage 04 — metric card stagger
  const [cardVis, setCardVis] = useState([false, false, false]);

  // Stage 05 — association reveal
  const [assocIn, setAssocIn] = useState(false);

  // ── Scroll-based stage + visibility detection ─────────────────────────────
  useEffect(() => {
    const onScroll = () => {
      if (!wrapperRef.current) return;
      const rect      = wrapperRef.current.getBoundingClientRect();
      const scrolled  = -rect.top;                          // px scrolled past story top
      const vh        = window.innerHeight;

      setInStory(scrolled > -vh * 0.5 && scrolled < vh * 5);

      if (scrolled < 0) return;
      const stage = Math.min(4, Math.floor(scrolled / vh));
      setActive(prev => (prev !== stage ? stage : prev));
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // ── Per-stage entrance animations ─────────────────────────────────────────
  useEffect(() => {
    const timers = [];

    if (active === 0) {
      const target    = 541909;
      const duration  = 2200;
      const startTime = performance.now();
      let raf;
      const step = (now) => {
        const t = Math.min((now - startTime) / duration, 1);
        setCounter(Math.floor(easeOutQuart(t) * target));
        if (t < 1) raf = requestAnimationFrame(step);
      };
      raf = requestAnimationFrame(step);
      return () => cancelAnimationFrame(raf);
    }

    if (active === 1) {
      setBarsIn(false);
      timers.push(setTimeout(() => setBarsIn(true), 80));
    }

    if (active === 2) {
      setPillVis([false, false, false, false]);
      [0, 1, 2, 3].forEach(i =>
        timers.push(setTimeout(() =>
          setPillVis(v => { const n = [...v]; n[i] = true; return n; }),
          150 + i * 150
        ))
      );
    }

    if (active === 3) {
      setCardVis([false, false, false]);
      [0, 1, 2].forEach(i =>
        timers.push(setTimeout(() =>
          setCardVis(v => { const n = [...v]; n[i] = true; return n; }),
          150 + i * 200
        ))
      );
    }

    if (active === 4) {
      setAssocIn(false);
      timers.push(setTimeout(() => setAssocIn(true), 200));
    }

    return () => timers.forEach(clearTimeout);
  }, [active]);

  // ── Dot click → scroll to stage ──────────────────────────────────────────
  const scrollToStage = (i) => {
    if (!wrapperRef.current) return;
    const top = wrapperRef.current.getBoundingClientRect().top + window.scrollY + i * window.innerHeight;
    window.scrollTo({ top, behavior: 'smooth' });
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <>
      {/* ══ 500 vh outer wrapper ══ */}
      <div ref={wrapperRef} style={{ height: '500vh', position: 'relative' }}>

        {/* Sticky viewport */}
        <div style={{
          position: 'sticky',
          top: 0,
          height: '100vh',
          overflow: 'hidden',
          background: '#000',
        }}>
          {/* Aurora layers (CSS classes from index.css) */}
          <div className="aurora-layer-1" />
          <div className="aurora-layer-2" />

          {/* ── Stage 01 — The Raw Data ────────────────────────────────── */}
          <div style={sw(active === 0)}>
            <Watermark num="01" />
            <Pill>Dataset</Pill>
            <HoloTitle>541,909 Transactions</HoloTitle>

            {/* Animated counter */}
            <div style={{
              fontFamily: "'Syne', sans-serif",
              fontWeight: 800,
              fontSize: '5rem',
              lineHeight: 1,
              marginBottom: '32px',
              color: '#fff',
              filter: 'drop-shadow(0 0 24px rgba(201,160,203,0.5))',
              fontVariantNumeric: 'tabular-nums',
            }}>
              {counter.toLocaleString()}
            </div>

            <Body>
              One UK online retailer. One full year of customer behavior. Every purchase,
              every product, every pattern — waiting to be decoded.
            </Body>
            <Sub>Source: UCI Machine Learning Repository · Dec 2010 → Dec 2011</Sub>
          </div>

          {/* ── Stage 02 — The Cleaning ────────────────────────────────── */}
          <div style={sw(active === 1)}>
            <Watermark num="02" />
            <Pill>Preprocessing</Pill>
            <HoloTitle>338,151 Clean Rows</HoloTitle>

            {/* Animated bars */}
            <div style={{
              width: '100%', maxWidth: '600px',
              display: 'flex', flexDirection: 'column', gap: '12px',
              marginBottom: '32px',
            }}>
              {[
                { label: 'Raw Dataset',    value: '541,909', pct: '100%', bg: 'rgba(255,255,255,0.15)',                    delay: '0s'   },
                { label: 'After Cleaning', value: '397,884', pct: '73%',  bg: 'rgba(201,160,203,0.5)',                    delay: '0.2s' },
                { label: 'Final Dataset',  value: '338,151', pct: '62%',  bg: 'linear-gradient(90deg,#C9A0CB,#9FCEEE)',  delay: '0.4s' },
              ].map(bar => (
                <div key={bar.label} style={{
                  width: barsIn ? bar.pct : '0%',
                  height: '48px',
                  borderRadius: '999px',
                  background: bar.bg,
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0 20px',
                  justifyContent: 'space-between',
                  overflow: 'hidden',
                  whiteSpace: 'nowrap',
                  transition: `width 0.8s cubic-bezier(0.23,1,0.32,1) ${bar.delay}`,
                  minWidth: '0px',
                }}>
                  <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem', color: '#fff' }}>{bar.label}</span>
                  <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.85rem', color: '#fff', fontVariantNumeric: 'tabular-nums' }}>{bar.value}</span>
                </div>
              ))}
            </div>

            <Body>
              203,758 rows removed. Nulls, cancellations, negative quantities, zero prices
              and outliers — eliminated.
            </Body>
            <Sub>IQR outlier removal · StandardScaler · MinMaxScaler comparison</Sub>
          </div>

          {/* ── Stage 03 — The Customers ───────────────────────────────── */}
          <div style={sw(active === 2)}>
            <Watermark num="03" />
            <Pill>RFM Analysis</Pill>
            <HoloTitle>4,191 Unique Customers</HoloTitle>

            {/* Segment pills with stagger */}
            <div style={{
              display: 'flex', flexDirection: 'column', gap: '12px',
              marginBottom: '32px', width: '100%', maxWidth: '480px',
            }}>
              {SEGMENTS.map((seg, i) => (
                <div key={seg.name} style={{
                  background: 'rgba(255,255,255,0.08)',
                  backdropFilter: 'blur(10px)',
                  WebkitBackdropFilter: 'blur(10px)',
                  borderRadius: '999px',
                  padding: '14px 28px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  opacity: pillVis[i] ? 1 : 0,
                  transform: pillVis[i] ? 'translateY(0)' : 'translateY(20px)',
                  transition: 'opacity 0.5s ease, transform 0.5s ease',
                }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: seg.dot, flexShrink: 0 }} />
                  <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: '0.95rem', color: '#fff', flex: 1 }}>
                    {seg.name}
                  </span>
                  <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)', fontVariantNumeric: 'tabular-nums' }}>
                    {seg.stat}
                  </span>
                </div>
              ))}
            </div>

            <Body>
              RFM analysis transformed raw transactions into 4 distinct behavioral segments.
            </Body>
            <Sub>Recency · Frequency · Monetary · Log transformation applied</Sub>
          </div>

          {/* ── Stage 04 — The Algorithm ───────────────────────────────── */}
          <div style={sw(active === 3)}>
            <Watermark num="04" />
            <Pill>Clustering</Pill>
            <HoloTitle>K-Means Wins</HoloTitle>

            {/* Metric cards */}
            <div style={{
              display: 'flex', gap: '12px',
              justifyContent: 'center', alignItems: 'center',
              flexWrap: 'wrap',
              marginBottom: '32px',
            }}>
              {CARDS.map((card, i) => (
                <div key={card.name} style={{
                  width: '150px', minWidth: '150px', maxWidth: '150px',
                  overflow: 'hidden',
                  textAlign: 'center',
                  padding: '20px 12px',
                  background: 'rgba(255,255,255,0.06)',
                  backdropFilter: 'blur(20px)',
                  WebkitBackdropFilter: 'blur(20px)',
                  borderRadius: '16px',
                  boxSizing: 'border-box',
                  boxShadow: 'inset 0 0 0 1px rgba(201,160,203,0.3)',
                  opacity: cardVis[i] ? 1 : 0,
                  transform: cardVis[i] ? 'translateY(0)' : 'translateY(24px)',
                  transition: 'opacity 0.5s ease, transform 0.5s ease',
                }}>
                  {card.winner && (
                    <div style={{
                      background: 'linear-gradient(135deg,#C9A0CB,#9FCEEE)',
                      color: '#000',
                      borderRadius: '999px',
                      padding: '3px 10px',
                      fontFamily: "'Inter', sans-serif",
                      fontWeight: 600,
                      fontSize: '0.7rem',
                      marginBottom: '12px',
                      display: 'inline-block',
                    }}>
                      WINNER
                    </div>
                  )}

                  {card.winner ? (
                    <div style={{
                      fontFamily: "'Syne', sans-serif",
                      fontWeight: 800,
                      fontSize: 'clamp(1rem,2.5vw,1.8rem)',
                      marginBottom: '8px',
                      color: '#fff',
                      fontVariantNumeric: 'tabular-nums',
                      letterSpacing: '-0.02em',
                      whiteSpace: 'nowrap',
                      display: 'block',
                      width: '100%',
                    }}>
                      {card.score}
                    </div>
                  ) : (
                    <div style={{
                      fontFamily: "'Syne', sans-serif",
                      fontWeight: 800,
                      fontSize: 'clamp(1rem,2.5vw,1.8rem)',
                      color: `rgba(255,255,255,${card.alpha})`,
                      marginBottom: '8px',
                      fontVariantNumeric: 'tabular-nums',
                      letterSpacing: '-0.02em',
                      whiteSpace: 'nowrap',
                      display: 'block',
                      width: '100%',
                    }}>
                      {card.score}
                    </div>
                  )}

                  <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 300, fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', marginBottom: '6px' }}>
                    Silhouette Score
                  </div>
                  <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '0.8rem', color: 'rgba(255,255,255,0.7)' }}>
                    {card.name}
                  </div>
                </div>
              ))}
            </div>

            <Body>
              Three algorithms. Three distance metrics. One clear winner —
              K-Means with Euclidean distance.
            </Body>
            <Sub>Validated · Silhouette Score · Davies-Bouldin · Calinski-Harabasz</Sub>
          </div>

          {/* ── Stage 05 — The Discovery ───────────────────────────────── */}
          <div style={sw(active === 4)}>
            <Watermark num="05" />
            <Pill>Market Basket</Pill>
            <HoloTitle>Lift = 21.23×</HoloTitle>

            {/* Product association */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexWrap: 'wrap',
              gap: '8px',
              marginBottom: '20px',
              opacity: assocIn ? 1 : 0,
              transform: assocIn ? 'translateY(0)' : 'translateY(20px)',
              transition: 'opacity 0.6s ease, transform 0.6s ease',
            }}>
              <div className="glass-card" style={{ padding: '16px 28px' }}>
                <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: '0.95rem', color: '#fff' }}>
                  Green Regency Teacup
                </span>
              </div>

              <div style={{
                fontFamily: "'Syne', sans-serif",
                fontWeight: 800,
                fontSize: '2.5rem',
                margin: '0 12px',
                color: '#fff',
                filter: 'drop-shadow(0 0 20px rgba(201,160,203,0.6))',
              }}>
                →
              </div>

              <div className="glass-card" style={{ padding: '16px 28px' }}>
                <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: '0.95rem', color: '#fff' }}>
                  Pink Regency Teacup
                </span>
              </div>
            </div>

            {/* Lift score */}
            <div style={{
              fontFamily: "'Syne', sans-serif",
              fontWeight: 800,
              fontSize: '3.5rem',
              lineHeight: 1,
              color: '#fff',
              filter: 'drop-shadow(0 0 30px rgba(201,160,203,0.5)) drop-shadow(0 0 60px rgba(159,206,238,0.3))',
              opacity: assocIn ? 1 : 0,
              transition: 'opacity 0.6s ease 0.25s',
              marginBottom: '6px',
              fontVariantNumeric: 'tabular-nums',
            }}>
              21.23×
            </div>
            <div style={{
              fontFamily: "'Inter', sans-serif",
              fontWeight: 300,
              fontSize: '0.8rem',
              color: 'rgba(255,255,255,0.4)',
              marginBottom: '28px',
            }}>
              Lift Score
            </div>

            <Body>
              The Regency Teacup bundle — the strongest product association across
              all 4 customer segments.
            </Body>
            <Sub>
              Apriori algorithm · 86 global association rules discovered ·
              Consistent across Platinum, Loyal, At Risk and Lost
            </Sub>
          </div>

        </div>{/* /sticky */}
      </div>{/* /500vh */}

      {/* ── Progress dots (fixed, visible only inside story) ────────────── */}
      {inStory && (
        <div style={{
          position: 'fixed',
          bottom: '32px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 50,
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          {[0, 1, 2, 3, 4].map(i => (
            <div
              key={i}
              onClick={() => scrollToStage(i)}
              style={{
                width:        active === i ? '12px' : '8px',
                height:       active === i ? '12px' : '8px',
                borderRadius: '50%',
                background:   active === i
                  ? 'linear-gradient(135deg,#C9A0CB,#9FCEEE)'
                  : 'rgba(255,255,255,0.2)',
                border:       active === i ? 'none' : '1px solid rgba(255,255,255,0.3)',
                boxShadow:    active === i ? '0 0 12px rgba(201,160,203,0.6)' : 'none',
                transition:   'all 0.3s ease',
                cursor:       'pointer',
              }}
            />
          ))}
        </div>
      )}
    </>
  );
}
