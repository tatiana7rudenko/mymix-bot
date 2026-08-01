import { motion, useReducedMotion } from "motion/react";
import AnimatedVideoPortrait from "./components/AnimatedVideoPortrait";
import "./App.css";

export default function App() {
  const reduced = useReducedMotion();

  const fadeUp = (delay: number) => ({
    initial: reduced ? { opacity: 0 } : { opacity: 0, y: 18 },
    animate: reduced ? { opacity: 1 } : { opacity: 1, y: 0 },
    transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] as const, delay },
  });

  return (
    <main className="page">
      <AnimatedVideoPortrait
        src="/video/portrait-placeholder.webm"
        framePosition="50% 28%"
        size={260}
      />

      <section className="hero">
        <motion.p className="hero__eyebrow" {...fadeUp(0.15)}>
          MyMix · знакомства и саморазвитие
        </motion.p>
        <motion.h1 className="hero__title" {...fadeUp(0.25)}>
          Гра почалася.
          <br />
          Тебе чекають нові знайомства
        </motion.h1>
        <motion.p className="hero__lead" {...fadeUp(0.35)}>
          Завдання по саморозвитку, живі люди та підтримка на кожному кроці.
          Натисни «Продовжити» — і рухаймося далі разом.
        </motion.p>
        <motion.div className="hero__actions" {...fadeUp(0.45)}>
          <a className="btn btn--primary" href="#start">
            Продовжити
          </a>
          <a className="btn btn--ghost" href="#help">
            Потрібна допомога
          </a>
        </motion.div>
      </section>
    </main>
  );
}
