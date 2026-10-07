import { useLang } from '../i18n.jsx';

export default function Scoreboard({ scoreboard, onEnd, busy }) {
  const { t } = useLang();
  if (!scoreboard) return null;
  const { rounds, user_total, opponent_total } = scoreboard;
  const latest = rounds.length ? rounds[rounds.length - 1].round : null;
  const leader =
    rounds.length === 0
      ? null
      : user_total > opponent_total
        ? 'you'
        : opponent_total > user_total
          ? 'cf'
          : 'tied';

  return (
    <aside className="scoreboard">
      <h3>{t('score.title')}</h3>
      {leader && (
        <span className="leader-pill">
          {leader === 'you' && (
            <>
              <span className="you">{t('score.youLead')}</span> {user_total.toFixed(1)} –{' '}
              {opponent_total.toFixed(1)}
            </>
          )}
          {leader === 'cf' && (
            <>
              <span className="cf">{t('score.cfLead')}</span> {opponent_total.toFixed(1)} –{' '}
              {user_total.toFixed(1)}
            </>
          )}
          {leader === 'tied' && (
            <>
              {t('score.tied')} {user_total.toFixed(1)}
            </>
          )}
        </span>
      )}
      {rounds.length === 0 ? (
        <p className="muted">{t('score.empty')}</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>{t('score.rd')}</th>
              <th>{t('score.you')}</th>
              <th>{t('score.cf')}</th>
            </tr>
          </thead>
          <tbody>
            {rounds.map((r) => (
              <tr key={r.round} className={r.round === latest ? 'latest' : ''}>
                <td className="num">{r.round}</td>
                <td className="num">{r.user_score.toFixed(1)}</td>
                <td className="num">{r.opponent_score.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td>{t('score.total')}</td>
              <td className="num">{user_total.toFixed(1)}</td>
              <td className="num">{opponent_total.toFixed(1)}</td>
            </tr>
          </tfoot>
        </table>
      )}
      {rounds.length > 0 && (
        <button className="btn-judge" disabled={busy} onClick={onEnd}>
          {busy ? t('score.judging') : t('score.end')}
        </button>
      )}
    </aside>
  );
}
