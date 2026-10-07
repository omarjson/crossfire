import { useLang } from '../i18n.jsx';

export default function LangToggle() {
  const { lang, setLang, t } = useLang();
  return (
    <button
      type="button"
      className="lang-toggle"
      onClick={() => setLang(lang === 'ar' ? 'en' : 'ar')}
      title={lang === 'ar' ? 'Switch to English' : 'التبديل إلى العربية'}
      aria-label={lang === 'ar' ? 'Switch to English' : 'التبديل إلى العربية'}
    >
      {t('lang.toggle')}
    </button>
  );
}
