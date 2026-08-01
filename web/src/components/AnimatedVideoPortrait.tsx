import { useCallback, useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { motion, useReducedMotion } from "motion/react";
import "./AnimatedVideoPortrait.css";

export interface AnimatedVideoPortraitProps {
  /** Путь к видеофайлу (mp4 / webm). */
  src: string;
  /** Постер, показывается до первого кадра. */
  poster?: string;
  /**
   * object-position видео внутри круга. Задаётся по реальному положению
   * лица в кадре: для вертикального рилса с лицом в верхней трети
   * подходит "50% 25%"–"50% 32%". Не оставляйте слепое "center".
   */
  framePosition?: string;
  /** Диаметр круга на десктопе, px (220–280 рекомендовано). */
  size?: number;
  /** Диаметр на планшете (по умолчанию ~0.78 от size). */
  sizeTablet?: number;
  /** Диаметр на мобильном (по умолчанию ~0.54 от size). */
  sizeMobile?: number;
  /** Градиент или цвет тонкой рамки вокруг круга. */
  ringColor?: string;
  /** Мягкое свечение позади круга. */
  glow?: boolean;
  /** Цвет свечения (полупрозрачный). */
  glowColor?: string;
  /** Орбитальные линии, частицы, градиентное пятно, связующая линия. */
  decorations?: boolean;
  className?: string;
}

const SPRING = {
  type: "spring" as const,
  stiffness: 120,
  damping: 19,
  mass: 1,
};

export default function AnimatedVideoPortrait({
  src,
  poster,
  framePosition = "50% 28%",
  size = 260,
  sizeTablet,
  sizeMobile,
  ringColor = "linear-gradient(140deg, #d8b28e 0%, #c98d7b 45%, #9d6b5e 100%)",
  glow = true,
  glowColor = "rgba(206, 154, 120, 0.4)",
  decorations = true,
  className,
}: AnimatedVideoPortraitProps) {
  const reduced = useReducedMotion();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [muted, setMuted] = useState(true);
  const [failed, setFailed] = useState(false);

  // iOS/Android: авто-плей гарантирован только для программно
  // замьюченного видео, поэтому дублируем атрибут свойством.
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    v.muted = true;
    v.play().catch(() => {
      /* автоплей заблокирован — видео стартует по первому тапу */
    });
  }, []);

  const toggleSound = useCallback(() => {
    const v = videoRef.current;
    if (!v || failed) return;
    const nextMuted = !v.muted;
    v.muted = nextMuted;
    setMuted(nextMuted);
    if (v.paused) v.play().catch(() => {});
  }, [failed]);

  const styleVars = {
    "--avp-size-desktop": `${size}px`,
    "--avp-size-tablet": `${sizeTablet ?? Math.round(size * 0.78)}px`,
    "--avp-size-mobile": `${sizeMobile ?? Math.round(size * 0.54)}px`,
    "--avp-ring": ringColor,
    "--avp-glow-color": glowColor,
  } as CSSProperties;

  return (
    <motion.div
      className={`avp ${className ?? ""}`}
      style={styleVars}
      initial={
        reduced
          ? { opacity: 0 }
          : { opacity: 0, scale: 0.82, x: 50, y: -40, rotate: 4 }
      }
      animate={
        reduced
          ? { opacity: 1 }
          : { opacity: 1, scale: 1, x: 0, y: 0, rotate: 0 }
      }
      transition={
        reduced
          ? { duration: 0.35, ease: "easeOut" }
          : { ...SPRING, opacity: { duration: 0.55, ease: "easeOut" } }
      }
    >
      {decorations && (
        <div className="avp__scene" aria-hidden="true">
          <div className="avp__blob" />
          <div className="avp__orbit avp__orbit--near">
            <span className="avp__orbit-dot" />
          </div>
          <div className="avp__orbit avp__orbit--far">
            <span className="avp__orbit-dot avp__orbit-dot--small" />
          </div>
          <span className="avp__particle avp__particle--a" />
          <span className="avp__particle avp__particle--b" />
          <span className="avp__particle avp__particle--c" />
          <span className="avp__thread" />
        </div>
      )}

      <motion.div
        className="avp__float"
        animate={reduced ? undefined : { y: [0, -4, 0] }}
        transition={{
          duration: 6,
          ease: "easeInOut",
          repeat: Infinity,
          delay: 1.1,
        }}
      >
        {glow && <div className="avp__glow" aria-hidden="true" />}

        <motion.div
          className="avp__frame"
          whileHover={reduced ? undefined : { scale: 1.03 }}
          transition={{ type: "spring", stiffness: 260, damping: 22 }}
        >
          <div className="avp__gap">
            <div
              className="avp__circle"
              onClick={toggleSound}
              role="presentation"
            >
              {failed ? (
                <div className="avp__fallback" />
              ) : (
                <video
                  ref={videoRef}
                  className="avp__video"
                  src={src}
                  poster={poster}
                  style={{ objectPosition: framePosition }}
                  autoPlay
                  muted
                  loop
                  playsInline
                  preload="metadata"
                  onError={() => setFailed(true)}
                />
              )}

              <button
                type="button"
                className="avp__sound"
                aria-label={muted ? "Включить звук" : "Выключить звук"}
                aria-pressed={!muted}
                onClick={(e) => {
                  e.stopPropagation();
                  toggleSound();
                }}
              >
                {muted ? (
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none">
                    <path
                      d="M11 5.5 6.8 9H4a1 1 0 0 0-1 1v4a1 1 0 0 0 1 1h2.8L11 18.5a.6.6 0 0 0 1-.46V5.96a.6.6 0 0 0-1-.46Z"
                      fill="currentColor"
                    />
                    <path
                      d="m16 9.5 5 5m0-5-5 5"
                      stroke="currentColor"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                    />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none">
                    <path
                      d="M11 5.5 6.8 9H4a1 1 0 0 0-1 1v4a1 1 0 0 0 1 1h2.8L11 18.5a.6.6 0 0 0 1-.46V5.96a.6.6 0 0 0-1-.46Z"
                      fill="currentColor"
                    />
                    <path
                      d="M15.5 9.3a4 4 0 0 1 0 5.4M18 7a7.4 7.4 0 0 1 0 10"
                      stroke="currentColor"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                    />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}
