import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Network,
  Server,
} from "lucide-react";

const services = [
  {
    name: "api-gateway",
    status: "healthy",
    dependencies: ["user-service", "order-service", "auth-service"],
  },
  {
    name: "order-service",
    status: "healthy",
    dependencies: [
      "payment-service",
      "inventory-service",
      "notification-service",
    ],
  },
  {
    name: "payment-service",
    status: "degraded",
    dependencies: [],
  },
  {
    name: "inventory-service",
    status: "healthy",
    dependencies: [],
  },
  {
    name: "notification-service",
    status: "healthy",
    dependencies: [],
  },
  {
    name: "user-service",
    status: "healthy",
    dependencies: [],
  },
  {
    name: "auth-service",
    status: "healthy",
    dependencies: [],
  },
];

function ServiceNode({ name, status }) {
  return (
    <div className={`service-node ${status}`}>
      <div className="service-node-icon">
        {status === "degraded" ? (
          <AlertTriangle size={18} />
        ) : (
          <Server size={18} />
        )}
      </div>

      <div>
        <strong>{name}</strong>
        <span>{status}</span>
      </div>
    </div>
  );
}

export default function ServiceMap() {
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="eyebrow">GRAPH INTELLIGENCE</div>
          <h1>Service Dependency Map</h1>
          <p className="page-description">
            Runtime dependency graph used for blast-radius and RCA reasoning.
          </p>
        </div>
      </div>

      <div className="service-map-stats">
        <div className="small-stat">
          <span>Services</span>
          <strong>7</strong>
        </div>

        <div className="small-stat">
          <span>Dependencies</span>
          <strong>6</strong>
        </div>

        <div className="small-stat">
          <span>Degraded</span>
          <strong className="warning-text">1</strong>
        </div>

        <div className="small-stat">
          <span>Graph status</span>
          <strong className="positive">Valid</strong>
        </div>
      </div>

      <div className="panel topology-panel">
        <div className="panel-heading">
          <div>
            <div className="panel-title">
              <Network size={16} />
              Runtime Topology
            </div>
            <div className="panel-subtitle">
              Directed service dependency relationships
            </div>
          </div>

          <div className="status-badge warning">
            <Activity size={13} />
            payment-service degraded
          </div>
        </div>

        <div className="topology">
          <div className="topology-level">
            <ServiceNode name="api-gateway" status="healthy" />
          </div>

          <div className="topology-arrow">?</div>

          <div className="topology-level multi">
            <ServiceNode name="user-service" status="healthy" />
            <ServiceNode name="order-service" status="healthy" />
            <ServiceNode name="auth-service" status="healthy" />
          </div>

          <div className="topology-arrow">
            <span>order-service dependencies ?</span>
          </div>

          <div className="topology-level multi">
            <ServiceNode name="payment-service" status="degraded" />
            <ServiceNode name="inventory-service" status="healthy" />
            <ServiceNode name="notification-service" status="healthy" />
          </div>
        </div>
      </div>

      <div className="panel dependency-panel">
        <div className="panel-title">Dependency Edges</div>

        <div className="dependency-grid">
          {services
            .flatMap((service) =>
              service.dependencies.map((dependency) => [
                service.name,
                dependency,
              ])
            )
            .map(([source, target]) => (
              <div className="dependency-edge" key={`${source}-${target}`}>
                <span>{source}</span>
                <ArrowRight size={14} />
                <strong>{target}</strong>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
