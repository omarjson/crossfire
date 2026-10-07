import { useEffect, useMemo, useRef, useState } from 'react';
import { useLang } from '../i18n.jsx';
import LangToggle from './LangToggle.jsx';

const PERSONA_IDS = ['skeptic', 'lawyer', 'contrarian', 'economist'];
const DIFF_IDS = ['friendly', 'rigorous', 'hostile'];

const MAX_MOTION = 500;

/* Typewriter for the gold headline line: types part A, photo pops in,
   then types part B. */
function TypeLine() {
  const { t } = useLang();
  const PART1 = t('landing.hero.tA');
  const PART2 = t('landing.hero.tB');
  const [phase, setPhase] = useState(0);
  const [chars, setChars] = useState(0);
  const reduceMotion = useMemo(
    () =>
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    []
  );

  // restart the typing when the language changes
  useEffect(() => {
    setPhase(0);
    setChars(0);
  }, [PART1, PART2]);

  useEffect(() => {
    if (reduceMotion) {
      setPhase(3);
      setChars(PART2.length);
      return;
    }
    let timer;
    if (phase === 0) {
      if (chars < PART1.length) timer = setTimeout(() => setChars((c) => c + 1), 55);
      else timer = setTimeout(() => setPhase(1), 300);
    } else if (phase === 1) {
      timer = setTimeout(() => {
        setPhase(2);
        setChars(0);
      }, 500);
    } else if (phase === 2) {
      if (chars < PART2.length) timer = setTimeout(() => setChars((c) => c + 1), 55);
      else timer = setTimeout(() => setPhase(3), 500);
    }
    return () => clearTimeout(timer);
  }, [phase, chars, reduceMotion, PART1, PART2]);

  return (
    <span className="gold">
      {phase === 0 ? PART1.slice(0, chars) : PART1}
      {phase >= 1 && <span className="type-photo pop" aria-hidden="true" />}
      {phase >= 2 && PART2.slice(0, chars)}
      {phase < 3 && <span className="caret" aria-hidden="true" />}
    </span>
  );
}

/* Subtle fade-up on scroll for sections. */
function Reveal({ children, className = '' }) {
  const ref = useRef(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === 'undefined') {
      setSeen(true);
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setSeen(true);
          io.disconnect();
        }
      },
      { threshold: 0.12 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <div ref={ref} className={`reveal${seen ? ' in' : ''} ${className}`}>
      {children}
    </div>
  );
}

export default function Landing({ onStart, busy, error, onProgress }) {
  const { t, lang } = useLang();
  const [motion, setMotion] = useState('');
  const [persona, setPersona] = useState('skeptic');
  const [difficulty, setDifficulty] = useState('rigorous');

  const valid = motion.trim().length >= 10 && motion.trim().length <= MAX_MOTION;

  const scrollToSetup = () =>
    document.getElementById('setup')?.scrollIntoView({ behavior: 'smooth' });

  const samples = [1, 2, 3, 4].map((n) => t(`landing.sample.${n}`));

  return (
    <div className="landing">
      {/* the "screen" — entire page framed as one rounded card on sand */}
      <div className="screen">
        {/* nav inside the screen */}
        <header className="screen-nav">
          <span className="logo">
            Cross<span>fire</span>
          </span>
          <span className="screen-nav-actions">
            <LangToggle />
            <button className="ghost" onClick={onProgress} disabled={busy}>
              {t('nav.record')}
            </button>
          </span>
        </header>

        {/* hero */}
        <section className="hero">
          <h1>
            {t('landing.hero.l1')}
            <br />
            {t('landing.hero.l2')}
            <br />
            <TypeLine />
          </h1>
          <p className="hero-sub">{t('landing.hero.sub')}</p>
          <div className="hero-ctas">
            <button className="btn-primary" onClick={scrollToSetup}>
              {t('landing.cta.enter')}
            </button>
            <button className="btn-ghost-arrow" onClick={scrollToSetup}>
              <span>{t('landing.cta.how')}</span>
              <span className="circle-arrow" aria-hidden="true">
                {lang === 'ar' ? '↓' : '↓'}
              </span>
            </button>
          </div>
        </section>

        {/* credibility strip */}
        <ul className="cred-strip">
          <li>{t('landing.cred.1')}</li>
          <li>{t('landing.cred.2')}</li>
          <li>{t('landing.cred.3')}</li>
          <li>{t('landing.cred.4')}</li>
        </ul>
      </div>

      {/* how it works */}
      <Reveal>
        <section className="how">
          <h2>{t('landing.how.title')}</h2>
          <p className="section-sub">{t('landing.how.sub')}</p>
          <div className="steps">
            <div className="step">
              <div className="step-num">01</div>
              <h3>{t('landing.step1.title')}</h3>
              <p>{t('landing.step1.desc')}</p>
            </div>
            <div className="step">
              <div className="step-num">02</div>
              <h3>{t('landing.step2.title')}</h3>
              <p>{t('landing.step2.desc')}</p>
            </div>
            <div className="step">
              <div className="step-num">03</div>
              <h3>{t('landing.step3.title')}</h3>
              <p>{t('landing.step3.desc')}</p>
            </div>
          </div>
        </section>
      </Reveal>

      {/* guided setup */}
      <Reveal>
        <section className="setup-section" id="setup">
          <h2>{t('landing.setup.title')}</h2>
          <p className="section-sub">{t('landing.setup.sub')}</p>

          <div className="setup-step">
            <div className="step-head">
              <span className="n">01</span>
              <h3>{t('landing.s1.title')}</h3>
            </div>
            <p className="step-hint">{t('landing.s1.hint')}</p>
            <textarea
              value={motion}
              onChange={(e) => setMotion(e.target.value.slice(0, MAX_MOTION))}
              rows={3}
              placeholder={t('landing.s1.placeholder')}
            />
            <div className={`char-count${motion.length >= MAX_MOTION ? ' over' : ''}`}>
              {motion.trim().length < 10
                ? `${t('landing.s1.min')} (${motion.trim().length})`
                : `${motion.trim().length}/${MAX_MOTION}`}
            </div>
            {lang === 'ar' && (
              <p className="lang-note">{t('landing.s1.englishNote')}</p>
            )}
            <div className="samples">
              <span className="sample-label">{t('landing.s1.samples')}</span>
              {samples.map((s) => (
                <button key={s} type="button" className="sample-chip" onClick={() => setMotion(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="setup-step">
            <div className="step-head">
              <span className="n">02</span>
              <h3>{t('landing.s2.title')}</h3>
            </div>
            <p className="step-hint">{t('landing.s2.hint')}</p>
            <div className="persona-grid">
              {PERSONA_IDS.map((id) => (
                <button
                  key={id}
                  type="button"
                  className={persona === id ? 'persona selected' : 'persona'}
                  onClick={() => setPersona(id)}
                >
                  <strong>{t(`persona.${id}.name`)}</strong>
                  <span>{t(`persona.${id}.desc`)}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="setup-step">
            <div className="step-head">
              <span className="n">03</span>
              <h3>{t('landing.s3.title')}</h3>
            </div>
            <p className="step-hint">{t('landing.s3.hint')}</p>
            <div className="seg">
              {DIFF_IDS.map((id) => (
                <button
                  key={id}
                  type="button"
                  className={difficulty === id ? 'selected' : ''}
                  onClick={() => setDifficulty(id)}
                >
                  {t(`diff.${id}.name`)}
                  <small>{t(`diff.${id}.hint`)}</small>
                </button>
              ))}
            </div>
          </div>

          {error && <div className="error">{error}</div>}

          <div className="setup-cta">
            <button
              className="btn-primary"
              disabled={busy || !valid}
              onClick={() => onStart(motion.trim(), persona, difficulty)}
            >
              {busy ? t('landing.start.busy') : t('landing.start.idle')}
            </button>
          </div>
        </section>
      </Reveal>
    </div>
  );
}
