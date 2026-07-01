import { useState, useEffect, useRef } from 'react';
import { 
  Activity, Play, Square, Terminal, RefreshCw, 
  Zap, Cpu, BarChart2, X, Search 
} from 'lucide-react';

const API_URL = "http://127.0.0.1:8888";

interface BridgeStatus {
  name: string;
  port: number;
  online: boolean;
  pending_jobs: number;
  error?: string;
}

interface PlaybookState {
  is_running: boolean;
  name?: string;
  pid?: number;
  started_at?: number;
}

interface Candidate {
  symbol: string;
  name: string;
  score: number;
  risk: string;
  intraday_use: string;
  metrics: any;
  reasons: string[];
  warnings: string[];
  sentiment?: number;
  trend?: string;
  urgency?: string;
  narrative?: string;
}

export default function App() {
  const [bridges, setBridges] = useState<Record<string, BridgeStatus>>({});
  const [playbook, setPlaybook] = useState<PlaybookState>({ is_running: false });
  const [logs, setLogs] = useState<string[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [scalpTicker, setScalpTicker] = useState<string>("SPARC.NS");
  
  const terminalRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/api/health`);
      if (res.ok) {
        const data = await res.json();
        setBridges(data.bridges || {});
        setPlaybook(data.playbook || { is_running: false });
      }
    } catch (e) {
      console.error("Backend offline:", e);
    }
  };

  const fetchCandidates = async () => {
    try {
      const res = await fetch(`${API_URL}/api/candidates`);
      if (res.ok) {
        const data = await res.json();
        setCandidates(data.candidates || []);
      }
    } catch (e) {
      console.error("Failed to fetch candidates:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_URL}/api/playbooks/status`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
        setPlaybook({
          is_running: data.is_running,
          name: data.name,
          pid: data.pid,
          started_at: data.started_at
        });
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchHealth();
    fetchCandidates();
    fetchLogs();

    const interval = setInterval(() => {
      fetchHealth();
      fetchLogs();
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const handleStartBridge = async (key: string) => {
    try {
      await fetch(`${API_URL}/api/bridge/start/${key}`, { method: "POST" });
      setTimeout(fetchHealth, 1000);
    } catch (e) {
      alert("Failed to start bridge");
    }
  };

  const handleRunPlaybook = async (playbookName: string, ticker?: string) => {
    try {
      const res = await fetch(`${API_URL}/api/playbooks/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ playbook: playbookName, ticker })
      });
      if (res.ok) {
        fetchLogs();
      } else {
        const err = await res.json();
        alert(`Error: ${err.detail}`);
      }
    } catch (e) {
      alert("Could not connect to backend API on port 8888");
    }
  };

  const handleKillPlaybook = async () => {
    try {
      await fetch(`${API_URL}/api/playbooks/kill`, { method: "POST" });
      fetchLogs();
    } catch (e) {}
  };

  const handleResetAll = async () => {
    try {
      await fetch(`${API_URL}/api/bridge/reset_all`, { method: "POST" });
      fetchHealth();
    } catch (e) {}
  };

  const handleReloadExtension = async (key: string) => {
    try {
      await fetch(`${API_URL}/api/bridge/reload/${key}`, { method: "POST" });
      alert(`Sent reload command to ${key} extension & woke up Chrome tab!`);
    } catch (e) {}
  };

  const handleReloadAllExtensions = async () => {
    try {
      await fetch(`${API_URL}/api/bridge/reload_all`, { method: "POST" });
      alert("Sent reload command to all 4 Chrome extensions & woke up tabs!");
    } catch (e) {}
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-title">
          <Activity size={32} color="#06b6d4" />
          <div>
            <h1>ANTIGRAVITY TRADING TERMINAL</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginTop: "4px" }}>
              Manifest V3 Extension Command Center & Intraday Execution Deck
            </p>
          </div>
        </div>
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <span className="badge badge-cyan">Backend Port: 8888</span>
          <button className="btn" style={{ background: "rgba(16, 185, 129, 0.2)", color: "#34d399", border: "1px solid rgba(16, 185, 129, 0.4)" }} onClick={handleReloadAllExtensions}>
            🔄 Reload All Extensions
          </button>
          <button className="btn" style={{ background: "rgba(239, 68, 68, 0.2)", color: "#f87171", border: "1px solid rgba(239, 68, 68, 0.4)" }} onClick={handleResetAll}>
            💥 Flush All Queues
          </button>
          <button className="btn" style={{ background: "rgba(255,255,255,0.05)" }} onClick={() => { fetchHealth(); fetchCandidates(); }}>
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </header>

      {/* Extension Bridge Grid */}
      <div style={{ marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: "18px", fontWeight: 600, display: "flex", alignItems: "center", gap: "8px" }}>
          <Cpu size={20} color="#10b981" /> Live Extension Bridge Status (Sidecar Engine)
        </h2>
        <span style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          Chrome MV3 Extensions communicate with these local HTTP queues
        </span>
      </div>

      <div className="grid-bridges">
        {Object.entries(bridges).map(([key, info]) => (
          <div className="card" key={key}>
            <div className="bridge-header">
              <span className="bridge-name">
                <span className={`status-dot ${info.online ? 'dot-green' : 'dot-red'}`} />
                {info.name}
              </span>
              <span className={`badge ${info.online ? 'badge-green' : 'badge-red'}`}>
                {info.online ? 'ONLINE' : 'OFFLINE'}
              </span>
            </div>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
              Endpoint: <code>http://127.0.0.1:{info.port}</code>
            </p>
            <div className="bridge-meta" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "10px" }}>
              <span>Pending Jobs: <strong>{info.pending_jobs}</strong></span>
              <div style={{ display: "flex", gap: "6px" }}>
                <button 
                  className="btn" 
                  style={{ padding: "4px 8px", fontSize: "11px", background: "rgba(16, 185, 129, 0.15)", color: "#34d399" }}
                  onClick={() => handleReloadExtension(key)}
                  title="Reload extension code in Chrome & wake worker"
                >
                  🔄 Reload
                </button>
                {!info.online && (
                  <button 
                    className="btn" 
                    style={{ padding: "4px 8px", fontSize: "11px", background: "rgba(6,182,212,0.2)", color: "#22d3ee" }}
                    onClick={() => handleStartBridge(key)}
                  >
                    <Zap size={14} /> Auto-Start
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Playbook Command Center */}
      <div className="command-deck">
        <div className="card">
          <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
            <Zap size={20} color="#f59e0b" /> Intraday Playbook Execution Deck
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "20px" }}>
            Trigger root orchestrator routines directly from your visual command center.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <button 
              className="btn btn-primary" 
              disabled={playbook.is_running}
              onClick={() => handleRunPlaybook("pre-market")}
            >
              <Play size={16} /> Execute Pre-Market Universe Scan (Screener + Perplexity)
            </button>

            <div style={{ display: "flex", gap: "8px" }}>
              <input 
                type="text" 
                value={scalpTicker} 
                onChange={(e) => setScalpTicker(e.target.value)}
                placeholder="Ticker (e.g. SPARC.NS)"
                style={{
                  flex: 1, padding: "10px 14px", borderRadius: "10px", 
                  background: "rgba(0,0,0,0.4)", border: "1px solid var(--border-color)",
                  color: "white", fontSize: "14px"
                }}
              />
              <button 
                className="btn btn-primary" 
                style={{ background: "linear-gradient(135deg, #10b981 0%, #059669 100%)" }}
                disabled={playbook.is_running || !scalpTicker}
                onClick={() => handleRunPlaybook("scalp", scalpTicker)}
              >
                <Play size={16} /> Scalp Intraday
              </button>
            </div>

            {playbook.is_running && (
              <button className="btn btn-danger" onClick={handleKillPlaybook} style={{ marginTop: "8px" }}>
                <Square size={16} /> Stop Running Playbook ({playbook.name})
              </button>
            )}
          </div>
        </div>

        {/* Live Terminal */}
        <div className="card" style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <h3 style={{ fontSize: "16px", fontWeight: 600, display: "flex", alignItems: "center", gap: "8px" }}>
              <Terminal size={18} color="#06b6d4" /> Live Execution Console Stream
            </h3>
            {playbook.is_running ? (
              <span className="badge badge-amber">RUNNING (PID: {playbook.pid})</span>
            ) : (
              <span className="badge badge-green">IDLE</span>
            )}
          </div>
          <div className="terminal-box" ref={terminalRef}>
            {logs.length === 0 ? (
              <div style={{ color: "#64748b", fontStyle: "italic" }}>
                Ready... No active playbook logs. Click 'Execute Pre-Market Universe Scan' to start streaming.
              </div>
            ) : (
              logs.map((line, idx) => {
                let cls = "terminal-line";
                if (line.includes("ERROR") || line.includes("Failed") || line.includes("Exception")) cls += " error";
                else if (line.includes("WARNING") || line.includes("offline")) cls += " warn";
                else if (line.includes("SUCCESS") || line.includes("SAVED") || line.includes("Extracted")) cls += " success";
                return <div key={idx} className={cls}>{line}</div>;
              })
            )}
          </div>
        </div>
      </div>

      {/* Candidate Matrix */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 style={{ fontSize: "18px", fontWeight: 600, display: "flex", alignItems: "center", gap: "8px" }}>
              <BarChart2 size={20} color="#38bdf8" /> Intraday Candidate & Signal Matrix
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginTop: "4px" }}>
              Combined intelligence from SQLite Warehouses (Screener quantitative models + Perplexity AI catalysts)
            </p>
          </div>
          <span className="badge badge-cyan">{candidates.length} Tickers Loaded</span>
        </div>

        {loading ? (
          <p style={{ padding: "20px", color: "var(--text-secondary)" }}>Loading database records...</p>
        ) : candidates.length === 0 ? (
          <p style={{ padding: "20px", color: "var(--text-secondary)" }}>
            No candidates found in SQLite database yet. Run a Pre-Market scan above!
          </p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Company Name</th>
                  <th>Bot Score</th>
                  <th>Risk Bucket</th>
                  <th>Intraday Use</th>
                  <th>AI Sentiment</th>
                  <th>Trend</th>
                  <th>Catalyst Summary</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((c, i) => (
                  <tr key={i}>
                    <td><span className="ticker-link">{c.symbol}</span></td>
                    <td style={{ fontWeight: 500 }}>{c.name}</td>
                    <td>
                      <span className={`badge ${c.score >= 80 ? 'badge-green' : c.score >= 65 ? 'badge-cyan' : 'badge-amber'}`}>
                        {c.score}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${c.risk === 'LOW' ? 'badge-green' : c.risk === 'MEDIUM' ? 'badge-amber' : 'badge-red'}`}>
                        {c.risk}
                      </span>
                    </td>
                    <td>{c.intraday_use}</td>
                    <td>
                      {c.sentiment !== undefined && c.sentiment !== null ? (
                        <span className={`badge ${c.sentiment > 0 ? 'badge-green' : c.sentiment < 0 ? 'badge-red' : 'badge-amber'}`}>
                          {c.sentiment > 0 ? `+${c.sentiment} BULLISH` : c.sentiment < 0 ? `${c.sentiment} BEARISH` : '0 NEUTRAL'}
                        </span>
                      ) : (
                        <span style={{ color: "#64748b", fontSize: "12px" }}>Pending AI...</span>
                      )}
                    </td>
                    <td style={{ fontWeight: 600, color: c.trend === 'BULLISH' ? '#34d399' : c.trend === 'BEARISH' ? '#f87171' : '#94a3b8' }}>
                      {c.trend || "---"}
                    </td>
                    <td style={{ maxWidth: "260px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", color: "var(--text-secondary)", fontSize: "13px" }}>
                      {c.narrative || "No breaking narrative logged."}
                    </td>
                    <td>
                      <button 
                        className="btn" 
                        style={{ padding: "6px 12px", fontSize: "12px", background: "rgba(255,255,255,0.06)" }}
                        onClick={() => setSelectedCandidate(c)}
                      >
                        <Search size={14} /> Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedCandidate && (
        <div className="modal-overlay" onClick={() => setSelectedCandidate(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
              <div>
                <h2 style={{ fontSize: "22px", fontWeight: 700, color: "#38bdf8" }}>{selectedCandidate.symbol}</h2>
                <p style={{ fontSize: "15px", color: "var(--text-secondary)" }}>{selectedCandidate.name}</p>
              </div>
              <button className="btn" style={{ padding: "6px", background: "transparent" }} onClick={() => setSelectedCandidate(null)}>
                <X size={20} color="#94a3b8" />
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "12px" }}>
                <span style={{ fontSize: "12px", color: "var(--text-secondary)", textTransform: "uppercase" }}>Screener Quantitative Score</span>
                <div style={{ fontSize: "24px", fontWeight: 700, color: "#34d399", marginTop: "4px" }}>{selectedCandidate.score} / 100</div>
              </div>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "12px" }}>
                <span style={{ fontSize: "12px", color: "var(--text-secondary)", textTransform: "uppercase" }}>Risk Bucket & Intraday Fit</span>
                <div style={{ fontSize: "20px", fontWeight: 700, color: "#fbbf24", marginTop: "4px" }}>
                  {selectedCandidate.risk} | Intraday: {selectedCandidate.intraday_use}
                </div>
              </div>
            </div>

            {selectedCandidate.narrative && (
              <div style={{ marginBottom: "20px" }}>
                <h4 style={{ fontSize: "14px", fontWeight: 600, color: "#22d3ee", marginBottom: "8px" }}>Perplexity AI Live Catalyst Summary:</h4>
                <div style={{ background: "rgba(6,182,212,0.1)", border: "1px solid rgba(6,182,212,0.3)", padding: "14px", borderRadius: "12px", fontSize: "14px", lineHeight: 1.6 }}>
                  {selectedCandidate.narrative}
                </div>
              </div>
            )}

            {selectedCandidate.reasons && selectedCandidate.reasons.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <h4 style={{ fontSize: "14px", fontWeight: 600, color: "#34d399", marginBottom: "8px" }}>✅ Bullish Thesis Drivers:</h4>
                <ul style={{ paddingLeft: "20px", fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                  {selectedCandidate.reasons.map((r, idx) => (
                    <li key={idx} style={{ marginBottom: "4px" }}>{r}</li>
                  ))}
                </ul>
              </div>
            )}

            {selectedCandidate.warnings && selectedCandidate.warnings.length > 0 && (
              <div>
                <h4 style={{ fontSize: "14px", fontWeight: 600, color: "#f87171", marginBottom: "8px" }}>⚠️ Risk Flags & Warnings:</h4>
                <ul style={{ paddingLeft: "20px", fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                  {selectedCandidate.warnings.map((w, idx) => (
                    <li key={idx} style={{ marginBottom: "4px" }}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
