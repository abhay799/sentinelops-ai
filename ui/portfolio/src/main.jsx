import { createRoot } from "react-dom/client";
import { ArrowRight, ExternalLink, TerminalSquare } from "lucide-react";
import { docLinks, layers, lifecycle, previews, scenarios } from "./content.js";
import "./styles.css";

const Link = ({ href, children, className = "", ...rest }) => <a className={className} href={href} {...rest}>{children}</a>;

function Section({ id, eyebrow, title, children }) {
  return <section id={id} className="section"><div className="section-heading"><span>{eyebrow}</span><h2>{title}</h2></div>{children}</section>;
}

function App() {
  return <main>
    <header className="nav-wrap">
      <nav aria-label="Primary navigation" className="nav"><a className="brand" href="#top"><span className="brand-mark">S</span><span>SentinelOps <small>AI</small></span></a><div className="nav-links"><a href="#system">System</a><a href="#safety">Safety</a><a href="#evidence">Evidence</a><a href="#docs">Docs</a></div><Link className="nav-cta" href="./control-center/">Open Control Center <ArrowRight size={14} /></Link></nav>
    </header>

    <section id="top" className="hero section">
      <div className="hero-copy"><p className="eyebrow">RELIABILITY ENGINEERING PORTFOLIO PROJECT</p><h1>SentinelOps <em>AI</em></h1><p className="hero-title">Autonomous Reliability Intelligence &amp; Failure Prevention Platform</p><p className="lede">An engineering project exploring evidence-grounded reliability intelligence, causal investigation, counterfactual decision support, and safety-gated local remediation.</p><div className="actions"><Link className="button primary" href="./control-center/">Open Control Center <ArrowRight size={16} /></Link><Link className="button" href="https://github.com/abhay799/sentinelops-ai/blob/main/docs/architecture/PROJECT_ARCHITECTURE.md">View Architecture</Link><Link className="text-link" href="https://github.com/abhay799/sentinelops-ai/blob/main/docs/evidence/BENCHMARKS_AND_EVIDENCE.md">View Evidence <ExternalLink size={13} /></Link></div></div>
      <div className="hero-card" aria-label="Current project boundaries"><div className="card-top"><span>CONTROL BOUNDARY</span><span className="status">LOCAL LAB</span></div><div className="signal"><i></i><div><strong>Evidence-grounded flow</strong><small>DETERMINISTIC · SYNTHETIC · NOT CONNECTED</small></div></div><div className="flow-mini"><span>Signal</span><b>→</b><span>Hypothesis</span><b>→</b><span>Guard</span><b>→</b><span>Human</span><b>→</b><span>Sandbox</span></div><p>Production infrastructure and telemetry are <strong>NOT CONNECTED</strong>. Production performance is <strong>NOT MEASURED</strong>.</p></div>
    </section>

    <Section id="problem" eyebrow="THE ENGINEERING PROBLEM" title="From fragmented signals to cautious decisions.">
      <div className="problem-grid"><p>Modern distributed failures generate fragmented telemetry and ambiguous causal signals. Traditional monitoring can identify that something is broken. SentinelOps explores what is happening, what may fail, what supports or contradicts a leading hypothesis, and whether an intervention is safe enough to propose.</p><ul className="questions"><li>What evidence supports the leading hypothesis?</li><li>What contradicts it?</li><li>What intervention is safer?</li><li>Is action authorized, and did recovery succeed?</li></ul></div>
    </Section>

    <Section id="lifecycle" eyebrow="CORE LIFECYCLE" title="A reliability loop with an explicit human boundary.">
      <div className="lifecycle" aria-label="SentinelOps reliability lifecycle">{lifecycle.map((step, index) => <div key={step} className={step === "Human Authorization" ? "life-step human" : "life-step"}><span>{String(index + 1).padStart(2, "0")}</span><strong>{step}</strong></div>)}</div>
    </Section>

    <Section id="system" eyebrow="ARCHITECTURE / ENGINEERING SYSTEM" title="A connected chain of reliability capabilities.">
      <div className="layer-grid">{layers.map((layer, index) => <div className="layer" key={layer}><span>{String(index + 1).padStart(2, "0")}</span>{layer}</div>)}</div><Link className="text-link below" href="https://github.com/abhay799/sentinelops-ai/blob/main/docs/architecture/PROJECT_ARCHITECTURE.md">Inspect the architecture documentation <ArrowRight size={13} /></Link>
    </Section>

    <Section id="safety" eyebrow="SAFETY MODEL" title="No remediation without accountable controls.">
      <div className="safety"><div className="invariant"><span>NO REMEDIATION WITHOUT</span><div>{["Evidence", "Confidence", "Safety", "Authorization", "Rollback", "Verification"].map((word) => <b key={word}>{word}</b>)}</div></div><div className="safety-copy"><p className="equation">Planner Recommendation <i>≠</i> SentinelGuard Approval <i>≠</i> Human Authorization <i>≠</i> Execution</p><ul><li>Fail-closed control flow</li><li>Agents have no execution authority or independent RCA-confirmation authority</li><li>Agents cannot bypass SentinelGuard or human approval</li><li><code>rollback</code> is the only configured sandbox execution adapter</li></ul></div></div>
    </Section>

    <Section id="preview" eyebrow="CONTROL CENTER PREVIEW" title="The deep operational interface.">
      <p className="section-intro">Real rendered captures can replace these frames after reproducible browser capture. Until then, no screenshots are represented as captured.</p><div className="preview-grid">{previews.map(([title, filename, scenario, detail]) => <article className="preview" key={title}><div className="placeholder"><TerminalSquare size={24} /><strong>SCREENSHOT PENDING CAPTURE</strong><span>{filename}</span></div><h3>{title}</h3><p>{detail}</p><small>Scenario: <code>{scenario}</code></small></article>)}</div><Link className="text-link below" href="https://github.com/abhay799/sentinelops-ai/blob/main/docs/media/CAPTURE_GUIDE.md">Open reproducible capture guide <ArrowRight size={13} /></Link>
    </Section>

    <Section id="scenarios" eyebrow="DETERMINISTIC DEMO SCENARIOS" title="Nine engineering demonstrations, not incident history.">
      <div className="scenario-grid">{scenarios.map(([name, description]) => <article key={name}><code>{name}</code><p>{description}</p></article>)}</div>
    </Section>

    <Section id="evidence" eyebrow="ENGINEERING EVIDENCE" title="Evidence is classified before it is presented.">
      <div className="evidence-grid"><div className="tags">{["IMPLEMENTED", "MEASURED DEVELOPMENT DATA", "SYNTHETIC", "SIMULATED", "DETERMINISTIC", "LOCAL", "NOT CONNECTED", "NOT MEASURED"].map((tag) => <span key={tag}>{tag}</span>)}</div><div className="metrics"><p>Historical Phase 10 measurements</p><div><strong>0.2778</strong><span>Precision</span><strong>1.0000</strong><span>Recall</span><strong>0.4348</strong><span>F1</span><strong>1.8</strong><span>Average lead events</span></div><small>DEVELOPMENT DATA · SYNTHETIC CONTEXT · NOT PRODUCTION-CALIBRATED</small></div></div><Link className="text-link below" href="https://github.com/abhay799/sentinelops-ai/blob/main/docs/evidence/BENCHMARKS_AND_EVIDENCE.md">Read benchmarks and evidence <ArrowRight size={13} /></Link>
    </Section>

    <Section id="stack" eyebrow="TECHNOLOGY / ENGINEERING STACK" title="Built from repository-backed components.">
      <div className="stack-grid"><article><h3>Backend / Intelligence</h3><p>Python · FastAPI · NetworkX · scikit-learn</p></article><article><h3>Observability</h3><p>Prometheus · OpenTelemetry · Grafana</p></article><article><h3>Distributed Infrastructure</h3><p>PostgreSQL · Redis · Kafka · Docker Compose</p></article><article><h3>Frontend</h3><p>React · Vite · JavaScript</p></article><article><h3>Validation / Evidence</h3><p>pytest · Node built-in tests · JSON evidence manifest</p></article></div>
    </Section>

    <Section id="phases" eyebrow="PHASE 0–15 MAP" title="An implemented progression with stated boundaries.">
      <div className="phase-grid">{[["Foundation", "0–4", "Runtime foundations, telemetry, and features"], ["Intelligence", "5–9", "Anomaly, graph, incidents, RCA, and challenge"], ["Prediction / Decision Support", "10–12", "Early warning, simulation, impact, and priority"], ["Safe Remediation", "13–14", "Planning, Guard, authorization gate, local execution"], ["Grounded Investigation", "15", "Evidence-bound investigation provider"]].map(([name, phase, detail]) => <article key={name}><span>PHASES {phase}</span><h3>{name}</h3><p>{detail}</p><small>IMPLEMENTED</small></article>)}</div>
    </Section>

    <Section id="boundaries" eyebrow="CURRENT BOUNDARIES" title="Credibility comes from what is not claimed.">
      <div className="boundary-grid">{[["Production Infrastructure", "NOT CONNECTED"], ["Production Telemetry", "NOT CONNECTED"], ["Production Benchmark", "NOT MEASURED"], ["Controlled Remediation", "LOCAL SANDBOX"], ["Counterfactuals", "SIMULATED"], ["Phase 15 Provider", "DETERMINISTIC"], ["Human Authorization", "REQUIRED"]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
    </Section>

    <Section id="docs" eyebrow="DOCUMENTATION / NEXT STEP" title="Inspect the engineering record.">
      <div className="docs-grid">{docLinks.map(([label, href]) => <Link key={label} href={href}>{label}<ArrowRight size={15} /></Link>)}</div>
    </Section>

    <footer><div className="brand"><span className="brand-mark">S</span><span>SentinelOps <small>AI</small></span></div><p>Engineering portfolio project · LOCAL · SYNTHETIC · DETERMINISTIC · NOT CONNECTED</p><a href="#top">Back to top ↑</a></footer>
  </main>;
}

createRoot(document.getElementById("root")).render(<App />);
