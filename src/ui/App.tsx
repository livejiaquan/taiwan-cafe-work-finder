import { useState, type ReactNode } from 'react'

type IconName = 'arrow' | 'bolt' | 'calendar' | 'check' | 'clock' | 'plug' | 'refresh' | 'search' | 'shield' | 'wifi' | 'x'

function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
    bolt: <path d="m13 2-9 12h7l-1 8 9-12h-7l1-8Z" />,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 11h18" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    plug: <><path d="M12 22v-6M8 2v5m8-5v5M7 7h10v3a5 5 0 0 1-10 0V7Z" /></>,
    refresh: <><path d="M20 11a8 8 0 0 0-14.9-4M4 4v4h4M4 13a8 8 0 0 0 14.9 4M20 20v-4h-4" /></>,
    search: <><circle cx="11" cy="11" r="6" /><path d="m20 20-4.2-4.2" /></>,
    shield: <path d="M12 3 4.5 6v5c0 4.7 3.2 8.4 7.5 10 4.3-1.6 7.5-5.3 7.5-10V6L12 3Z" />,
    wifi: <><path d="M2.5 8.5a14 14 0 0 1 19 0M5.5 12a9 9 0 0 1 13 0M9 15.5a4.5 4.5 0 0 1 6 0" /><path d="M12 19h.01" /></>,
    x: <path d="m7 7 10 10M17 7 7 17" />,
  }
  return <svg aria-hidden="true" className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>
}

const currentStatus = {
  updated: '2026 年 8 月 11 日',
  verified: 0,
  scope: '大台北',
}

function StateChip({ children, tone = 'olive' }: { children: ReactNode; tone?: 'olive' | 'ochre' | 'teal' }) {
  return <span className={`state-chip state-chip--${tone}`}>{children}</span>
}

function StatusCard() {
  return <section className="status-card" aria-labelledby="data-status-title">
    <div className="status-card__top">
      <div>
        <p className="eyebrow">公開資料狀態</p>
        <h2 id="data-status-title">尚無可安全推薦的店家</h2>
      </div>
      <StateChip tone="ochre">等待實地驗證</StateChip>
    </div>
    <p className="status-card__body">目前資料尚未通過分店、營業與工作條件的公開驗證門檻；我們不把舊來源或探索資料當作今日推薦。</p>
    <dl className="status-stats">
      <div><dt>可公開推薦</dt><dd>{currentStatus.verified}<span> 間</span></dd></div>
      <div><dt>資料範圍</dt><dd>{currentStatus.scope}</dd></div>
      <div><dt>最後評估</dt><dd className="status-stats__date">{currentStatus.updated}</dd></div>
    </dl>
    <a className="text-link" href="https://github.com/livejiaquan/taiwan-cafe-work-finder/blob/feat/verified-trust-slice/docs/data-publication-contract.md">閱讀驗證標準 <Icon name="arrow" size={16} /></a>
  </section>
}

function FinderControls() {
  return <section className="finder" aria-labelledby="finder-title">
    <div className="finder__heading"><div><p className="eyebrow">找到真正適合工作的地方</p><h2 id="finder-title">從證據開始，而非猜測</h2></div><StateChip>尚未啟用</StateChip></div>
    <p>店家資料通過公開門檻後，這裡會優先顯示插座、Wi‑Fi、安靜度、營業與每項條件的證據狀態。</p>
    <form className="filter-bar" aria-label="工作咖啡廳篩選（資料尚未開放）">
      <label className="search-field"><Icon name="search" /><span className="sr-only">搜尋地區或店名</span><input disabled placeholder="搜尋地區或店名" /></label>
      <button type="button" disabled><Icon name="plug" />需要插座</button>
      <button type="button" disabled><Icon name="wifi" />穩定 Wi‑Fi</button>
      <button type="button" disabled><Icon name="clock" />安靜工作</button>
      <button type="submit" className="primary-button" disabled>開始尋找 <Icon name="arrow" /></button>
    </form>
    <p className="disabled-note"><Icon name="shield" size={17} />篩選會在至少 10 間、2–3 個行政區的店家完成公開驗證後啟用。</p>
  </section>
}

function EvidenceGrid() {
  const items = [
    ['插座', '是否有、在哪裡、何時觀察到', 'plug'],
    ['Wi‑Fi', '不是「有網路」，而是有時效的條件證據', 'wifi'],
    ['安靜度', '以單人專注工作為判準，並標示觀察時間', 'clock'],
    ['營業狀態', '分店級別的近期營業佐證', 'calendar'],
  ] as const
  return <section className="evidence-section" aria-labelledby="evidence-title"><div className="section-heading"><p className="eyebrow">工作判斷的四個關鍵</p><h2 id="evidence-title">每個答案，都要看得到依據</h2><p>來源、觀察日期與新鮮度會和條件本身一起顯示。</p></div><div className="evidence-grid">{items.map(([title, detail, icon]) => <article key={title} className="evidence-card"><span className="evidence-card__icon"><Icon name={icon} /></span><h3>{title}</h3><p>{detail}</p><span className="evidence-card__status"><Icon name="check" size={15} />驗證後公開</span></article>)}</div></section>
}

function NextStep() {
  return <aside className="next-step" aria-labelledby="next-step-title"><div className="next-step__icon"><Icon name="refresh" size={24} /></div><div><p className="eyebrow">正在進行</p><h2 id="next-step-title">三間分店的私人驗證作業預檢</h2><p>先測試實地觀察、來源授權與每月更新是否能長期維持。通過後才會建立公開搜尋。</p></div><a href="https://github.com/livejiaquan/taiwan-cafe-work-finder/blob/feat/verified-trust-slice/docs/research/2026-08-11-mvp-browse-find-readiness.md" className="secondary-button">查看方法 <Icon name="arrow" size={18} /></a></aside>
}

export function App() {
  const [notice, setNotice] = useState(false)
  return <div className="page-shell">
    <a className="skip-link" href="#main-content">跳到主要內容</a>
    <header className="site-header"><a className="brand" href="#top" aria-label="台灣生活資料誌：工作咖啡廳搜尋首頁"><span className="brand-mark" aria-hidden="true"><span /></span><span><strong>台灣生活資料誌</strong><small>TAIWAN FIELD NOTES</small></span></a><p className="site-name">工作咖啡廳搜尋</p><button className="header-action" onClick={() => setNotice(true)}><Icon name="shield" size={17} />資料原則</button></header>
    {notice && <div className="toast" role="status"><Icon name="check" size={18} />不展示未通過公開門檻的候選資料。<button aria-label="關閉通知" onClick={() => setNotice(false)}><Icon name="x" size={17} /></button></div>}
    <main id="main-content">
      <section id="top" className="hero"><div className="hero__copy"><p className="hero-kicker"><span />大台北・單人專注工作</p><h1><span className="hero__title-line">今天要工作，</span><br /><span className="hero__title-line">先確認它真的適合。</span></h1><p className="hero__lede">一個以證據與新鮮度為優先的工作咖啡廳搜尋。插座、Wi‑Fi、安靜度與營業狀態，都不該只是舊印象。</p><a className="primary-button primary-button--active" href="#data-status-title">查看目前狀態 <Icon name="arrow" /></a></div><StatusCard /></section>
      <FinderControls />
      <EvidenceGrid />
      <NextStep />
    </main>
    <footer className="site-footer"><p><strong>台灣生活資料誌</strong>・工作咖啡廳搜尋</p><p>公開前不顯示候選店家，也不將來源擷取日期視為驗證日期。</p></footer>
  </div>
}
