import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Clock3,
  ShieldCheck,
} from "lucide-react";

const incidents = [
  {
    id: "INC-0001",
    severity: "HIGH",
    service: "payment-service",
    candidate: "payment-service",
    disposition: "Supported candidate",
    guard: "Approved",
    recovery: "Verified",
    status: "Resolved",
  },
  {
    id: "INC-0002",
    severity: "MEDIUM",
    service: "order-service",
    candidate: "order-service",
    disposition: "Inconclusive",
    guard: "Not evaluated",
    recovery: "N/A",
    status: "Investigating",
  },
];

export default function Incidents() {
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="eyebrow">INCIDENT INTELLIGENCE</div>
          <h1>Incidents</h1>
          <p className="page-description">
            Correlated reliability incidents with RCA, safety and recovery state.
          </p>
        </div>
      </div>

      <div className="incident-summary-grid">
        <div className="small-stat">
          <span>Active</span>
          <strong>1</strong>
        </div>

        <div className="small-stat">
          <span>High priority</span>
          <strong className="warning-text">1</strong>
        </div>

        <div className="small-stat">
          <span>Recovered</span>
          <strong className="positive">1</strong>
        </div>

        <div className="small-stat">
          <span>Awaiting RCA</span>
          <strong>1</strong>
        </div>
      </div>

      <div className="panel incidents-table-panel">
        <div className="panel-heading">
          <div>
            <div className="panel-title">Incident Queue</div>
            <div className="panel-subtitle">
              Evidence-correlated incident records
            </div>
          </div>
        </div>

        <div className="incident-table">
          <div className="incident-table-head">
            <span>Incident</span>
            <span>Service</span>
            <span>RCA disposition</span>
            <span>SentinelGuard</span>
            <span>Recovery</span>
            <span>Status</span>
            <span />
          </div>

          {incidents.map((incident) => (
            <div className="incident-table-row" key={incident.id}>
              <div>
                <strong>{incident.id}</strong>
                <div className={`severity ${incident.severity.toLowerCase()}`}>
                  <AlertTriangle size={11} />
                  {incident.severity}
                </div>
              </div>

              <span>{incident.service}</span>
              <span>{incident.disposition}</span>

              <span className={incident.guard === "Approved" ? "positive" : ""}>
                {incident.guard}
              </span>

              <span
                className={
                  incident.recovery === "Verified"
                    ? "positive"
                    : ""
                }
              >
                {incident.recovery}
              </span>

              <div className="status-cell">
                {incident.status === "Resolved" ? (
                  <CheckCircle2 size={15} />
                ) : (
                  <Clock3 size={15} />
                )}
                {incident.status}
              </div>

              <button className="row-action">
                <ChevronRight size={17} />
              </button>
            </div>
          ))}
        </div>

        <div className="safety-strip">
          <ShieldCheck size={19} />
          <div>
            <strong>Incident decisions remain evidence gated</strong>
            <p>
              A supported RCA candidate is still not automatically treated as a
              confirmed root cause.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
