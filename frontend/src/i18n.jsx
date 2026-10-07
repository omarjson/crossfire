/* Crossfire i18n — English + Arabic with RTL support.
   Usage: wrap the app in <LangProvider>, then const { t, lang, setLang } = useLang().
   t('key') returns the string for the active language (falls back to English). */
import { createContext, useCallback, useContext, useEffect, useState } from 'react';

const en = {
  // nav / shared
  'nav.record': 'Sparring record',
  'nav.back': 'Back',
  'brand': 'Crossfire',
  'lang.toggle': 'ع',

  // landing
  'landing.eyebrow': 'AI debate sparring gym',
  'landing.hero.l1': 'Most AI agrees',
  'landing.hero.l2': 'with you.',
  'landing.hero.tA': 'This one ',
  'landing.hero.tB': 'disagrees well.',
  'landing.hero.sub':
    'Crossfire takes the other side — argues the strongest version of the opposing case, ' +
    'calls your logical fouls like a referee, checks every claim against live evidence, ' +
    'and scores you like a judge.',
  'landing.cta.enter': 'Enter the arena',
  'landing.cta.how': 'See how it works',
  'landing.cred.1': '4 sparring personas',
  'landing.cred.2': 'Live evidence checks',
  'landing.cred.3': 'Real-time fallacy referee',
  'landing.cred.4': 'Side-switch training',
  'landing.how.title': 'How a spar works',
  'landing.how.sub': 'Three steps. No small talk.',
  'landing.step1.title': 'State your position',
  'landing.step1.desc': 'Pick a motion worth defending and choose your sparring partner and difficulty.',
  'landing.step2.title': 'Spar across rounds',
  'landing.step2.desc': 'Crossfire argues the strongest opposing case. Fouls get flagged, claims get fact-checked live.',
  'landing.step3.title': 'Get judged',
  'landing.step3.desc': 'An impartial judge scores every round and hands you a report card on your reasoning.',
  'landing.setup.title': 'Set up your debate',
  'landing.setup.sub': "Three choices, then you're in the ring.",
  'landing.s1.title': 'Your position',
  'landing.s1.hint': 'State a claim worth defending. Sharp, specific motions make the best spars.',
  'landing.s1.englishNote': 'Debates run in English — the AI spars far better in English than Arabic.',
  'landing.s1.placeholder': 'e.g. AI will replace most office jobs by 2030.',
  'landing.s1.min': 'at least 10 characters',
  'landing.s1.samples': 'Or start from a classic:',
  'landing.sample.1': 'AI will replace most office jobs by 2030.',
  'landing.sample.2': 'Social media does more harm than good.',
  'landing.sample.3': 'Universal basic income would strengthen the economy.',
  'landing.sample.4': 'Remote work makes teams less productive.',
  'landing.s2.title': 'Pick your sparring partner',
  'landing.s2.hint': 'Each persona attacks differently. Pick the weakness you want to train.',
  'landing.s3.title': 'Difficulty',
  'landing.s3.hint': 'How hard should Crossfire come at you?',
  'landing.start.busy': 'Entering the arena…',
  'landing.start.idle': 'Start the debate',

  // personas
  'persona.skeptic.name': 'The Skeptic',
  'persona.skeptic.desc': 'Demands evidence for everything. Distrusts bold claims.',
  'persona.lawyer.name': 'The Lawyer',
  'persona.lawyer.desc': 'Cross-examines. Traps contradictions, exposes weak links.',
  'persona.contrarian.name': 'The Contrarian',
  'persona.contrarian.desc': 'Attacks your premises, not your conclusions.',
  'persona.economist.name': 'The Economist',
  'persona.economist.desc': 'Everything is a trade-off. Prices costs, names losers.',

  // difficulties
  'diff.friendly.name': 'Friendly',
  'diff.friendly.hint': 'Spars playfully. Good for a first debate.',
  'diff.rigorous.name': 'Rigorous',
  'diff.rigorous.hint': 'Direct and demanding. The default workout.',
  'diff.hostile.name': 'Hostile',
  'diff.hostile.hint': 'Cross-examination. Shows no mercy.',

  // arena
  'arena.live': 'Live spar',
  'arena.headsup': 'Heads up:',
  'arena.composer.placeholder': 'Your move — make your case…',
  'arena.composer.hint': 'Ctrl/Cmd + Enter to send',
  'arena.flip': 'Flip sides',
  'arena.flip.title': 'Crossfire switches sides and argues YOUR case — better than you did',
  'arena.send.busy': 'Thinking…',
  'arena.send.idle': 'Send move',
  'arena.cached': 'Evidence checks ran on the cached corpus.',

  // feed
  'feed.foul': 'FOUL',
  'feed.fix': 'Fix:',
  'feed.you': 'You',
  'feed.score.title': 'Move score out of 10',
  'feed.sideswitch': 'SIDE SWITCH',
  'feed.sideswitch.sub': 'Crossfire argues your side — better than you did',
  'feed.gap': 'Where your case was weak:',
  'feed.hygiene.title': 'Evidence hygiene for this round',
  'feed.empty.title': 'Round one is yours',
  'feed.empty.desc':
    'Crossfire opens the debate. Make your first move below — argue your position. ' +
    'It will steelman the opposition and come back swinging.',
  'feed.round': 'Round',
  'feed.thinking': 'Crossfire is thinking…',
  'feed.hygiene.claims': 'claims',
  'feed.hygiene.verified': 'verified',
  'feed.hygiene.disputed': 'disputed',
  'feed.hygiene.unverifiable': 'unverifiable',

  // scoreboard
  'score.title': 'Scoreboard',
  'score.youLead': 'You lead',
  'score.cfLead': 'Crossfire leads',
  'score.tied': 'Dead even at',
  'score.empty': 'No rounds yet — the board fills as you spar.',
  'score.rd': 'Rd',
  'score.you': 'You',
  'score.cf': 'CF',
  'score.total': 'Total',
  'score.judging': 'Judging…',
  'score.end': 'End debate — call the judge',

  // verdict
  'verdict.kicker': 'FINAL VERDICT',
  'verdict.win.user': 'You take the debate.',
  'verdict.win.opponent': 'Crossfire takes the debate.',
  'verdict.win.draw': 'Dead heat.',
  'verdict.you': 'You',
  'verdict.cf': 'Crossfire',
  'verdict.scorecard': 'Round scorecard',
  'verdict.th.round': 'Round',
  'verdict.th.you': 'You',
  'verdict.th.cf': 'CF',
  'verdict.th.note': "Judge's note",
  'verdict.report': 'Your report card',
  'verdict.fallacyProfile': 'Fallacy profile',
  'verdict.clean': 'Clean sheet — no fouls called all debate.',
  'verdict.hygiene': 'Evidence hygiene',
  'verdict.hygiene.sub': 'of your claims verified against live sources',
  'verdict.tips': 'How to hit harder next time',
  'verdict.noTips': 'No tips — a flawless performance, apparently.',
  'verdict.rematch': 'Run it back',

  // progress
  'progress.titleA': 'Your sparring',
  'progress.titleB': 'record',
  'progress.empty.title': 'No debates yet',
  'progress.empty.desc':
    'Your record starts the moment you step into the ring. Fallacy profile, evidence hygiene, round history — all tracked here.',
  'progress.empty.cta': 'Start your first spar',
  'progress.debates': 'debates',
  'progress.rounds': 'rounds',
  'progress.flips': 'side flips',
  'progress.foulRate': 'fouls / round',
  'progress.fallacyProfile': 'Fallacy profile',
  'progress.clean': 'Clean record so far — no fouls called.',
  'progress.hygieneByDebate': 'Evidence hygiene by debate',
  'progress.none': 'No debates yet.',
  'progress.th.debate': 'Debate',
  'progress.th.rounds': 'Rounds',
  'progress.th.hygiene': 'Hygiene',
  'progress.th.status': 'Status',
  'progress.judged': 'judged',
  'progress.open': 'open',

  // errors
  'err.offline': 'Could not reach the debate engine. Check your connection and try again.',
  'err.expired': 'That debate session expired. Start a fresh one.',
  'err.rejected': 'That move was rejected — check the limits and try again.',
  'err.generic': 'Something went wrong. Try again.',
};

const ar = {
  'nav.record': 'سجل المنازلات',
  'nav.back': 'رجوع',
  'brand': 'Crossfire',
  'lang.toggle': 'EN',

  'landing.eyebrow': 'صالة تدريب المناظرات بالذكاء الاصطناعي',
  'landing.hero.l1': 'معظم الذكاء الاصطناعي',
  'landing.hero.l2': 'يتفق معك.',
  'landing.hero.tA': 'هذا ',
  'landing.hero.tB': 'يُجيد الاختلاف.',
  'landing.hero.sub':
    'يتولى Crossfire الطرف الآخر — يعرض أقوى نسخة من الحجة المعارضة، ' +
    'ويحتسب أخطاءك المنطقية كالحكم، ويفحص كل ادعاء بالأدلة المباشرة، ' +
    'ويقيّمك كالقاضي.',
  'landing.cta.enter': 'ادخل الحلبة',
  'landing.cta.how': 'شاهد كيف يعمل',
  'landing.cred.1': '٤ شخصيات للتدريب',
  'landing.cred.2': 'فحص الأدلة مباشرة',
  'landing.cred.3': 'حكم مغالطات فوري',
  'landing.cred.4': 'تدريب قلب الجهات',
  'landing.how.title': 'كيف تجري المنازلة',
  'landing.how.sub': 'ثلاث خطوات. بلا مقدمات.',
  'landing.step1.title': 'حدد موقفك',
  'landing.step1.desc': 'اختر قضية تستحق الدفاع واختر شريك التدريب ومستوى الصعوبة.',
  'landing.step2.title': 'تنازل عبر الجولات',
  'landing.step2.desc': 'يعرض Crossfire أقوى حجة معارضة. تُحتسب الأخطاء، وتُفحص الادعاءات مباشرة.',
  'landing.step3.title': 'احصل على التقييم',
  'landing.step3.desc': 'قاضٍ محايد يقيّم كل جولة ويمنحك بطاقة تقرير عن منطقك.',
  'landing.setup.title': 'جهّز مناظرتك',
  'landing.setup.sub': 'ثلاثة خيارات، ثم أنت في الحلبة.',
  'landing.s1.title': 'موقفك',
  'landing.s1.hint': 'اذكر ادعاءً يستحق الدفاع. القضايا الحادة المحددة تصنع أفضل المنازلات.',
  'landing.s1.englishNote': 'تُجرى المناظرة باللغة الإنجليزية — يتفوق الذكاء الاصطناعي في المناظرة بالإنجليزية.',
  'landing.s1.placeholder': 'مثال: سيحل الذكاء الاصطناعي محل معظم الوظائف المكتبية بحلول 2030.',
  'landing.s1.min': 'عشرة أحرف على الأقل',
  'landing.s1.samples': 'أو ابدأ من كلاسيكية:',
  'landing.sample.1': 'سيحل الذكاء الاصطناعي محل معظم الوظائف المكتبية بحلول 2030.',
  'landing.sample.2': 'وسائل التواصل الاجتماعي تضر أكثر مما تنفع.',
  'landing.sample.3': 'الدخل الأساسي الشامل سيقوي الاقتصاد.',
  'landing.sample.4': 'العمل عن بعد يجعل الفرق أقل إنتاجية.',
  'landing.s2.title': 'اختر شريك التدريب',
  'landing.s2.hint': 'كل شخصية تهاجم بأسلوب مختلف. اختر نقطة الضعف التي تريد تدريبها.',
  'landing.s3.title': 'الصعوبة',
  'landing.s3.hint': 'ما مدى قسوة Crossfire عليك؟',
  'landing.start.busy': 'دخول الحلبة…',
  'landing.start.idle': 'ابدأ المناظرة',

  'persona.skeptic.name': 'المتشكك',
  'persona.skeptic.desc': 'يطالب بالدليل على كل شيء. لا يثق بالادعاءات الجريئة.',
  'persona.lawyer.name': 'المحامي',
  'persona.lawyer.desc': 'يستجوب. ينصب الفخاخ للتناقضات ويفضح الحلقات الضعيفة.',
  'persona.contrarian.name': 'المخالف',
  'persona.contrarian.desc': 'يهاجم مقدماتك، لا نتائجك.',
  'persona.economist.name': 'الاقتصادي',
  'persona.economist.desc': 'كل شيء مقايضة. يُسعّر التكاليف ويسمّي الخاسرين.',

  'diff.friendly.name': 'ودود',
  'diff.friendly.hint': 'يتنازل بمرح. مناسب للمنازلة الأولى.',
  'diff.rigorous.name': 'صارم',
  'diff.rigorous.hint': 'مباشر ومتطلب. التدريب الافتراضي.',
  'diff.hostile.name': 'عدائي',
  'diff.hostile.hint': 'استجواب صارم. بلا رحمة.',

  'arena.live': 'منازلة مباشرة',
  'arena.headsup': 'تنبيه:',
  'arena.composer.placeholder': 'دورك — اعرض حجتك…',
  'arena.composer.hint': 'Ctrl/Cmd + Enter للإرسال',
  'arena.flip': 'اقلب الجهة',
  'arena.flip.title': 'سيتولى Crossfire الدفاع عن موقفك — أفضل منك',
  'arena.send.busy': 'يفكر…',
  'arena.send.idle': 'أرسل الدور',
  'arena.cached': 'تم إجراء فحص الأدلة على النسخة المخزنة.',

  'feed.foul': 'خطأ',
  'feed.fix': 'التصليح:',
  'feed.you': 'أنت',
  'feed.score.title': 'نتيجة الدور من 10',
  'feed.sideswitch': 'قلب الجهة',
  'feed.sideswitch.sub': 'يدافع Crossfire عن موقفك — أفضل منك',
  'feed.gap': 'حيث كان موقفك ضعيفًا:',
  'feed.hygiene.title': 'نظافة الأدلة لهذه الجولة',
  'feed.empty.title': 'الجولة الأولى لك',
  'feed.empty.desc':
    'يفتتح Crossfire المناظرة. قم بدورك الأول أدناه — دافع عن موقفك. ' +
    'سيعرض أقوى حجة معارضة ويرد بقوة.',
  'feed.round': 'جولة',
  'feed.thinking': 'Crossfire يفكر…',
  'feed.hygiene.claims': 'ادعاءات',
  'feed.hygiene.verified': 'مؤكدة',
  'feed.hygiene.disputed': 'متنازع عليها',
  'feed.hygiene.unverifiable': 'غير قابلة للتحقق',

  'score.title': 'لوحة النتائج',
  'score.youLead': 'أنت متقدم',
  'score.cfLead': 'Crossfire متقدم',
  'score.tied': 'تعادل تام عند',
  'score.empty': 'لا جولات بعد — تمتلئ اللوحة أثناء التنازل.',
  'score.rd': 'ج',
  'score.you': 'أنت',
  'score.cf': 'CF',
  'score.total': 'المجموع',
  'score.judging': 'جارٍ التحكيم…',
  'score.end': 'أنهِ المناظرة — استدعِ القاضي',

  'verdict.kicker': 'الحكم النهائي',
  'verdict.win.user': 'أنت تكسب المناظرة.',
  'verdict.win.opponent': 'يكسب Crossfire المناظرة.',
  'verdict.win.draw': 'تعادل تام.',
  'verdict.you': 'أنت',
  'verdict.cf': 'Crossfire',
  'verdict.scorecard': 'بطاقة نتائج الجولات',
  'verdict.th.round': 'الجولة',
  'verdict.th.you': 'أنت',
  'verdict.th.cf': 'CF',
  'verdict.th.note': 'ملاحظة القاضي',
  'verdict.report': 'بطاقة تقريرك',
  'verdict.fallacyProfile': 'ملف المغالطات',
  'verdict.clean': 'سجل نظيف — لم تُحتسب أخطاء طوال المناظرة.',
  'verdict.hygiene': 'نظافة الأدلة',
  'verdict.hygiene.sub': 'من ادعاءاتك تم التحقق منها بمصادر مباشرة',
  'verdict.tips': 'كيف تضرب بقوة أكبر المرة القادمة',
  'verdict.noTips': 'لا نصائح — أداء مثالي على ما يبدو.',
  'verdict.rematch': 'جولة أخرى',

  'progress.titleA': 'سجل',
  'progress.titleB': 'منازلاتك',
  'progress.empty.title': 'لا مناظرات بعد',
  'progress.empty.desc':
    'يبدأ سجلك لحظة دخولك الحلبة. ملف المغالطات ونظافة الأدلة وسجل الجولات — كلها هنا.',
  'progress.empty.cta': 'ابدأ أول منازلة',
  'progress.debates': 'مناظرات',
  'progress.rounds': 'جولات',
  'progress.flips': 'قلب الجهات',
  'progress.foulRate': 'أخطاء / جولة',
  'progress.fallacyProfile': 'ملف المغالطات',
  'progress.clean': 'سجل نظيف حتى الآن — لم تُحتسب أخطاء.',
  'progress.hygieneByDebate': 'نظافة الأدلة حسب المناظرة',
  'progress.none': 'لا مناظرات بعد.',
  'progress.th.debate': 'المناظرة',
  'progress.th.rounds': 'الجولات',
  'progress.th.hygiene': 'النظافة',
  'progress.th.status': 'الحالة',
  'progress.judged': 'محسومة',
  'progress.open': 'مفتوحة',

  'err.offline': 'تعذر الوصول إلى محرك المناظرة. تحقق من اتصالك وحاول مجددًا.',
  'err.expired': 'انتهت صلاحية جلسة المناظرة. ابدأ واحدة جديدة.',
  'err.rejected': 'تم رفض هذا الدور — تحقق من الحدود وحاول مجددًا.',
  'err.generic': 'حدث خطأ ما. حاول مجددًا.',
};

/* Fallacy type names (backend sends snake_case). */
const FALLACIES = {
  en: {
    strawman: 'strawman', ad_hominem: 'ad hominem', false_dilemma: 'false dilemma',
    appeal_to_authority: 'appeal to authority', bandwagon: 'bandwagon',
    slippery_slope: 'slippery slope', begging_the_question: 'begging the question',
    hasty_generalization: 'hasty generalization', prompt_injection: 'prompt injection',
  },
  ar: {
    strawman: 'رجل القش', ad_hominem: 'هجوم على الشخص', false_dilemma: 'معضلة زائفة',
    appeal_to_authority: 'احتكام إلى السلطة', bandwagon: 'الانسياق مع القطيع',
    slippery_slope: 'منحدر زلق', begging_the_question: 'مصادرة على المطلوب',
    hasty_generalization: 'تعميم متسرع', prompt_injection: 'حقن الأوامر',
  },
};

const STRINGS = { en, ar };
const LANG_KEY = 'crossfire-lang';

const LangContext = createContext({
  lang: 'en',
  setLang: () => {},
  t: (k) => k,
  fallacyName: (type) => type,
});

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try {
      const saved = localStorage.getItem(LANG_KEY);
      if (saved === 'ar' || saved === 'en') return saved;
      return (navigator.language || 'en').startsWith('ar') ? 'ar' : 'en';
    } catch {
      return 'en';
    }
  });

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    try {
      localStorage.setItem(LANG_KEY, lang);
    } catch {
      /* private mode */
    }
  }, [lang]);

  const setLang = useCallback((l) => {
    if (l === 'ar' || l === 'en') setLangState(l);
  }, []);

  const t = useCallback(
    (key) => STRINGS[lang][key] ?? STRINGS.en[key] ?? key,
    [lang]
  );

  const fallacyName = useCallback(
    (type) => FALLACIES[lang][type] ?? FALLACIES.en[type] ?? type.replace(/_/g, ' '),
    [lang]
  );

  return (
    <LangContext.Provider value={{ lang, setLang, t, fallacyName }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
