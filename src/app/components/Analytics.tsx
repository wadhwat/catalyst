import { useState, useMemo } from "react";
import { motion } from "motion/react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadialBarChart,
  RadialBar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { TrendingUp, TrendingDown, Shield, Clock, Zap, AlertTriangle } from "lucide-react";
import { useInspection } from "../context/InspectionContext";

const PART_COLORS: Record<string, string> = {
  Bucket: "#FFCD11", Hydraulic: "#F97316", Track: "#EF4444",
  Engine: "#A78BFA", Bearing: "#38BDF8", Seals: "#34D399",
};

const monthlyTrend = [
  { month: "Sep", prevented: 3, downtime: 5.2 },
  { month: "Oct", prevented: 5, downtime: 3.8 },
  { month: "Nov", prevented: 4, downtime: 4.1 },
  { month: "Dec", prevented: 8, downtime: 2.3 },
  { month: "Jan", prevented: 11, downtime: 1.8 },
  { month: "Feb", prevented: 14, downtime: 1.2 },
];

function parseDuration(s: string): number {
  let secs = 0;
  const minMatch = s.match(/(\d+)\s*m/);
  const secMatch = s.match(/(\d+)\s*s/);
  if (minMatch) secs += parseInt(minMatch[1]) * 60;
  if (secMatch) secs += parseInt(secMatch[1]);
  return secs || 252; // fallback 4m12s
}

function formatDuration(secs: number): string {
  const m = Math.floor(secs / 60);
  const s = Math.round(secs % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-xl px-3 py-2.5"
      style={{
        background: "rgba(18,18,18,0.95)",
        border: "1px solid rgba(255,255,255,0.1)",
        backdropFilter: "blur(12px)",
      }}
    >
      <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "11px" }} className="mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color, fontSize: "12px", fontWeight: 600 }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
};

export function Analytics() {
  const [activeTab, setActiveTab] = useState<"overview" | "fleet" | "trends">("overview");
  const { state } = useInspection();
  const { history, machines } = state;

  const totalIssues = history.reduce((sum, h) => sum + h.issuesFound, 0);
  const avgDuration = history.length > 0
    ? history.reduce((sum, h) => sum + parseDuration(h.duration), 0) / history.length
    : 252;
  const passRate = history.length > 0
    ? ((history.filter((h) => h.status === "passed").length / history.length) * 100).toFixed(1)
    : "97.3";

  const kpis = [
    { label: "Downtime Prevented", value: "47h", trend: "+12%", up: true, color: "#22C55E", icon: Shield },
    { label: "Issues Detected", value: String(totalIssues), trend: "+8%", up: false, color: "#FFCD11", icon: AlertTriangle },
    { label: "Avg Check Time", value: formatDuration(avgDuration), trend: "-18%", up: true, color: "#38BDF8", icon: Clock },
    { label: "AI Accuracy", value: `${passRate}%`, trend: "+1.2%", up: true, color: "#A78BFA", icon: Zap },
  ];

  // Derive weekly scans from history
  const weeklyScans = useMemo(() => {
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const counts = days.map((day) => ({ day, scans: 0, issues: 0 }));
    history.forEach((h) => {
      const d = new Date(h.timestamp);
      const dayIdx = d.getDay();
      counts[dayIdx].scans++;
      counts[dayIdx].issues += h.issuesFound;
    });
    // Rotate so Mon is first
    return [...counts.slice(1), counts[0]];
  }, [history]);

  // Derive issues by part from flaggedParts
  const issuesByPart = useMemo(() => {
    const partCounts: Record<string, number> = {};
    history.forEach((h) => {
      h.flaggedParts?.forEach((part) => {
        // Normalize to short name
        const key = part.split(" ")[0];
        partCounts[key] = (partCounts[key] || 0) + 1;
      });
    });
    return Object.entries(partCounts)
      .map(([part, count]) => ({ part, count, color: PART_COLORS[part] || "#FFCD11" }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);
  }, [history]);

  // Derive uptime from machine status
  const uptimeData = useMemo(() => {
    const fills = ["#FFCD11", "#22C55E", "#EF4444", "#F97316", "#A78BFA", "#38BDF8"];
    return machines.map((m, i) => ({
      name: m.model,
      uptime: m.status === "good" ? 95 + Math.floor(Math.random() * 5) : m.status === "needs-check" ? 80 + Math.floor(Math.random() * 10) : 60 + Math.floor(Math.random() * 15),
      fill: fills[i % fills.length],
    }));
  }, [machines]);

  return (
    <div
      className="h-full overflow-y-auto"
      style={{ background: "#0D0D0D", scrollbarWidth: "none" }}
    >
      {/* Header */}
      <div className="px-5 pt-2 pb-4">
        <p style={{ color: "#FFCD11", fontSize: "11px", fontWeight: 700, letterSpacing: "0.15em" }} className="uppercase">
          Performance Intelligence
        </p>
        <h1 className="text-white mt-0.5" style={{ fontSize: "24px", fontWeight: 700, lineHeight: 1.2 }}>
          Analytics
        </h1>

        {/* Segment control */}
        <div
          className="flex gap-1 mt-4 rounded-2xl p-1"
          style={{ background: "rgba(255,255,255,0.06)" }}
        >
          {(["overview", "fleet", "trends"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className="flex-1 py-2 rounded-xl text-[12px] font-semibold transition-all"
              style={{
                background: activeTab === tab ? "#FFCD11" : "transparent",
                color: activeTab === tab ? "#0D0D0D" : "rgba(255,255,255,0.4)",
              }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="px-5 pb-6 space-y-4">
        {/* KPI Cards */}
        {activeTab === "overview" && (
          <>
            <div className="grid grid-cols-2 gap-2.5">
              {kpis.map((kpi, i) => {
                const Icon = kpi.icon;
                return (
                  <motion.div
                    key={kpi.label}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.07 }}
                    className="rounded-2xl px-4 py-4"
                    style={{
                      background: "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.08)",
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div
                        className="w-8 h-8 rounded-xl flex items-center justify-center"
                        style={{ background: `${kpi.color}18` }}
                      >
                        <Icon size={15} color={kpi.color} />
                      </div>
                      <div
                        className="flex items-center gap-0.5 px-1.5 py-0.5 rounded-full"
                        style={{
                          background: kpi.up ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
                        }}
                      >
                        {kpi.up ? (
                          <TrendingUp size={9} color="#22C55E" />
                        ) : (
                          <TrendingDown size={9} color="#EF4444" />
                        )}
                        <span style={{ color: kpi.up ? "#22C55E" : "#EF4444", fontSize: "9px", fontWeight: 700 }}>
                          {kpi.trend}
                        </span>
                      </div>
                    </div>
                    <p style={{ color: kpi.color, fontSize: "22px", fontWeight: 800, lineHeight: 1 }}>
                      {kpi.value}
                    </p>
                    <p style={{ color: "rgba(255,255,255,0.4)", fontSize: "10px" }} className="mt-1">
                      {kpi.label}
                    </p>
                  </motion.div>
                );
              })}
            </div>

            {/* Weekly scans chart */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="rounded-3xl px-4 pt-4 pb-2"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-white text-[13px] font-semibold">Weekly Scans</p>
                  <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px" }}>This week vs issues</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-[#FFCD11]" />
                    <span style={{ color: "rgba(255,255,255,0.4)", fontSize: "10px" }}>Scans</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-[#EF4444]" />
                    <span style={{ color: "rgba(255,255,255,0.4)", fontSize: "10px" }}>Issues</span>
                  </div>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={weeklyScans} barGap={4} barSize={20}>
                  <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="day" tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                  <Bar dataKey="scans" fill="#FFCD11" radius={[6, 6, 0, 0]} opacity={0.85} />
                  <Bar dataKey="issues" fill="#EF4444" radius={[6, 6, 0, 0]} opacity={0.75} />
                </BarChart>
              </ResponsiveContainer>
            </motion.div>

            {/* Issues by part */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="rounded-3xl px-4 py-4"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <p className="text-white text-[13px] font-semibold mb-3">Issues by Component</p>
              <div className="space-y-2.5">
                {issuesByPart.map((item) => (
                  <div key={item.part} className="flex items-center gap-3">
                    <span style={{ color: "rgba(255,255,255,0.5)", fontSize: "11px", width: 56, flexShrink: 0 }}>
                      {item.part}
                    </span>
                    <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.07)" }}>
                      <motion.div
                        className="h-full rounded-full"
                        style={{ background: item.color }}
                        initial={{ width: 0 }}
                        animate={{ width: `${(item.count / 8) * 100}%` }}
                        transition={{ duration: 0.8, delay: 0.5 }}
                      />
                    </div>
                    <span style={{ color: item.color, fontSize: "11px", fontWeight: 700, width: 16, textAlign: "right", flexShrink: 0 }}>
                      {item.count}
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>
          </>
        )}

        {activeTab === "fleet" && (
          <>
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-3xl px-4 pt-4 pb-3"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <p className="text-white text-[13px] font-semibold mb-1">Fleet Uptime</p>
              <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px" }} className="mb-4">
                Last 30 days availability
              </p>
              <div className="space-y-3">
                {uptimeData.map((machine, i) => (
                  <motion.div
                    key={machine.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.08 }}
                    className="flex items-center gap-3"
                  >
                    <span style={{ color: "rgba(255,255,255,0.6)", fontSize: "12px", fontWeight: 600, width: 64, flexShrink: 0 }}>
                      {machine.name}
                    </span>
                    <div className="flex-1 h-6 rounded-full overflow-hidden relative" style={{ background: "rgba(255,255,255,0.07)" }}>
                      <motion.div
                        className="h-full rounded-full flex items-center pl-3"
                        style={{ background: `${machine.fill}22`, border: `1px solid ${machine.fill}50` }}
                        initial={{ width: 0 }}
                        animate={{ width: `${machine.uptime}%` }}
                        transition={{ duration: 0.9, delay: i * 0.1 + 0.3, ease: "easeOut" }}
                      />
                    </div>
                    <span style={{ color: machine.fill, fontSize: "12px", fontWeight: 700, width: 36, textAlign: "right", flexShrink: 0 }}>
                      {machine.uptime}%
                    </span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Machine health overview */}
            <div className="space-y-2.5">
              {[
                { machine: "CAT 777", alert: "4 parts flagged — schedule immediate service", type: "critical" },
                { machine: "CAT 980", alert: "Track tension below spec — monitor closely", type: "warning" },
                { machine: "CAT D8", alert: "Swing bearing lubrication overdue", type: "warning" },
              ].map((item, i) => (
                <motion.div
                  key={item.machine}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 + 0.2 }}
                  className="rounded-2xl px-4 py-3.5 flex items-start gap-3"
                  style={{
                    background: item.type === "critical" ? "rgba(239,68,68,0.08)" : "rgba(255,205,17,0.07)",
                    border: item.type === "critical" ? "1px solid rgba(239,68,68,0.25)" : "1px solid rgba(255,205,17,0.2)",
                  }}
                >
                  <AlertTriangle
                    size={16}
                    color={item.type === "critical" ? "#EF4444" : "#FFCD11"}
                    className="mt-0.5 shrink-0"
                  />
                  <div>
                    <p style={{ color: "white", fontSize: "13px", fontWeight: 600 }}>{item.machine}</p>
                    <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "11px" }} className="mt-0.5">
                      {item.alert}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </>
        )}

        {activeTab === "trends" && (
          <>
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-3xl px-4 pt-4 pb-3"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <div className="mb-4">
                <p className="text-white text-[13px] font-semibold">Downtime Prevented</p>
                <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px" }}>6-month trend (hours saved)</p>
              </div>
              <ResponsiveContainer width="100%" height={160}>
                <AreaChart data={monthlyTrend}>
                  <defs>
                    <linearGradient id="preventedGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#FFCD11" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#FFCD11" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="month" tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="prevented"
                    name="Issues Prevented"
                    stroke="#FFCD11"
                    strokeWidth={2}
                    fill="url(#preventedGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="rounded-3xl px-4 pt-4 pb-3"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <div className="mb-4">
                <p className="text-white text-[13px] font-semibold">Avg Downtime / Check</p>
                <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "11px" }}>Hours of unplanned downtime per scan</p>
              </div>
              <ResponsiveContainer width="100%" height={140}>
                <AreaChart data={monthlyTrend}>
                  <defs>
                    <linearGradient id="downtimeGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#EF4444" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="month" tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="downtime"
                    name="Downtime (h)"
                    stroke="#EF4444"
                    strokeWidth={2}
                    fill="url(#downtimeGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </motion.div>

            {/* ROI summary */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
              className="rounded-3xl px-5 py-5"
              style={{
                background: "linear-gradient(135deg, rgba(255,205,17,0.1) 0%, rgba(255,184,0,0.06) 100%)",
                border: "1px solid rgba(255,205,17,0.25)",
              }}
            >
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp size={16} color="#FFCD11" />
                <p style={{ color: "#FFCD11", fontSize: "12px", fontWeight: 700, letterSpacing: "0.1em" }} className="uppercase">
                  ROI Summary
                </p>
              </div>
              <p style={{ color: "white", fontSize: "28px", fontWeight: 800, lineHeight: 1 }}>
                $142,500
              </p>
              <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "12px" }} className="mt-1">
                Estimated savings from prevented downtime
              </p>
              <div className="flex gap-4 mt-4">
                {[
                  { label: "Repairs Avoided", value: "12" },
                  { label: "Hours Saved", value: "47h" },
                  { label: "Fleet Health", value: "88%" },
                ].map((s) => (
                  <div key={s.label}>
                    <p style={{ color: "#FFCD11", fontSize: "16px", fontWeight: 800 }}>{s.value}</p>
                    <p style={{ color: "rgba(255,255,255,0.35)", fontSize: "9px" }}>{s.label}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </div>
    </div>
  );
}
