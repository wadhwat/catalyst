import { useState } from "react";
import { motion } from "motion/react";
import { useNavigate } from "react-router";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ChevronRight,
  Camera,
  Clock,
  Filter,
  TrendingUp,
} from "lucide-react";
import { useInspection } from "../context/InspectionContext";
import type { InspectionResult } from "../data/types";

const statusConfig = {
  passed: {
    icon: CheckCircle2,
    color: "#22C55E",
    bg: "rgba(34,197,94,0.1)",
    border: "rgba(34,197,94,0.2)",
    label: "Passed",
  },
  warning: {
    icon: AlertTriangle,
    color: "#FFCD11",
    bg: "rgba(255,205,17,0.1)",
    border: "rgba(255,205,17,0.25)",
    label: "Warning",
  },
  failed: {
    icon: XCircle,
    color: "#EF4444",
    bg: "rgba(239,68,68,0.1)",
    border: "rgba(239,68,68,0.2)",
    label: "Failed",
  },
};

function groupByDate(entries: InspectionResult[]) {
  const groups: Record<string, InspectionResult[]> = {};
  entries.forEach((entry) => {
    if (!groups[entry.date]) groups[entry.date] = [];
    groups[entry.date].push(entry);
  });
  return groups;
}

export function MaintenanceHistory() {
  const navigate = useNavigate();
  const { state } = useInspection();
  const historyData = state.history;
  const [filter, setFilter] = useState<"all" | "passed" | "warning" | "failed">("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = historyData.filter((h) => filter === "all" || h.status === filter);
  const grouped = groupByDate(filtered);

  const passRate = historyData.length > 0
    ? Math.round((historyData.filter((h) => h.status === "passed").length / historyData.length) * 100)
    : 0;
  const totalIssues = historyData.reduce((sum, h) => sum + h.issuesFound, 0);

  return (
    <div
      className="h-full overflow-y-auto"
      style={{ background: "#0D0D0D", scrollbarWidth: "none" }}
    >
      {/* Header */}
      <div className="px-5 pt-2 pb-4">
        <p style={{ color: "#FFCD11", fontSize: "11px", fontWeight: 700, letterSpacing: "0.15em" }} className="uppercase">
          Fleet Records
        </p>
        <h1 className="text-white mt-0.5" style={{ fontSize: "24px", fontWeight: 700, lineHeight: 1.2 }}>
          Maintenance History
        </h1>

        {/* Summary cards */}
        <div className="flex gap-2.5 mt-4">
          <div
            className="flex-1 rounded-2xl px-3 py-3"
            style={{ background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.2)" }}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <TrendingUp size={13} color="#22C55E" />
              <span style={{ color: "#22C55E", fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em" }}>PASS RATE</span>
            </div>
            <p style={{ color: "#22C55E", fontSize: "26px", fontWeight: 800, lineHeight: 1 }}>{passRate}%</p>
            <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px" }} className="mt-0.5">Last 30 days</p>
          </div>
          <div
            className="flex-1 rounded-2xl px-3 py-3"
            style={{ background: "rgba(255,205,17,0.08)", border: "1px solid rgba(255,205,17,0.2)" }}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <AlertTriangle size={13} color="#FFCD11" />
              <span style={{ color: "#FFCD11", fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em" }}>ISSUES</span>
            </div>
            <p style={{ color: "#FFCD11", fontSize: "26px", fontWeight: 800, lineHeight: 1 }}>{totalIssues}</p>
            <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px" }} className="mt-0.5">Parts flagged</p>
          </div>
          <div
            className="flex-1 rounded-2xl px-3 py-3"
            style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <Camera size={13} color="rgba(255,255,255,0.5)" />
              <span style={{ color: "rgba(255,255,255,0.4)", fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em" }}>SCANS</span>
            </div>
            <p style={{ color: "white", fontSize: "26px", fontWeight: 800, lineHeight: 1 }}>{historyData.length}</p>
            <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px" }} className="mt-0.5">This week</p>
          </div>
        </div>

        {/* Filter pills */}
        <div className="flex gap-2 mt-4">
          {(["all", "passed", "warning", "failed"] as const).map((f) => {
            const cfg = f !== "all" ? statusConfig[f] : null;
            return (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className="px-3 py-1.5 rounded-full text-[11px] font-semibold transition-all flex items-center gap-1"
                style={{
                  background: filter === f
                    ? (cfg?.color ?? "#FFCD11")
                    : "rgba(255,255,255,0.07)",
                  color: filter === f ? "#0D0D0D" : "rgba(255,255,255,0.45)",
                }}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            );
          })}
        </div>
      </div>

      {/* Timeline */}
      <div className="px-5 pb-6">
        {Object.entries(grouped).map(([date, entries]) => (
          <div key={date} className="mb-5">
            <div className="flex items-center gap-3 mb-3">
              <span style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em" }}>
                {date.toUpperCase()}
              </span>
              <div className="flex-1 h-px" style={{ background: "rgba(255,255,255,0.07)" }} />
              <span style={{ color: "rgba(255,255,255,0.2)", fontSize: "10px" }}>
                {entries.length} {entries.length === 1 ? "check" : "checks"}
              </span>
            </div>

            <div className="space-y-2.5">
              {entries.map((entry, i) => {
                const cfg = statusConfig[entry.status];
                const Icon = cfg.icon;
                const isExpanded = expandedId === entry.id;

                return (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                  >
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                      className="w-full text-left overflow-hidden rounded-2xl"
                      style={{
                        background: isExpanded ? cfg.bg : "rgba(255,255,255,0.04)",
                        border: `1px solid ${isExpanded ? cfg.border : "rgba(255,255,255,0.07)"}`,
                      }}
                    >
                      <div className="flex items-center gap-3 px-4 py-3.5">
                        {/* Status icon */}
                        <div
                          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                          style={{ background: cfg.bg, border: `1px solid ${cfg.border}` }}
                        >
                          <Icon size={18} color={cfg.color} />
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <p style={{ color: "white", fontSize: "14px", fontWeight: 600 }}>
                              {entry.machine}
                            </p>
                            <div
                              className="px-2 py-0.5 rounded-full"
                              style={{ background: cfg.bg }}
                            >
                              <span style={{ color: cfg.color, fontSize: "10px", fontWeight: 700 }}>
                                {cfg.label}
                              </span>
                            </div>
                          </div>
                          <p style={{ color: "rgba(255,255,255,0.4)", fontSize: "11px" }} className="mt-0.5">
                            {entry.machineType}
                          </p>
                          <div className="flex items-center gap-3 mt-1.5">
                            <div className="flex items-center gap-1">
                              <Clock size={10} color="rgba(255,255,255,0.3)" />
                              <span style={{ color: "rgba(255,255,255,0.3)", fontSize: "10px" }}>{entry.time}</span>
                            </div>
                            <span style={{ color: "rgba(255,255,255,0.2)", fontSize: "10px" }}>•</span>
                            <span style={{ color: "rgba(255,255,255,0.3)", fontSize: "10px" }}>
                              {entry.partsChecked} parts · {entry.duration}
                            </span>
                            {entry.issuesFound > 0 && (
                              <>
                                <span style={{ color: "rgba(255,255,255,0.2)", fontSize: "10px" }}>•</span>
                                <span style={{ color: cfg.color, fontSize: "10px", fontWeight: 600 }}>
                                  {entry.issuesFound} issue{entry.issuesFound > 1 ? "s" : ""}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                        <ChevronRight
                          size={16}
                          color="rgba(255,255,255,0.25)"
                          style={{ transform: isExpanded ? "rotate(90deg)" : "none", transition: "transform 0.2s" }}
                        />
                      </div>

                      {/* Expanded detail */}
                      {isExpanded && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="px-4 pb-4"
                        >
                          <div
                            className="h-px w-full mb-3"
                            style={{ background: "rgba(255,255,255,0.08)" }}
                          />
                          <div className="flex gap-4 mb-3">
                            <div>
                              <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px" }}>Operator</p>
                              <p style={{ color: "white", fontSize: "12px", fontWeight: 600 }}>{entry.operator}</p>
                            </div>
                            <div>
                              <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px" }}>Duration</p>
                              <p style={{ color: "white", fontSize: "12px", fontWeight: 600 }}>{entry.duration}</p>
                            </div>
                            <div>
                              <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px" }}>Parts</p>
                              <p style={{ color: "white", fontSize: "12px", fontWeight: 600 }}>{entry.partsChecked}/6</p>
                            </div>
                          </div>
                          {entry.notes && (
                            <div
                              className="rounded-xl px-3 py-2.5 mb-3"
                              style={{ background: "rgba(255,255,255,0.05)" }}
                            >
                              <p style={{ color: "rgba(255,255,255,0.6)", fontSize: "11px", lineHeight: 1.5 }}>
                                {entry.notes}
                              </p>
                            </div>
                          )}
                          {entry.flaggedParts && (
                            <div className="flex flex-wrap gap-1.5">
                              {entry.flaggedParts.map((part) => (
                                <span
                                  key={part}
                                  className="px-2.5 py-1 rounded-full text-[10px] font-medium"
                                  style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}` }}
                                >
                                  {part}
                                </span>
                              ))}
                            </div>
                          )}
                        </motion.div>
                      )}
                    </button>
                  </motion.div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
