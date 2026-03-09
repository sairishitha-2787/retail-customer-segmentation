export default function AuroraBackground({ children }) {
  return (
    <section className="aurora-container">
      <div className="aurora-layer-1" />
      <div className="aurora-layer-2" />
      {children}
    </section>
  );
}
