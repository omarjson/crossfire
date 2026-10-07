import { useLang } from '../i18n.jsx';

function hygieneClass(ratio) {
  if (ratio >= 0.8) return 'good';
  if (ratio >= 0.5) return 'mid';
  return 'poor';
}

export default function Verdict({ verdict, onRematch }) {
  const { t, fallacyName } = useLang();
  const rc = verdict.report_card || {};
  const profile = Object.entries(rc.fallacy_profile || {}).sort((a, b) => b[1] - a[1]);
  const maxCount = profile.length ? profile[0][1] : 1;
  const hygiene = rc.evidence_hygiene ?? 1;

  const winClass =
    verdict.winner === 'user' ? 'win-user' : verdict.winner === 'opponent' ? 'win-opponent' : 'win-draw';
  const title =
    verdict.winner === 'user'
      ? t('verdict.win.user')
      : verdict.winner === 'opponent'
        ? t('verdict.win.opponent')
        : t('verdict.win.draw');

  return (
    <div className="verdict-wrap">
      <div className={`winner-banner ${winClass}`}>
        <div className="winner-kicker">{t('verdict.kicker')}</div>
        <h2 className="winner-title">{title}</h2>
        <div className="winner-score">
          <div>
            <div className="n num who-you">{verdict.user_total.toFixed(1)}</div>
            <span className="lbl">{t('verdict.you')}</span>
          </div>
          <div>
            <div className="n num who-cf">{verdict.opponent_total.toFixed(1)}</div>
            <span className="lbl">{t('verdict.cf')}</span>
          </div>
        </div>
      </div>

      {verdict.summary && <p className="verdict-summary">{verdict.summary}</p>}

      <h3>{t('verdict.scorecard')}</h3>
      <table className="wide">
        <thead>
          <tr>
            <th>{t('verdict.th.round')}</th>
            <th>{t('verdict.th.you')}</th>
            <th>{t('verdict.th.cf')}</th>
            <th>{t('verdict.th.note')}</th>
          </tr>
        </thead>
        <tbody>
          {verdict.rounds.map((r) => {
            const youWon = r.user_score > r.opponent_score;
            const cfWon = r.opponent_score > r.user_score;
            return (
              <tr key={r.round} className={youWon || cfWon ? 'round-won' : ''}>
                <td className="num">{r.round}</td>
                <td className="num">
                  {r.user_score.toFixed(1)} {youWon && <span className="w">●</span>}
                </td>
                <td className="num">
                  {r.opponent_score.toFixed(1)} {cfWon && <span className="w">●</span>}
                </td>
                <td>{r.note}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <h3>{t('verdict.report')}</h3>
      <div className="report-grid">
        <div className="report-cell">
          <span className="rc-label">{t('verdict.fallacyProfile')}</span>
          {profile.length === 0 ? (
            <p className="muted">{t('verdict.clean')}</p>
          ) : (
            <div className="bars">
              {profile.map(([type, n]) => (
                <div key={type} className="bar-row">
                  <span className="bar-label">{fallacyName(type)}</span>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${Math.min(100, (n / maxCount) * 100)}%` }} />
                  </div>
                  <span className="bar-num num">{n}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="report-cell">
          <span className="rc-label">{t('verdict.hygiene')}</span>
          <strong className={`big ${hygieneClass(hygiene)}`}>{Math.round(hygiene * 100)}%</strong>
          <p className="muted" style={{ margin: '8px 0 0' }}>
            {t('verdict.hygiene.sub')}
          </p>
        </div>
        <div className="report-cell tips-cell">
          <span className="rc-label">{t('verdict.tips')}</span>
          {(rc.tips || []).length === 0 ? (
            <p className="muted">{t('verdict.noTips')}</p>
          ) : (
            <ul className="tips-list">
              {rc.tips.map((tip, i) => (
                <li key={i}>{tip}</li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <button className="btn-primary" onClick={onRematch}>
        {t('verdict.rematch')}
      </button>
    </div>
  );
}
