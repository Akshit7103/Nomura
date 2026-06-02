"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();

  function handleSubmit(e) {
    e.preventDefault();
    router.push("/schedules");
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center overflow-hidden"
      style={{
        background:
          "linear-gradient(135deg, #818cf8 0%, #60a5fa 55%, #38bdf8 100%)",
      }}
    >
      {/* Sparkles */}
      {[
        {
          left: "6%",
          top: "72%",
          size: 3,
          dur: 4.5,
          delay: 0,
          anim: "sparkle-float",
        },
        {
          left: "14%",
          top: "55%",
          size: 5,
          dur: 6,
          delay: 1.2,
          anim: "sparkle-twinkle",
        },
        {
          left: "22%",
          top: "80%",
          size: 2,
          dur: 5,
          delay: 0.6,
          anim: "sparkle-float",
        },
        {
          left: "32%",
          top: "20%",
          size: 4,
          dur: 7,
          delay: 2,
          anim: "sparkle-twinkle",
        },
        {
          left: "42%",
          top: "65%",
          size: 3,
          dur: 5.5,
          delay: 0.3,
          anim: "sparkle-drift",
        },
        {
          left: "50%",
          top: "85%",
          size: 5,
          dur: 6.5,
          delay: 1.8,
          anim: "sparkle-float",
        },
        {
          left: "58%",
          top: "30%",
          size: 3,
          dur: 4,
          delay: 0.9,
          anim: "sparkle-twinkle",
        },
        {
          left: "67%",
          top: "75%",
          size: 4,
          dur: 7,
          delay: 2.5,
          anim: "sparkle-float",
        },
        {
          left: "75%",
          top: "45%",
          size: 2,
          dur: 5,
          delay: 0.4,
          anim: "sparkle-drift",
        },
        {
          left: "83%",
          top: "60%",
          size: 6,
          dur: 8,
          delay: 1.5,
          anim: "sparkle-twinkle",
        },
        {
          left: "90%",
          top: "25%",
          size: 3,
          dur: 5.5,
          delay: 0.7,
          anim: "sparkle-float",
        },
        {
          left: "10%",
          top: "35%",
          size: 4,
          dur: 6,
          delay: 3,
          anim: "sparkle-drift",
        },
        {
          left: "48%",
          top: "15%",
          size: 3,
          dur: 4.5,
          delay: 1.1,
          anim: "sparkle-float",
        },
        {
          left: "77%",
          top: "88%",
          size: 2,
          dur: 6,
          delay: 2.2,
          anim: "sparkle-twinkle",
        },
        {
          left: "35%",
          top: "50%",
          size: 5,
          dur: 7.5,
          delay: 0.5,
          anim: "sparkle-float",
        },
        {
          left: "62%",
          top: "10%",
          size: 3,
          dur: 5,
          delay: 3.5,
          anim: "sparkle-drift",
        },
        {
          left: "88%",
          top: "78%",
          size: 4,
          dur: 6,
          delay: 1.8,
          anim: "sparkle-twinkle",
        },
        {
          left: "25%",
          top: "90%",
          size: 2,
          dur: 4,
          delay: 2.8,
          anim: "sparkle-float",
        },
      ].map((s, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: s.left,
            top: s.top,
            width: s.size,
            height: s.size,
            borderRadius: s.anim === "sparkle-twinkle" ? "2px" : "50%",
            background: "white",
            boxShadow: `0 0 ${s.size * 2}px ${s.size}px rgba(255,255,255,0.6)`,
            animation: `${s.anim} ${s.dur}s ${s.delay}s ease-in-out infinite`,
            pointerEvents: "none",
          }}
        />
      ))}

      <div
        className="bg-white flex overflow-hidden shadow-2xl"
        style={{ width: 780, height: 460 }}
      >
        {/* ── Left: dark panel with illustration ── */}
        <div
          className="relative flex flex-col items-center justify-center flex-shrink-0 overflow-hidden"
          style={{
            width: 340,
            background: "linear-gradient(160deg, #112244 0%, #091326 100%)",
          }}
        >
          {/* subtle grid lines */}
          <svg
            className="absolute inset-0 w-full h-full opacity-10"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <pattern
                id="grid"
                width="28"
                height="28"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 28 0 L 0 0 0 28"
                  fill="none"
                  stroke="#60a5fa"
                  strokeWidth="0.5"
                />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>

          {/* floating accent dots */}
          <div className="absolute top-8 left-8 w-2 h-2 rounded-full bg-sky-400 opacity-60" />
          <div className="absolute top-16 right-12 w-1.5 h-1.5 rounded-full bg-indigo-400 opacity-50" />
          <div className="absolute bottom-16 left-14 w-1.5 h-1.5 rounded-full bg-sky-400 opacity-50" />
          <div className="absolute bottom-10 right-10 w-2 h-2 rounded-full bg-violet-400 opacity-40" />

          {/* AI Bot SVG */}
          <svg
            viewBox="0 0 120 145"
            fill="none"
            width="160"
            height="194"
            className="relative z-10"
          >
            {/* antenna */}
            <line
              x1="60"
              y1="6"
              x2="60"
              y2="26"
              stroke="#475569"
              strokeWidth="3"
              strokeLinecap="round"
            />
            <circle cx="60" cy="6" r="6" fill="#38bdf8" />
            <circle cx="60" cy="6" r="3" fill="#e0f2fe" />

            {/* head */}
            <rect x="14" y="26" width="92" height="74" rx="16" fill="#1e293b" />

            {/* left eye */}
            <circle cx="38" cy="58" r="15" fill="#0c4a6e" />
            <circle cx="38" cy="58" r="10" fill="#0ea5e9" />
            <circle cx="38" cy="58" r="5" fill="#e0f2fe" />
            <circle cx="38" cy="58" r="2.5" fill="#0f172a" />
            <circle cx="40.5" cy="55.5" r="1.5" fill="white" opacity="0.8" />

            {/* right eye */}
            <circle cx="82" cy="58" r="15" fill="#0c4a6e" />
            <circle cx="82" cy="58" r="10" fill="#0ea5e9" />
            <circle cx="82" cy="58" r="5" fill="#e0f2fe" />
            <circle cx="82" cy="58" r="2.5" fill="#0f172a" />
            <circle cx="84.5" cy="55.5" r="1.5" fill="white" opacity="0.8" />

            {/* smile */}
            <path
              d="M40 80 Q60 92 80 80"
              stroke="#38bdf8"
              strokeWidth="3"
              strokeLinecap="round"
              fill="none"
            />

            {/* ears */}
            <rect x="6" y="40" width="8" height="22" rx="4" fill="#334155" />
            <rect x="106" y="40" width="8" height="22" rx="4" fill="#334155" />

            {/* neck */}
            <rect x="44" y="100" width="32" height="12" rx="4" fill="#334155" />
            <rect x="48" y="103" width="5" height="6" rx="2" fill="#475569" />
            <rect x="57" y="103" width="5" height="6" rx="2" fill="#475569" />
            <rect x="66" y="103" width="5" height="6" rx="2" fill="#475569" />
          </svg>

          {/* label */}
          <p
            className="relative z-10 mt-4 text-[11px] font-medium tracking-widest uppercase"
            style={{ color: "rgba(255,255,255,0.3)" }}
          >
            AI · Powered
          </p>
        </div>

        {/* ── Right: form ── */}
        <div className="flex-1 flex flex-col justify-center px-12">
          <h3 className="text-[18px]  text-gray-700 mb-1 text-center tracking-tight">
            Agentic Workflows Admin Panel | Login
          </h3>
          <br></br>

          <form onSubmit={handleSubmit} className="space-y-3">
            {/* Email */}
            <div
              className="flex items-center gap-3 px-4 py-3"
              style={{ background: "#f1f5f9" }}
            >
              <svg
                viewBox="0 0 20 20"
                fill="currentColor"
                className="w-4 h-4 flex-shrink-0 text-gray-400"
              >
                <path d="M3 4a2 2 0 0 0-2 2v1.161l8.441 4.221a1.25 1.25 0 0 0 1.118 0L19 7.162V6a2 2 0 0 0-2-2H3Z" />
                <path d="m19 8.839-7.77 3.885a2.75 2.75 0 0 1-2.46 0L1 8.839V14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8.839Z" />
              </svg>
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 bg-transparent outline-none text-sm text-gray-600 placeholder-gray-400"
              />
            </div>

            {/* Password */}
            <div
              className="flex items-center gap-3 px-4 py-3"
              style={{ background: "#f1f5f9" }}
            >
              <svg
                viewBox="0 0 20 20"
                fill="currentColor"
                className="w-4 h-4 flex-shrink-0 text-gray-400"
              >
                <path
                  fillRule="evenodd"
                  d="M10 1a4.5 4.5 0 0 0-4.5 4.5V9H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2h-.5V5.5A4.5 4.5 0 0 0 10 1Zm3 8V5.5a3 3 0 1 0-6 0V9h6Z"
                  clipRule="evenodd"
                />
              </svg>
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="flex-1 bg-transparent outline-none text-sm text-gray-600 placeholder-gray-400"
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 text-white text-xs font-bold tracking-[0.18em] uppercase transition-opacity hover:opacity-90"
              style={{ background: "#2356d4" }}
            >
              Login
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
