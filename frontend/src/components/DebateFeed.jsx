import { useLang } from '../i18n.jsx';

function FallacyCallout({ fallacy }) {
  const { t, fallacyName } = useLang();
  return (
    <div className="fallacy">
      <div className="fallacy-head">
        <span className="foul-badge">{t('feed.foul')}</span>
        <strong>{fallacyName(fallacy.type)}</strong>
      </div>
      <p>{fallacy.explanation}</p>
      <p className="fix">
        <em>{t('feed.fix')}</em> {fallacy.fix}
      </p>
    </div>
  );
}

function Move({ side, text, analysis }) {
  const { t } = useLang();
  return (
    <div className={`move ${side}`}>
      <div className="move-meta">
        <span className="who">{side === 'user' ? t('feed.you') : 'Crossfire'}</span>
        <span className="score-chip num" title={analysis.score_reason || t('feed.score.title')}>
          {analysis.score.toFixed(1)}
        </span>
      </div>
      <p className="move-text">{text}</p>
      {(analysis.fallacies || []).map((f, i) => (
        <FallacyCallout key={i} fallacy={f} />
      ))}
    </div>
  );
}

function ThinkingBubble({ label }) {
  return (
    <div className="thinking-bubble" aria-live="polite">
      <div className="dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <span className="thinking-label">{label}</span>
    </div>
  );
}

function FlipCard({ flip }) {
  const { t } = useLang();
  return (
    <div className="flip-card">
      <div className="flip-head">
        <span className="flip-badge">{t('feed.sideswitch')}</span>
        <span className="muted">{t('feed.sideswitch.sub')}</span>
      </div>
      <p className="move-text">{flip.flipped_move}</p>
      {flip.gap_note && (
        <p className="flip-gap">
          <em>{t('feed.gap')}</em> {flip.gap_note}
        </p>
      )}
    </div>
  );
}

function HygieneLine({ hygiene }) {
  const { t } = useLang();
  // rebuild the line from claim checks so it localizes; fall back to the
  // backend string if checks are missing
  const checks = hygiene.checks || [];
  let text = hygiene.text;
  if (checks.length) {
    const v = checks.filter((c) => c.verdict === 'verified').length;
    const d = checks.filter((c) => c.verdict === 'disputed').length;
    const u = checks.filter((c) => c.verdict === 'unverifiable').length;
    text =
      `${checks.length} ${t('feed.hygiene.claims')} · ${v} ${t('feed.hygiene.verified')} · ` +
      `${d} ${t('feed.hygiene.disputed')} · ${u} ${t('feed.hygiene.unverifiable')}`;
  }
  return (
    <div className="hygiene" title={t('feed.hygiene.title')}>
      {text}
    </div>
  );
}

export default function DebateFeed({ turns, flips, thinking }) {
  const { t } = useLang();
  if (!turns.length && !thinking) {
    return (
      <div className="feed-empty">
        <h3>{t('feed.empty.title')}</h3>
        <p>{t('feed.empty.desc')}</p>
      </div>
    );
  }
  const flipsByRound = {};
  (flips || []).forEach((f) => {
    (flipsByRound[f.after_round] = flipsByRound[f.after_round] || []).push(f);
  });
  return (
    <div className="feed">
      {turns.map((turn) => (
        <div key={turn.round_no} className="round">
          <div className="round-head">
            <div className="round-label">
              {t('feed.round')} {turn.round_no}
            </div>
            <div className="round-rule" />
          </div>
          <Move side="user" text={turn.user_move} analysis={turn.user_analysis} />
          <Move side="opponent" text={turn.opponent_move} analysis={turn.opponent_analysis} />
          <HygieneLine hygiene={{ text: turn.hygiene, checks: turn.claim_checks }} />
          {(flipsByRound[turn.round_no] || []).map((f, i) => (
            <FlipCard key={i} flip={f} />
          ))}
        </div>
      ))}
      {thinking && <ThinkingBubble label={t('feed.thinking')} />}
    </div>
  );
}
