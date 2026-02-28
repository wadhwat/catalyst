import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate, useParams } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import {
  ChevronLeft,
  Settings2,
  ZoomIn,
  ChevronDown,
  ChevronUp,
  Droplets,
  Wrench,
  Zap,
  Shield,
  CheckCircle2,
  Cpu,
  Cog,
  X,
  RotateCcw,
  ScanLine,
} from "lucide-react";

const machineNames: Record<string, string> = {
  "cat-320": "CAT 320 Excavator",
  "cat-d6": "CAT D6 Dozer",
  "cat-777": "CAT 777 Mining Truck",
  "cat-980": "CAT 980 Wheel Loader",
  "cat-d8": "CAT D8 Large Dozer",
  "cat-140": "CAT 140 Motor Grader",
};

interface ChecklistStep {
  id: number;
  icon: React.ElementType;
  title: string;
  description: string;
  part: string;
  status: "pending" | "in-progress" | "verified";
  position: { x: number; y: number; w: number; h: number };
  tooltip: { x: number; y: number };
}

const buildChecklist = (): ChecklistStep[] => [
  {
    id: 1,
    icon: Droplets,
    title: "Hydraulic Fluid Level",
    description: "Check reservoir sight glass — green zone required",
    part: "Hydraulic Reservoir",
    status: "pending",
    position: { x: 52, y: 42, w: 24, h: 18 },
    tooltip: { x: 54, y: 34 },
  },
  {
    id: 2,
    icon: Zap,
    title: "Bucket Teeth",
    description: "Inspect wear caps for cracks or missing material",
    part: "Bucket Assembly",
    status: "pending",
    position: { x: 12, y: 62, w: 36, h: 20 },
    tooltip: { x: 14, y: 55 },
  },
  {
    id: 3,
    icon: Wrench,
    title: "Track Tension",
    description: "Measure sag — target 25–32mm deflection",
    part: "Track Assembly",
    status: "pending",
    position: { x: 8, y: 78, w: 82, h: 12 },
    tooltip: { x: 10, y: 72 },
  },
  {
    id: 4,
    icon: Shield,
    title: "Boom Cylinder Seals",
    description: "Check for oil weeping or visible seal damage",
    part: "Boom Cylinder",
    status: "pending",
    position: { x: 36, y: 26, w: 22, h: 32 },
    tooltip: { x: 60, y: 20 },
  },
  {
    id: 5,
    icon: Cpu,
    title: "Engine Compartment",
    description: "Verify coolant level and belt condition",
    part: "Engine Bay",
    status: "pending",
    position: { x: 61, y: 50, w: 26, h: 22 },
    tooltip: { x: 63, y: 43 },
  },
  {
    id: 6,
    icon: Cog,
    title: "Swing Bearing Grease",
    description: "Apply grease if fitting dry — 3–5 pumps",
    part: "Swing Bearing",
    status: "pending",
    position: { x: 38, y: 57, w: 22, h: 16 },
    tooltip: { x: 40, y: 51 },
  },
];

export function CameraScreen() {
  const navigate = useNavigate();
  const { machineId } = useParams();
  const machineName = machineNames[machineId ?? "cat-320"] ?? "CAT 320 Excavator";

  const [steps, setSteps] = useState<ChecklistStep[]>(buildChecklist());
  const [sheetExpanded, setSheetExpanded] = useState(false);
  const [currentDetection, setCurrentDetection] = useState<ChecklistStep | null>(null);
  const [scanning, setScanning] = useState(false);
  const [scanStarted, setScanStarted] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [detectedIds, setDetectedIds] = useState<Set<number>>(new Set());
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const scanTimerRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const completedCount = steps.filter((s) => s.status === "verified").length;
  const progress = (completedCount / steps.length) * 100;

  const clearTimers = () => {
    scanTimerRef.current.forEach(clearTimeout);
    scanTimerRef.current = [];
  };

  const startScan = useCallback(() => {
    clearTimers();
    setScanning(true);
    setScanStarted(true);
    setSteps(buildChecklist());
    setDetectedIds(new Set());
    setCurrentDetection(null);

    const pending = buildChecklist();
    pending.forEach((step, i) => {
      const delay = 2200 + i * 3000;
      const t1 = setTimeout(() => {
        setSteps((prev) => prev.map((s) => (s.id === step.id ? { ...s, status: "in-progress" } : s)));
        setCurrentDetection(step);
        setDetectedIds((prev) => new Set([...prev, step.id]));
      }, delay);
      const t2 = setTimeout(() => {
        setSteps((prev) => prev.map((s) => (s.id === step.id ? { ...s, status: "verified" } : s)));
        setCurrentDetection(null);
      }, delay + 2000);
      scanTimerRef.current.push(t1, t2);
    });

    const totalTime = 2200 + pending.length * 3000 + 2200;
    const t = setTimeout(() => {
      setScanning(false);
      setShowSuccess(true);
    }, totalTime);
    scanTimerRef.current.push(t);
  }, []);

  useEffect(() => () => clearTimers(), []);

  const resetScan = () => {
    clearTimers();
    setShowSuccess(false);
    setScanStarted(false);
    setScanning(false);
    setSteps(buildChecklist());
    setDetectedIds(new Set());
    setCurrentDetection(null);
  };

  return (
    <div
      className="w-full flex items-center justify-center"
      style={{ height: "100dvh", background: "#050505" }}
    >
      {/* Phone frame container */}
      <div
        className="relative w-full md:max-w-[390px] overflow-hidden bg-black"
        style={{ height: "100dvh", maxHeight: "844px" }}
      >
        {/* ── Camera Background ── */}
        <div
          className="absolute inset-0 transition-transform duration-700"
          style={{ transform: `scale(${zoomLevel})` }}
        >
          <img
            src="https://images.unsplash.com/photo-1614303936041-0ad85737faef?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxleGNhdmF0b3IlMjBidWNrZXQlMjBhcm0lMjBjbG9zZSUyMHVwJTIwbWFjaGluZXJ5fGVufDF8fHx8MTc3MjI1OTE2MXww&ixlib=rb-4.1.0&q=80&w=800"
            alt="Camera feed"
            className="w-full h-full object-cover"
          />
          <div
            className="absolute inset-0"
            style={{ background: "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.5) 100%)" }}
          />
          <div
            className="absolute inset-x-0 top-0 h-40"
            style={{ background: "linear-gradient(to bottom, rgba(0,0,0,0.8), transparent)" }}
          />
          <div
            className="absolute inset-x-0 bottom-0 h-72"
            style={{ background: "linear-gradient(to top, rgba(0,0,0,0.9), transparent)" }}
          />
        </div>

        {/* ── AR SVG Overlay ── */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          viewBox="0 0 390 844"
          preserveAspectRatio="xMidYMid slice"
        >
          {/* Scanning line */}
          {scanning && (
            <motion.line
              x1={0} x2={390}
              stroke="rgba(255,205,17,0.35)"
              strokeWidth={1.5}
              initial={{ y1: 60, y2: 60 }}
              animate={{ y1: [60, 780], y2: [60, 780] }}
              transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            />
          )}

          {steps.map((step) => {
            if (!detectedIds.has(step.id)) return null;
            const { x, y, w, h } = step.position;
            const px = (x / 100) * 390;
            const py = (y / 100) * 844;
            const pw = (w / 100) * 390;
            const ph = (h / 100) * 844;
            const isActive = currentDetection?.id === step.id;
            const isVerified = step.status === "verified";
            const strokeColor = isVerified ? "#22C55E" : "#FFCD11";

            return (
              <g key={step.id}>
                {/* Fill */}
                <rect x={px} y={py} width={pw} height={ph} rx={8}
                  fill={isVerified ? "rgba(34,197,94,0.05)" : "rgba(255,205,17,0.06)"}
                />
                {/* Border */}
                <motion.rect
                  x={px} y={py} width={pw} height={ph} rx={8}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={isActive ? 2 : 1.5}
                  strokeDasharray="10 4"
                  initial={{ opacity: 0 }}
                  animate={{
                    opacity: 1,
                    strokeDashoffset: isActive ? [0, -28] : 0,
                  }}
                  transition={{
                    opacity: { duration: 0.4 },
                    strokeDashoffset: { duration: 1, repeat: Infinity, ease: "linear" },
                  }}
                />
                {/* Corners */}
                {([[px, py], [px + pw, py], [px, py + ph], [px + pw, py + ph]] as [number, number][]).map(([cx, cy], ci) => (
                  <g key={ci}>
                    <circle cx={cx} cy={cy} r={3.5} fill={strokeColor} />
                    {isActive && (
                      <motion.circle cx={cx} cy={cy} r={3.5}
                        fill="none" stroke={strokeColor} strokeWidth={1}
                        initial={{ r: 3.5, opacity: 0.7 }}
                        animate={{ r: 11, opacity: 0 }}
                        transition={{ duration: 1.2, repeat: Infinity, delay: ci * 0.15 }}
                      />
                    )}
                  </g>
                ))}
                {/* Verified check badge */}
                {isVerified && (
                  <motion.g
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: "spring", stiffness: 350, damping: 20 }}
                  >
                    <circle cx={px + pw / 2} cy={py + ph / 2} r={14} fill="rgba(34,197,94,0.88)" />
                    <path
                      d={`M ${px + pw / 2 - 6} ${py + ph / 2} l 4 5 l 9 -9`}
                      stroke="white" strokeWidth={2.5} strokeLinecap="round"
                      strokeLinejoin="round" fill="none"
                    />
                  </motion.g>
                )}
              </g>
            );
          })}

          {/* Floating part labels */}
          {steps.map((step) => {
            if (step.status !== "in-progress") return null;
            const px = (step.tooltip.x / 100) * 390;
            const py = (step.tooltip.y / 100) * 844;
            return (
              <motion.g key={`lbl-${step.id}`}
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <rect x={px} y={py - 13} width={118} height={22} rx={11} fill="rgba(255,205,17,0.92)" />
                <text x={px + 59} y={py + 3.5}
                  textAnchor="middle" fill="#0D0D0D"
                  fontSize={10} fontWeight="700"
                  fontFamily="-apple-system, BlinkMacSystemFont, 'Inter', sans-serif"
                >
                  {step.part}
                </text>
              </motion.g>
            );
          })}
        </svg>

        {/* ── Top Bar ── */}
        <div className="absolute top-0 inset-x-0 flex items-center justify-between px-5 pt-4 pb-2 z-40">
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate(-1)}
              className="w-9 h-9 rounded-full flex items-center justify-center"
              style={{ background: "rgba(0,0,0,0.55)", backdropFilter: "blur(16px)", border: "1px solid rgba(255,255,255,0.1)" }}
            >
              <ChevronLeft size={20} color="white" />
            </button>
            <div
              className="px-3 py-1.5 rounded-full flex items-center gap-2"
              style={{ background: "rgba(0,0,0,0.55)", backdropFilter: "blur(16px)", border: "1px solid rgba(255,255,255,0.12)" }}
            >
              <motion.div
                className="w-1.5 h-1.5 rounded-full bg-[#FFCD11]"
                animate={{ opacity: scanning ? [1, 0.2, 1] : 1 }}
                transition={{ duration: 0.8, repeat: scanning ? Infinity : 0 }}
              />
              <span className="text-white text-[12px] font-semibold">{machineName}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setZoomLevel((z) => (z === 1.0 ? 1.35 : 1.0))}
              className="w-9 h-9 rounded-full flex items-center justify-center"
              style={{ background: "rgba(0,0,0,0.55)", backdropFilter: "blur(16px)", border: "1px solid rgba(255,255,255,0.1)" }}
            >
              <ZoomIn size={16} color={zoomLevel > 1 ? "#FFCD11" : "white"} />
            </button>
            <button
              className="w-9 h-9 rounded-full flex items-center justify-center"
              style={{ background: "rgba(0,0,0,0.55)", backdropFilter: "blur(16px)", border: "1px solid rgba(255,255,255,0.1)" }}
            >
              <Settings2 size={16} color="white" />
            </button>
          </div>
        </div>

        {/* ── Progress Bar ── */}
        <AnimatePresence>
          {scanStarted && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="absolute top-[68px] inset-x-5 z-40"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span style={{ color: "rgba(255,255,255,0.6)", fontSize: "10px", letterSpacing: "0.12em" }} className="uppercase">
                  Inspection Progress
                </span>
                <span style={{ color: "#FFCD11", fontWeight: 700, fontSize: "11px" }}>
                  {completedCount}/{steps.length} Steps
                </span>
              </div>
              <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.1)" }}>
                <motion.div
                  className="h-full rounded-full"
                  style={{ background: "linear-gradient(90deg, #FFCD11 0%, #FFB800 100%)" }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Detection Popup Card ── */}
        <AnimatePresence mode="wait">
          {currentDetection && (
            <motion.div
              key={currentDetection.id}
              initial={{ opacity: 0, y: -16, scale: 0.92 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.96 }}
              transition={{ type: "spring", stiffness: 400, damping: 26 }}
              className="absolute z-50 top-[118px] left-5 right-5"
            >
              <div
                className="rounded-2xl overflow-hidden"
                style={{
                  background: "rgba(10,10,10,0.88)",
                  backdropFilter: "blur(28px)",
                  border: "1px solid rgba(255,205,17,0.28)",
                  boxShadow: "0 12px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,205,17,0.08)",
                }}
              >
                <div
                  className="h-px w-full"
                  style={{ background: "linear-gradient(90deg, transparent 0%, #FFCD11 50%, transparent 100%)" }}
                />
                <div className="px-4 py-3.5 flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                    style={{ background: "rgba(255,205,17,0.12)", border: "1px solid rgba(255,205,17,0.25)" }}
                  >
                    <motion.div
                      animate={{ scale: [1, 1.18, 1] }}
                      transition={{ duration: 1.4, repeat: Infinity }}
                    >
                      <ScanLine size={18} color="#FFCD11" />
                    </motion.div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-1">
                      <motion.div
                        className="w-1.5 h-1.5 rounded-full bg-[#FFCD11]"
                        animate={{ opacity: [1, 0.2, 1] }}
                        transition={{ duration: 0.9, repeat: Infinity }}
                      />
                      <span style={{ color: "#FFCD11", fontSize: "10px", fontWeight: 700, letterSpacing: "0.14em" }}>
                        DETECTED
                      </span>
                    </div>
                    <p className="text-white text-[14px] font-semibold leading-tight">
                      {currentDetection.part} Identified
                    </p>
                    <p style={{ color: "rgba(255,255,255,0.45)", fontSize: "11px" }} className="mt-0.5">
                      Tap to inspect
                    </p>
                  </div>
                  <button
                    onClick={() => setCurrentDetection(null)}
                    className="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
                    style={{ background: "rgba(255,255,255,0.07)" }}
                  >
                    <X size={13} color="rgba(255,255,255,0.55)" />
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Start Scan CTA ── */}
        <AnimatePresence>
          {!scanStarted && !showSuccess && (
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 24 }}
              transition={{ delay: 0.3 }}
              className="absolute z-40 inset-x-7"
              style={{ bottom: 140 }}
            >
              <motion.button
                onClick={startScan}
                whileTap={{ scale: 0.97 }}
                className="w-full py-5 rounded-3xl flex flex-col items-center gap-2"
                style={{
                  background: "linear-gradient(135deg, rgba(255,205,17,0.96) 0%, rgba(255,180,0,0.96) 100%)",
                  boxShadow: "0 0 48px rgba(255,205,17,0.28), 0 8px 32px rgba(0,0,0,0.45)",
                }}
              >
                <ScanLine size={26} color="#0D0D0D" strokeWidth={2.5} />
                <span style={{ color: "#0D0D0D", fontWeight: 800, fontSize: "17px" }}>
                  Start AI Inspection
                </span>
                <span style={{ color: "rgba(13,13,13,0.55)", fontSize: "11px" }}>
                  Computer Vision ready · 6 checks
                </span>
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Bottom Checklist Sheet ── */}
        <AnimatePresence>
          {scanStarted && !showSuccess && (
            <motion.div
              initial={{ y: 320 }}
              animate={{ y: 0 }}
              exit={{ y: 400 }}
              transition={{ type: "spring", stiffness: 280, damping: 30 }}
              className="absolute bottom-0 inset-x-0 z-40"
              style={{
                background: "rgba(10,10,10,0.93)",
                backdropFilter: "blur(36px)",
                borderTop: "1px solid rgba(255,255,255,0.09)",
                borderRadius: "24px 24px 0 0",
              }}
            >
              {/* Sheet handle */}
              <button
                onClick={() => setSheetExpanded((v) => !v)}
                className="w-full flex flex-col items-center pt-3 pb-2"
              >
                <div className="w-10 h-1 rounded-full mb-3" style={{ background: "rgba(255,255,255,0.18)" }} />
                <div className="flex items-center justify-between w-full px-5">
                  <div>
                    <div className="flex items-center gap-2">
                      <span style={{ color: "white", fontSize: "15px", fontWeight: 700 }}>
                        Maintenance Checklist
                      </span>
                      {scanning && (
                        <motion.span
                          animate={{ opacity: [1, 0.3, 1] }}
                          transition={{ duration: 1.1, repeat: Infinity }}
                          className="px-2 py-0.5 rounded-full flex items-center gap-1"
                          style={{ background: "rgba(255,205,17,0.14)" }}
                        >
                          <span style={{ color: "#FFCD11", fontSize: "9px", fontWeight: 800 }}>● LIVE</span>
                        </motion.span>
                      )}
                    </div>
                    <p style={{ color: "rgba(255,255,255,0.4)", fontSize: "11px" }} className="mt-0.5">
                      {completedCount} of {steps.length} verified
                    </p>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <svg width="34" height="34" viewBox="0 0 34 34">
                      <circle cx="17" cy="17" r="13" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="3" />
                      <motion.circle
                        cx="17" cy="17" r="13"
                        fill="none" stroke="#FFCD11" strokeWidth="3"
                        strokeLinecap="round"
                        transform="rotate(-90 17 17)"
                        animate={{ strokeDasharray: `${(81.7 * progress) / 100} 81.7` }}
                        transition={{ duration: 0.5 }}
                      />
                      <text x="17" y="21" textAnchor="middle" fill="#FFCD11" fontSize="8" fontWeight="800">
                        {completedCount}/{steps.length}
                      </text>
                    </svg>
                    {sheetExpanded ? (
                      <ChevronDown size={17} color="rgba(255,255,255,0.4)" />
                    ) : (
                      <ChevronUp size={17} color="rgba(255,255,255,0.4)" />
                    )}
                  </div>
                </div>
              </button>

              {/* Expanded list */}
              <motion.div
                animate={{ height: sheetExpanded ? "auto" : 0 }}
                style={{ overflow: "hidden" }}
                transition={{ duration: 0.26, ease: "easeInOut" }}
              >
                <div
                  className="px-4 pt-1.5 pb-6 space-y-2"
                  style={{ maxHeight: 300, overflowY: "auto", scrollbarWidth: "none" }}
                >
                  {steps.map((step, i) => {
                    const Icon = step.icon;
                    const isActive = step.status === "in-progress";
                    const isDone = step.status === "verified";
                    return (
                      <motion.div
                        key={step.id}
                        layout
                        initial={{ opacity: 0, x: -16 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.04 }}
                        className="flex items-center gap-3 px-3.5 py-3 rounded-2xl relative overflow-hidden"
                        style={{
                          background: isActive
                            ? "rgba(255,205,17,0.07)"
                            : isDone
                            ? "rgba(34,197,94,0.06)"
                            : "rgba(255,255,255,0.04)",
                          border: isActive
                            ? "1px solid rgba(255,205,17,0.28)"
                            : isDone
                            ? "1px solid rgba(34,197,94,0.18)"
                            : "1px solid rgba(255,255,255,0.06)",
                        }}
                      >
                        {isActive && (
                          <motion.div
                            className="absolute inset-0 rounded-2xl"
                            animate={{ opacity: [0.35, 0, 0.35] }}
                            transition={{ duration: 1.6, repeat: Infinity }}
                            style={{ background: "rgba(255,205,17,0.08)" }}
                          />
                        )}
                        <div
                          className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                          style={{
                            background: isDone
                              ? "rgba(34,197,94,0.14)"
                              : isActive
                              ? "rgba(255,205,17,0.14)"
                              : "rgba(255,255,255,0.07)",
                          }}
                        >
                          {isDone ? (
                            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 420 }}>
                              <CheckCircle2 size={17} color="#22C55E" />
                            </motion.div>
                          ) : (
                            <Icon size={15} color={isActive ? "#FFCD11" : "rgba(255,255,255,0.4)"} />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p
                            style={{
                              color: isDone ? "rgba(255,255,255,0.45)" : "white",
                              fontSize: "13px",
                              fontWeight: isDone ? 400 : 600,
                              textDecoration: isDone ? "line-through" : "none",
                              lineHeight: 1.3,
                            }}
                          >
                            {step.title}
                          </p>
                          {!isDone && (
                            <p style={{ color: "rgba(255,255,255,0.3)", fontSize: "10px" }} className="mt-0.5 leading-tight">
                              {step.description}
                            </p>
                          )}
                        </div>
                        <div
                          className="px-2 py-0.5 rounded-full"
                          style={{
                            background: isDone
                              ? "rgba(34,197,94,0.14)"
                              : isActive
                              ? "rgba(255,205,17,0.14)"
                              : "rgba(255,255,255,0.05)",
                          }}
                        >
                          <span
                            style={{
                              color: isDone ? "#22C55E" : isActive ? "#FFCD11" : "rgba(255,255,255,0.2)",
                              fontSize: "9px",
                              fontWeight: 700,
                              letterSpacing: "0.08em",
                            }}
                          >
                            {isDone ? "✓ Done" : isActive ? "Scanning" : "Pending"}
                          </span>
                        </div>
                      </motion.div>
                    );
                  })}
                  <button
                    onClick={resetScan}
                    className="w-full py-3 rounded-2xl flex items-center justify-center gap-2"
                    style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <RotateCcw size={13} color="rgba(255,255,255,0.35)" />
                    <span style={{ color: "rgba(255,255,255,0.35)", fontSize: "12px" }}>Reset Scan</span>
                  </button>
                </div>
              </motion.div>

              {/* Collapsed peek */}
              {!sheetExpanded && (
                <div className="px-5 pb-5">
                  {(() => {
                    const active = steps.find((s) => s.status === "in-progress");
                    const next = steps.find((s) => s.status === "pending");
                    if (active)
                      return (
                        <div className="flex items-center gap-2.5">
                          <motion.div
                            className="w-2 h-2 rounded-full bg-[#FFCD11] shrink-0"
                            animate={{ scale: [1, 1.5, 1] }}
                            transition={{ duration: 1, repeat: Infinity }}
                          />
                          <span style={{ color: "white", fontSize: "13px", fontWeight: 600 }}>
                            Scanning: {active.title}
                          </span>
                        </div>
                      );
                    if (next)
                      return (
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full shrink-0" style={{ background: "rgba(255,255,255,0.25)" }} />
                          <span style={{ color: "rgba(255,255,255,0.45)", fontSize: "13px" }}>
                            Next: {next.title}
                          </span>
                        </div>
                      );
                    return (
                      <div className="flex items-center gap-2.5">
                        <CheckCircle2 size={14} color="#22C55E" />
                        <span style={{ color: "#22C55E", fontSize: "13px", fontWeight: 600 }}>
                          All steps verified!
                        </span>
                      </div>
                    );
                  })()}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Success Overlay ── */}
        <AnimatePresence>
          {showSuccess && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 z-50 flex flex-col items-center justify-center"
              style={{ background: "rgba(0,0,0,0.93)", backdropFilter: "blur(24px)" }}
            >
              {/* Ambient rings */}
              {[80, 160, 240].map((size, i) => (
                <motion.div
                  key={size}
                  className="absolute rounded-full"
                  style={{ width: size * 2, height: size * 2, border: `1px solid rgba(255,205,17,${0.12 - i * 0.03})` }}
                  animate={{ scale: [1, 1.04, 1] }}
                  transition={{ duration: 3.5, repeat: Infinity, delay: i * 0.5 }}
                />
              ))}

              {/* Check circle */}
              <motion.div
                initial={{ scale: 0, rotate: -20 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: "spring", stiffness: 260, damping: 18, delay: 0.15 }}
                className="w-28 h-28 rounded-full flex items-center justify-center mb-7"
                style={{
                  background: "linear-gradient(135deg, #FFCD11 0%, #FFB000 100%)",
                  boxShadow: "0 0 64px rgba(255,205,17,0.35), 0 0 140px rgba(255,205,17,0.12)",
                }}
              >
                <motion.div
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5, type: "spring", stiffness: 380 }}
                >
                  <CheckCircle2 size={54} color="#0D0D0D" strokeWidth={2.5} />
                </motion.div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.55 }}
                className="text-center px-8"
              >
                <p style={{ color: "#FFCD11", fontSize: "11px", fontWeight: 800, letterSpacing: "0.2em" }} className="uppercase mb-2">
                  Inspection Complete
                </p>
                <h2 style={{ color: "white", fontSize: "30px", fontWeight: 900, lineHeight: 1.15 }}>
                  Maintenance<br />Check Passed
                </h2>
                <p style={{ color: "rgba(255,255,255,0.45)", fontSize: "13px" }} className="mt-3 leading-relaxed">
                  All 6 components verified<br />{machineName}
                </p>
                <div className="flex gap-3 mt-6 justify-center">
                  {[
                    { label: "Parts Scanned", value: "6" },
                    { label: "Issues Found", value: "0" },
                    { label: "Duration", value: "~22s" },
                  ].map((s) => (
                    <div
                      key={s.label}
                      className="px-3.5 py-2.5 rounded-2xl"
                      style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)" }}
                    >
                      <p style={{ color: "#FFCD11", fontWeight: 800, fontSize: "19px", lineHeight: 1 }}>{s.value}</p>
                      <p style={{ color: "rgba(255,255,255,0.4)", fontSize: "9px" }} className="mt-1">{s.label}</p>
                    </div>
                  ))}
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.75 }}
                className="absolute bottom-10 inset-x-6 space-y-3"
              >
                <button
                  onClick={() => navigate("/history")}
                  className="w-full py-4 rounded-3xl"
                  style={{
                    background: "linear-gradient(135deg, #FFCD11 0%, #FFB000 100%)",
                    boxShadow: "0 8px 32px rgba(255,205,17,0.28)",
                  }}
                >
                  <span style={{ color: "#0D0D0D", fontWeight: 800, fontSize: "16px" }}>View Report</span>
                </button>
                <button
                  onClick={resetScan}
                  className="w-full py-4 rounded-3xl"
                  style={{ background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.11)" }}
                >
                  <span style={{ color: "rgba(255,255,255,0.65)", fontSize: "15px" }}>Scan Again</span>
                </button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
