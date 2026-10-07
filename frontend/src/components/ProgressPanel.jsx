import { useLang } from '../i18n.jsx';
import LangToggle from './LangToggle.jsx';

export default function ProgressPanel({ progress, onBack, onStart }) {
  const { t, fallacyName } = useLang();

  const head = (
    <div className="progress-head">
      <h2>
        {t('progress.titleA')} <span>{t('progress.titleB')}</span>
      </h2>
      <span className="progress-head-actions">
        <LangToggle />
        <button className="ghost" onClick={onBack}>
          {t('nav.back')}
        </button>
      </span>
    </div>
  );

  if (!progress) {
    return (
      <div className="progress-wrap">
        {head}
        <div className="skeleton title" />
        <div className="skeleton block" />
        <div className="skeleton line" />
        <div className="skeleton line" style={{ width: '70%' }} />
      </div>
    );
  }

  const profile = Object.entries(progress.fallacy_profile || {});
  const maxCount = profile.length ? profile[0][1] : 1;
  const isEmpty = progress.debates === 0;

  return (
    <div className="progress-wrap">
      {head}

      {isEmpty ? (
        <div className="empty-state" style={{ marginTop: 32 }}>
          <h3>{t('progress.empty.title')}</h3>
          <p>{t('progress.empty.desc')}</p>
          <button className="btn-primary" onClick={onStart}>
            {t('progress.empty.cta')}
          </button>
        </div>
      ) : (
        <>
          <div className="stat-row">
            <div className="stat">
              <div className="stat-num num">{progress.debates}</div>
              <div className="stat-label">{t('progress.debates')}</div>
            </div>
            <div className="stat">
              <div className="stat-num num">{progress.total_rounds}</div>
              <div className="stat-label">{t('progress.rounds')}</div>
            </div>
            <div className="stat">
              <div className="stat-num num">{progress.total_flips}</div>
              <div className="stat-label">{t('progress.flips')}</div>
            </div>
            <div className="stat">
              <div className="stat-num num">{progress.fallacy_rate_per_round}</div>
              <div className="stat-label">{t('progress.foulRate')}</div>
            </div>
          </div>

          <h3>{t('progress.fallacyProfile')}</h3>
          {profile.length === 0 ? (
            <p className="muted">{t('progress.clean')}</p>
          ) : (
            <div className="bars">
              {profile.map(([type, n]) => (
                <div key={type} className="bar-row">
                  <span className="bar-label">{fallacyName(type)}</span>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{ width: `${Math.min(100, (n / maxCount) * 100)}%` }}
                    />
                  </div>
                  <span className="bar-num num">{n}</span>
                </div>
              ))}
            </div>
          )}

          <h3>{t('progress.hygieneByDebate')}</h3>
          {(progress.hygiene_by_debate || []).length === 0 ? (
            <p className="muted">{t('progress.none')}</p>
          ) : (
            <table className="progress-table">
              <thead>
                <tr>
                  <th>{t('progress.th.debate')}</th>
                  <th>{t('progress.th.rounds')}</th>
                  <th>{t('progress.th.hygiene')}</th>
                  <th>{t('progress.th.status')}</th>
                </tr>
              </thead>
              <tbody>
                {progress.hygiene_by_debate.map((d) => (
                  <tr key={d.session_id}>
                    <td className="mono">{d.session_id}…</td>
                    <td className="num">{d.rounds}</td>
                    <td className="num">{Math.round(d.hygiene * 100)}%</td>
                    <td>
                      <span className={`status-pill ${d.finished ? 'judged' : 'open'}`}>
                        {d.finished ? t('progress.judged') : t('progress.open')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}
