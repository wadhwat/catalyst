import { Outlet, useLocation, useNavigate } from "react-router";
import { motion } from "motion/react";
import { Camera, Clock, BarChart2 } from "lucide-react";

export function Layout() {
  const location = useLocation();
  const navigate = useNavigate();

  const tabs = [
    { icon: Camera, label: "Machines", path: "/" },
    { icon: Clock, label: "History", path: "/history" },
    { icon: BarChart2, label: "Analytics", path: "/analytics" },
  ];

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center">
      {/* Phone frame on desktop */}
      <div
        className="relative w-full md:max-w-[390px] bg-[#0D0D0D] overflow-hidden"
        style={{ height: "100dvh", maxHeight: "844px" }}
      >
        {/* Status bar */}
        <div className="flex items-center justify-between px-6 pt-3 pb-1 z-50 relative">
          <span className="text-white text-[13px] font-semibold tracking-tight">9:41</span>
          <div className="flex items-center gap-1.5">
            <svg width="17" height="12" viewBox="0 0 17 12" fill="white">
              <rect x="0" y="3" width="3" height="9" rx="1" opacity="0.4"/>
              <rect x="4.5" y="2" width="3" height="10" rx="1" opacity="0.6"/>
              <rect x="9" y="0" width="3" height="12" rx="1" opacity="0.8"/>
              <rect x="13.5" y="0" width="3" height="12" rx="1"/>
            </svg>
            <svg width="16" height="12" viewBox="0 0 16 12" fill="white">
              <path d="M8 2.5C10.5 2.5 12.7 3.6 14.2 5.3L15.5 4C13.7 2 11 0.8 8 0.8C5 0.8 2.3 2 0.5 4L1.8 5.3C3.3 3.6 5.5 2.5 8 2.5Z" opacity="0.4"/>
              <path d="M8 5C9.8 5 11.4 5.8 12.5 7L13.8 5.7C12.4 4.2 10.3 3.3 8 3.3C5.7 3.3 3.6 4.2 2.2 5.7L3.5 7C4.6 5.8 6.2 5 8 5Z" opacity="0.7"/>
              <circle cx="8" cy="10.5" r="1.5"/>
            </svg>
            <div className="flex items-center gap-0.5">
              <div className="w-6 h-3 border border-white/60 rounded-[3px] flex items-center px-0.5">
                <div className="h-1.5 bg-white rounded-sm" style={{ width: "80%" }} />
              </div>
              <div className="w-0.5 h-1.5 bg-white/50 rounded-r-sm" />
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden" style={{ height: "calc(100% - 44px - 70px)" }}>
          <Outlet />
        </div>

        {/* Bottom Tab Bar */}
        <div
          className="absolute bottom-0 left-0 right-0 z-50"
          style={{
            background: "rgba(13,13,13,0.92)",
            backdropFilter: "blur(20px)",
            borderTop: "1px solid rgba(255,255,255,0.08)",
            paddingBottom: "env(safe-area-inset-bottom, 8px)",
          }}
        >
          <div className="flex items-center justify-around pt-2 pb-2">
            {tabs.map((tab) => {
              const isActive = location.pathname === tab.path;
              return (
                <button
                  key={tab.path}
                  onClick={() => navigate(tab.path)}
                  className="flex flex-col items-center gap-1 px-6 py-1 relative"
                >
                  {isActive && (
                    <motion.div
                      layoutId="tab-indicator"
                      className="absolute inset-0 rounded-xl"
                      style={{ background: "rgba(255,205,17,0.08)" }}
                    />
                  )}
                  <tab.icon
                    size={22}
                    color={isActive ? "#FFCD11" : "rgba(255,255,255,0.4)"}
                    strokeWidth={isActive ? 2.5 : 1.5}
                  />
                  <span
                    className="text-[10px] tracking-wide"
                    style={{ color: isActive ? "#FFCD11" : "rgba(255,255,255,0.4)" }}
                  >
                    {tab.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}