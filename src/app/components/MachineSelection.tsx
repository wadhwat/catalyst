import { useState } from "react";
import { useNavigate } from "react-router";
import { motion } from "motion/react";
import { Search, Bell, ChevronRight, Clock, AlertTriangle, CheckCircle2, Filter } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

const machines = [
  {
    id: "cat-320",
    model: "CAT 320",
    type: "Hydraulic Excavator",
    image: "https://images.unsplash.com/photo-1759950345011-ee5a96640e00?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxleGNhdmF0b3IlMjBjb25zdHJ1Y3Rpb24lMjBzaXRlJTIwaGVhdnklMjBlcXVpcG1lbnR8ZW58MXx8fHwxNzcyMjU5MTUzfDA&ixlib=rb-4.1.0&q=80&w=400",
    status: "needs-check",
    lastCheck: "3 days ago",
    hoursUntilService: 47,
    alerts: 2,
  },
  {
    id: "cat-d6",
    model: "CAT D6",
    type: "Track-Type Tractor",
    image: "https://images.unsplash.com/photo-1690915788747-a772131e0fac?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjcmF3bGVyJTIwZG96ZXIlMjB0cmFjayUyMG1hY2hpbmUlMjBpbmR1c3RyaWFsfGVufDF8fHx8MTc3MjI1OTE2MHww&ixlib=rb-4.1.0&q=80&w=400",
    status: "good",
    lastCheck: "Today",
    hoursUntilService: 312,
    alerts: 0,
  },
  {
    id: "cat-777",
    model: "CAT 777",
    type: "Mining Truck",
    image: "https://images.unsplash.com/photo-1582280871722-424e91cbee8b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxkdW1wJTIwdHJ1Y2slMjBtaW5pbmclMjB5ZWxsb3clMjBoZWF2eXxlbnwxfHx8fDE3NzIyNTkxNTd8MA&ixlib=rb-4.1.0&q=80&w=400",
    status: "critical",
    lastCheck: "8 days ago",
    hoursUntilService: 2,
    alerts: 5,
  },
  {
    id: "cat-980",
    model: "CAT 980",
    type: "Wheel Loader",
    image: "https://images.unsplash.com/photo-1759850425285-46f70357253d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx3aGVlbCUyMGxvYWRlciUyMGNvbnN0cnVjdGlvbiUyMGVxdWlwbWVudHxlbnwxfHx8fDE3NzIxOTU5NTV8MA&ixlib=rb-4.1.0&q=80&w=400",
    status: "good",
    lastCheck: "Yesterday",
    hoursUntilService: 189,
    alerts: 0,
  },
  {
    id: "cat-d8",
    model: "CAT D8",
    type: "Large Dozer",
    image: "https://images.unsplash.com/photo-1621922688758-359fc864071e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxidWxsZG96ZXIlMjB5ZWxsb3clMjBDQVQlMjBoZWF2eSUyMG1hY2hpbmVyeXxlbnwxfHx8fDE3NzIyNTkxNTZ8MA&ixlib=rb-4.1.0&q=80&w=400",
    status: "needs-check",
    lastCheck: "5 days ago",
    hoursUntilService: 98,
    alerts: 1,
  },
  {
    id: "cat-140",
    model: "CAT 140",
    type: "Motor Grader",
    image: "https://images.unsplash.com/photo-1693064203616-2e78760f5df7?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtb3RvciUyMGdyYWRlciUyMHJvYWQlMjBjb25zdHJ1Y3Rpb24lMjBtYWNoaW5lfGVufDF8fHx8MTc3MjI1OTE1OHww&ixlib=rb-4.1.0&q=80&w=400",
    status: "good",
    lastCheck: "2 days ago",
    hoursUntilService: 234,
    alerts: 0,
  },
];

const statusConfig = {
  good: { label: "Good", color: "#22C55E", bg: "rgba(34,197,94,0.12)" },
  "needs-check": { label: "Check Due", color: "#FFCD11", bg: "rgba(255,205,17,0.12)" },
  critical: { label: "Critical", color: "#EF4444", bg: "rgba(239,68,68,0.12)" },
};

export function MachineSelection() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<"all" | "critical" | "needs-check" | "good">("all");

  const filtered = machines.filter((m) => {
    const matchSearch =
      m.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchFilter = activeFilter === "all" || m.status === activeFilter;
    return matchSearch && matchFilter;
  });

  return (
    <div
      className="h-full overflow-y-auto"
      style={{ background: "#0D0D0D", scrollbarWidth: "none" }}
    >
      {/* Header */}
      <div className="px-5 pt-2 pb-4">
        <div className="flex items-center justify-between mb-1">
          <div>
            <p className="text-[#FFCD11] text-[11px] tracking-[0.15em] uppercase font-semibold">
              CAT Fleet Vision
            </p>
            <h1
              className="text-white mt-0.5"
              style={{ fontSize: "24px", fontWeight: 700, lineHeight: 1.2 }}
            >
              My Equipment
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button className="w-9 h-9 rounded-full flex items-center justify-center relative"
              style={{ background: "rgba(255,255,255,0.08)" }}>
              <Bell size={18} color="white" />
              <div className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#EF4444] rounded-full border border-[#0D0D0D]" />
            </button>
            <button className="w-9 h-9 rounded-full overflow-hidden"
              style={{ background: "rgba(255,205,17,0.2)", border: "2px solid #FFCD11" }}>
              <span className="text-[#FFCD11] text-[13px] font-bold flex items-center justify-center h-full">JD</span>
            </button>
          </div>
        </div>

        {/* Stats row */}
        <div className="flex gap-2.5 mt-4">
          {[
            { label: "Active Units", value: "6", color: "#FFCD11" },
            { label: "Alerts", value: "8", color: "#EF4444" },
            { label: "Due Today", value: "2", color: "#F97316" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="flex-1 rounded-2xl px-3 py-2.5"
              style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}
            >
              <p style={{ color: stat.color, fontSize: "20px", fontWeight: 700, lineHeight: 1 }}>
                {stat.value}
              </p>
              <p className="text-[10px] mt-0.5" style={{ color: "rgba(255,255,255,0.5)" }}>
                {stat.label}
              </p>
            </div>
          ))}
        </div>

        {/* Search */}
        <div
          className="mt-4 flex items-center gap-2.5 rounded-2xl px-4 py-3"
          style={{ background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.1)" }}
        >
          <Search size={16} color="rgba(255,255,255,0.4)" />
          <input
            type="text"
            placeholder="Search equipment..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent flex-1 text-white text-[14px] outline-none placeholder:text-white/30"
          />
          <Filter size={16} color="rgba(255,255,255,0.4)" />
        </div>

        {/* Filter pills */}
        <div className="flex gap-2 mt-3">
          {(["all", "critical", "needs-check", "good"] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setActiveFilter(filter)}
              className="px-3 py-1.5 rounded-full text-[11px] font-medium tracking-wide transition-all"
              style={{
                background: activeFilter === filter ? "#FFCD11" : "rgba(255,255,255,0.08)",
                color: activeFilter === filter ? "#0D0D0D" : "rgba(255,255,255,0.5)",
              }}
            >
              {filter === "all" ? "All" : filter === "needs-check" ? "Due" : filter.charAt(0).toUpperCase() + filter.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Machine Cards Grid */}
      <div className="px-5 pb-4 grid grid-cols-2 gap-3">
        {filtered.map((machine, i) => {
          const status = statusConfig[machine.status as keyof typeof statusConfig];
          return (
            <motion.button
              key={machine.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06, duration: 0.3 }}
              onClick={() => navigate(`/camera/${machine.id}`)}
              className="text-left overflow-hidden rounded-3xl relative"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
              whileTap={{ scale: 0.97 }}
            >
              {/* Machine image */}
              <div className="relative h-[110px] overflow-hidden">
                <ImageWithFallback
                  src={machine.image}
                  alt={machine.model}
                  className="w-full h-full object-cover"
                />
                <div
                  className="absolute inset-0"
                  style={{ background: "linear-gradient(to bottom, transparent 30%, rgba(13,13,13,0.95) 100%)" }}
                />
                {/* Status badge */}
                <div
                  className="absolute top-2 right-2 px-2 py-0.5 rounded-full flex items-center gap-1"
                  style={{ background: status.bg, border: `1px solid ${status.color}30` }}
                >
                  <div
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ background: status.color }}
                  />
                  <span className="text-[9px] font-semibold" style={{ color: status.color }}>
                    {status.label}
                  </span>
                </div>
                {/* Alert badge */}
                {machine.alerts > 0 && (
                  <div
                    className="absolute top-2 left-2 w-5 h-5 rounded-full flex items-center justify-center"
                    style={{ background: "#EF4444" }}
                  >
                    <span className="text-white text-[9px] font-bold">{machine.alerts}</span>
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="px-3 py-3">
                <p className="text-white text-[15px]" style={{ fontWeight: 700, lineHeight: 1.2 }}>
                  {machine.model}
                </p>
                <p className="text-[11px] mt-0.5" style={{ color: "rgba(255,255,255,0.45)" }}>
                  {machine.type}
                </p>
                <div className="flex items-center justify-between mt-2.5">
                  <div className="flex items-center gap-1">
                    <Clock size={10} color="rgba(255,255,255,0.35)" />
                    <span className="text-[10px]" style={{ color: "rgba(255,255,255,0.35)" }}>
                      {machine.lastCheck}
                    </span>
                  </div>
                  <ChevronRight size={13} color="#FFCD11" />
                </div>
                {/* Service hours bar */}
                <div className="mt-2">
                  <div
                    className="h-1 rounded-full overflow-hidden"
                    style={{ background: "rgba(255,255,255,0.1)" }}
                  >
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min(100, (machine.hoursUntilService / 500) * 100)}%`,
                        background: machine.hoursUntilService < 50 ? "#EF4444" : machine.hoursUntilService < 150 ? "#FFCD11" : "#22C55E",
                      }}
                    />
                  </div>
                  <p className="text-[9px] mt-1" style={{ color: "rgba(255,255,255,0.3)" }}>
                    {machine.hoursUntilService}h until service
                  </p>
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Quick scan CTA */}
      <div className="px-5 pb-6">
        <motion.button
          whileTap={{ scale: 0.98 }}
          onClick={() => navigate("/camera/cat-320")}
          className="w-full py-4 rounded-3xl flex items-center justify-center gap-2.5"
          style={{
            background: "linear-gradient(135deg, #FFCD11 0%, #FFB800 100%)",
            boxShadow: "0 8px 32px rgba(255,205,17,0.25)",
          }}
        >
          <div className="w-5 h-5 rounded-full border-2 border-[#0D0D0D] flex items-center justify-center">
            <div className="w-2 h-2 bg-[#0D0D0D] rounded-full" />
          </div>
          <span style={{ color: "#0D0D0D", fontWeight: 700, fontSize: "15px" }}>
            Quick Scan — CAT 320
          </span>
        </motion.button>
      </div>
    </div>
  );
}
