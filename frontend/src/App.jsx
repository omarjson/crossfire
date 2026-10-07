import { useRef, useState } from 'react';
import { api } from './api.js';
import { LangProvider, useLang } from './i18n.jsx';
import Landing from './components/Landing.jsx';
import DebateFeed from './components/DebateFeed.jsx';
import Scoreboard from './components/Scoreboard.jsx';
import Verdict from './components/Verdict.jsx';
import ProgressPanel from './components/ProgressPanel.jsx';
import LangToggle from './components/LangToggle.jsx';

function Shell() {
  const { t } = useLang();
  const [phase, setPhase] = useState('landing'); // landing | debate | verdict | progress
  const [prevPhase, setPrevPhase] = useState('landing');
  const [session, setSession] = useState(null);
  const [turns, setTurns] = useState([]);
  const [flips, setFlips] = useState([]);
  const [scoreboard, setScoreboard] = useState(null);
  const [verdict, setVerdict] = useState(null);
  const [progress, setProgress] = useState(null);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState('');
  const [notices, setNotices] = useState([]);
  const feedEnd = useRef(null);

  const scrollDown = () =>
    setTimeout(() => feedEnd.current?.scrollIntoView({ behavior: 'smooth' }), 60);

  async function start(motion, persona, difficulty) {
    setBusy(true);
    setError('');
    setNotices([]);
    try {
      // Debates always run in English: the models spar far better in English
      // than Arabic. The UI language (toggle) is independent.
      const s = await api.createSession(motion, persona, difficulty, 'en');
      setSession(s);
      setTurns([]);
      setScoreboard({ rounds: [], user_total: 0, opponent_total: 0 });
      setVerdict(null);
      setPhase('debate');
      window.scrollTo(0, 0);
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setBusy(false);
    }
  }

  async function sendMove() {
    const text = draft.trim();
    if (!text || busy || !session) return;
    setBusy(true);
    setThinking(true);
    setError('');
    scrollDown();
    try {
      const turn = await api.postMove(session.session_id, text);
      setTurns((t) => [...t, turn]);
      const state = await api.getSession(session.session_id);
      setScoreboard(state.scoreboard);
      if (turn.degraded || (turn.notices && turn.notices.length)) {
        setNotices(turn.notices || [t('arena.cached')]);
      } else {
        setNotices([]);
      }
      setDraft('');
      scrollDown();
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setBusy(false);
      setThinking(false);
    }
  }

  async function flipSides() {
    if (busy || !session || turns.length === 0) return;
    setBusy(true);
    setThinking(true);
    setError('');
    scrollDown();
    try {
      const f = await api.flipSides(session.session_id);
      setFlips((fl) => [...fl, f]);
      scrollDown();
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setBusy(false);
      setThinking(false);
    }
  }

  async function openProgress() {
    setBusy(true);
    setError('');
    try {
      const p = await api.getProgress();
      setProgress(p);
      setPrevPhase(phase);
      setPhase('progress');
      window.scrollTo(0, 0);
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setBusy(false);
    }
  }

  function backFromProgress() {
    setPhase(prevPhase === 'progress' ? 'landing' : prevPhase);
  }

  function goLanding() {
    setPhase('landing');
    setSession(null);
    setTurns([]);
    setFlips([]);
    setScoreboard(null);
    setVerdict(null);
    setDraft('');
    setError('');
    setNotices([]);
    window.scrollTo(0, 0);
  }

  async function endDebate() {
    if (busy || !session) return;
    setBusy(true);
    setError('');
    try {
      const v = await api.endDebate(session.session_id);
      setVerdict(v);
      setPhase('verdict');
      window.scrollTo(0, 0);
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setBusy(false);
    }
  }

  function friendlyError(e) {
    const msg = String(e.message || e);
    if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
      return t('err.offline');
    }
    const m = msg.match(/API (\d+): (.*)/);
    if (m) {
      const body = m[2].replace(/^"|"$/g, '').slice(0, 160);
      if (m[1] === '404') return t('err.expired');
      if (m[1] === '400') return body || t('err.rejected');
      return `${t('err.generic')} (${m[1]})`;
    }
    return msg.slice(0, 200);
  }

  const personaName = (id) => t(`persona.${id}.name`);
  const diffName = (id) => t(`diff.${id}.name`);

  return (
    <div className="app">
      {phase !== 'landing' && (
        <header className="topbar">
          <span className="logo" onClick={phase !== 'debate' ? goLanding : undefined}>
            Cross<span>fire</span>
          </span>
          <span className="topbar-actions">
            <LangToggle />
            <button className="ghost" onClick={openProgress} disabled={busy}>
              {t('nav.record')}
            </button>
          </span>
        </header>
      )}

      {phase === 'landing' && (
        <Landing
          onStart={start}
          busy={busy}
          error={error}
          onProgress={openProgress}
        />
      )}

      {phase === 'debate' && session && (
        <main className="arena">
          <div className="motion-banner">
            <div className="motion-top">
              <span className="live-pill">
                <span className="live-dot" />
                {t('arena.live')}
              </span>
              <span className="motion-persona">
                {personaName(session.persona)} · {diffName(session.difficulty)}
              </span>
            </div>
            <h2 className="motion-text">{session.motion}</h2>
          </div>
          {notices.length > 0 && (
            <div className="notice-banner">
              <strong>{t('arena.headsup')}</strong> {notices.join(' ')}
            </div>
          )}
          <div className="arena-grid">
            <div className="feed-col">
              <DebateFeed turns={turns} flips={flips} thinking={thinking} />
              <div ref={feedEnd} />
              <div className="composer">
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  rows={3}
                  placeholder={t('arena.composer.placeholder')}
                  disabled={busy}
                  maxLength={2000}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) sendMove();
                  }}
                />
                <div className="composer-hint">{t('arena.composer.hint')}</div>
                <div className="composer-actions">
                  <button className="btn-flip" onClick={flipSides} disabled={busy || turns.length === 0} title={t('arena.flip.title')}>
                    {t('arena.flip')}
                  </button>
                  <button className="btn-send" onClick={sendMove} disabled={busy || !draft.trim()}>
                    {busy ? t('arena.send.busy') : t('arena.send.idle')}
                  </button>
                </div>
              </div>
              {error && <div className="error">{error}</div>}
            </div>
            <Scoreboard scoreboard={scoreboard} onEnd={endDebate} busy={busy} />
          </div>
        </main>
      )}

      {phase === 'progress' && (
        <ProgressPanel progress={progress} onBack={backFromProgress} onStart={goLanding} />
      )}

      {phase === 'verdict' && verdict && (
        <Verdict verdict={verdict} onRematch={goLanding} />
      )}
    </div>
  );
}

export default function App() {
  return (
    <LangProvider>
      <Shell />
    </LangProvider>
  );
}
