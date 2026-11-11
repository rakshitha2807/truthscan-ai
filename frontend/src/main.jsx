import React, { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import {
  Activity, AlertCircle, ArrowRight, ArrowUpRight, Bell, Bookmark, ChevronDown, ChevronRight, CircleHelp,
  FileText, Fingerprint, Globe2, ImagePlus, Layers3, Link2, Menu, MessageSquareText,
  MoreHorizontal, Plus, Search, ShieldCheck, Sparkles, Target, Trash2, TrendingUp, X, Zap
} from 'lucide-react'
import { analyzeClaim, clearSavedAnalysisHistory, getAnalysisHistory, getEvidenceEntries, saveAnalysisHistory } from './services/api'
import './styles.css'
import './image-attachment.css'
import './analysis-states.css'
import './evidence-explorer.css'
import './analysis-history.css'
import './NeuralBackground.css'
import './app-polish.css'

const NeuralBackground = lazy(() => import('./NeuralBackground'))

const formatExperimentTime = (timestamp) => new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short'
}).format(new Date(timestamp))

function Logo() {
  return <div className="brand-mark" aria-label="TruthScan AI"><div className="brand-icon"><Fingerprint size={21}/></div><span>TruthScan<span className="brand-ai"> AI</span></span></div>
}
function Sidebar({active, setActive, open, setOpen, experimentCount}) {
  const nav = [
    { label: 'Workspace', items: [{name:'Overview', icon: Layers3}, {name:'Fact checker', icon: Target}, {name:'Analysis History', icon: Bookmark}] },
    { label: 'Discover', items: [{name:'Trending claims', icon: TrendingUp}, {name:'Evidence Explorer', icon: FileText}, {name:'Source library', icon: Globe2}] }
  ]
  return <>
    {open && <div className="mobile-scrim" onClick={()=>setOpen(false)} />}
    <aside className={`sidebar ${open?'sidebar-open':''}`} aria-label="Primary navigation">
      <div className="side-top"><Logo/><button className="icon-btn side-close" aria-label="Close navigation" onClick={()=>setOpen(false)}><X size={18}/></button></div>
      <button className="new-check" onClick={()=>{setActive('Fact checker');setOpen(false)}}><Plus size={17}/> New fact check <span>⌘ K</span></button>
      {nav.map(group=><div className="nav-group" key={group.label}><div className="nav-label">{group.label}</div>{group.items.map(item=><button key={item.name} aria-current={active===item.name?'page':undefined} onClick={()=>{setActive(item.name);setOpen(false)}} className={`nav-item ${active===item.name?'active':''}`}><item.icon size={17}/>{item.name}{item.name==='Fact checker'&&<span className="nav-dot"/>}</button>)}</div>)}
      <div className="side-bottom">
        <div className="usage-card"><div className="usage-head"><span>Experiments this session</span><span>{experimentCount}</span></div><small>Submissions recorded in this session</small></div>
        <button className="nav-item" onClick={()=>{setActive('Help center');setOpen(false)}}><CircleHelp size={17}/> Help center</button>
        <div className="profile"><div className="avatar">SN</div><div><strong>Sanjana N.</strong><small>Free workspace</small></div><MoreHorizontal size={18} className="profile-more"/></div>
      </div>
    </aside>
  </>
}
function Topbar({active, setOpen}) {
  const [notificationsOpen,setNotificationsOpen] = useState(false)
  return <header className="topbar"><div className="top-left"><button className="icon-btn menu-btn" aria-label="Open navigation" onClick={()=>setOpen(true)}><Menu size={19}/></button><span className="breadcrumb">Workspace</span><ChevronRight size={14}/><strong>{active}</strong></div><div className="top-right"><div className="system-status unavailable"><i/> Demo mode · No backend connected</div><div className="notification-wrap"><button className="icon-btn" aria-label="Notifications" aria-expanded={notificationsOpen} onClick={()=>setNotificationsOpen(open=>!open)}><Bell size={18}/><b/></button>{notificationsOpen && <div className="notification-popover" role="status"><strong>You're all caught up</strong><span>Live notifications are unavailable in demo mode.</span></div>}</div><div className="avatar avatar-small" aria-label="Signed in as Sanjana">SN</div></div></header>
}
function AnalysisFeedback({state,analysis,error,onRetry}) {
  if(state==='loading') return <div className="analysis-state is-loading" role="status" aria-live="polite"><div className="analysis-state-content"><div className="analysis-state-icon"><span className="spinner"/></div><div><strong>Preparing sample analysis…</strong><p>Demo data only. No live sources are being checked.</p></div></div></div>
  if(state==='error') return <div className="analysis-state is-error" role="alert"><div className="analysis-state-content"><div className="analysis-state-icon"><AlertCircle size={19}/></div><div><strong>Demo analysis could not be completed</strong><p>{error}</p><button className="btn-secondary" type="button" onClick={onRetry}>Try again</button></div></div></div>
  if(!analysis) return <div className="analysis-state" aria-live="polite"><div className="analysis-state-content"><div className="analysis-state-icon"><Target size={19}/></div><div><strong>Demo mode is ready</strong><p>Submit a claim or attach an image to preview sample verdict and evidence cards. Demo output is not fact-checking.</p></div></div></div>

  return <div className="result-panel demo-result" aria-label="Demo analysis result">
    <div className="demo-disclaimer"><AlertCircle size={15}/><div><strong>DEMO DATA — NOT A FACT-CHECK</strong><span>Sample verdicts rotate to preview the interface. They are not based on your claim, verified sources, or external research.</span></div></div>
    <div className="result-top"><div><div className="eyebrow">SAMPLE ANALYSIS</div><h2>Illustrative result</h2><p className="demo-claim">{analysis.claim}</p></div></div>
    <div className="verdict-layout">
      <div className="verdict-card"><div className="verdict-label">SAMPLE VERDICT</div><div className="verdict-word">{analysis.verdict}</div><div className="verdict-explain">Demo output only</div></div>
      <div className="score-card"><div className="score-label">SAMPLE CREDIBILITY <span className="help-dot" title="This score is mock data">i</span></div><div className="score-content"><div className="score-ring" style={{'--score':`${analysis.credibilityScore}%`}}><div className="score-inner"><strong>{analysis.credibilityScore}</strong><span>/100</span></div></div><div><div className="score-caption">Demo score</div><p>Not a verified assessment.</p></div></div><div className="score-scale"><span>Low</span><span>High</span></div><div className="scale-line"><i style={{left:`${analysis.credibilityScore}%`}}/></div></div>
    </div>
    <div className="summary-box"><div className="summary-icon"><Sparkles size={15}/></div><div><strong>Sample explanation</strong><p>{analysis.explanation}</p></div></div>
    <div className="sources-head"><div><h3>Example evidence</h3><p>Placeholder items for UI preview only</p></div><span className="demo-evidence"><AlertCircle size={13}/> DEMO</span></div>
    {analysis.evidence.map((item,index)=><div className="source-row" key={`${item.title}-${index}`}><span className="source-number">{String(index+1).padStart(2,'0')}</span><div className="source-main"><strong>{item.title}</strong><span>{item.summary}</span><small>{item.source}</small></div><span className="authority">SAMPLE</span></div>)}
  </div>
}
function FactChecker({onExperiment}) {
  const [claim,setClaim] = useState('')
  const [mode,setMode] = useState('Claim')
  const [image,setImage] = useState(null)
  const [imagePreview,setImagePreview] = useState('')
  const [imageError,setImageError] = useState('')
  const [analysisState,setAnalysisState] = useState('idle')
  const [analysis,setAnalysis] = useState(null)
  const [analysisError,setAnalysisError] = useState('')
  const [methodologyOpen,setMethodologyOpen] = useState(false)
  const imageInput = useRef(null)
  const resetAnalysis = () => {
    if(analysisState==='loading') return
    setAnalysis(null)
    setAnalysisState('idle')
    setAnalysisError('')
  }
  useEffect(() => {
    if(!image) {
      setImagePreview('')
      return
    }
    const previewUrl = URL.createObjectURL(image)
    setImagePreview(previewUrl)
    return () => URL.revokeObjectURL(previewUrl)
  }, [image])
  const selectImage = (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    setImageError('')
    if(!file) return
    if(!file.type.startsWith('image/')) {
      setImage(null)
      setImageError('Choose an image file to attach.')
      return
    }
    setImage(file)
    resetAnalysis()
  }
  const runCheck = async () => {
    if((!claim.trim() && !image) || analysisState==='loading') return
    const submission = {
      claim: claim.trim() || image.name,
      mode: image && !claim.trim() ? 'Image' : mode,
      image,
      submittedAt: new Date().toISOString()
    }
    setAnalysisState('loading')
    setAnalysisError('')
    try {
      const result = await analyzeClaim(submission)
      const experiment = {...submission, analysis: result}
      onExperiment(experiment)
      setAnalysis(result)
      setAnalysisState('success')
      setClaim('')
      setImage(null)
    } catch (error) {
      setAnalysisError(error instanceof Error ? error.message : 'An unexpected error occurred.')
      setAnalysisState('error')
    }
  }
  return <div className="page-content">
    <div className="page-heading"><div><div className="eyebrow">INVESTIGATE WITH CONFIDENCE</div><h1>Fact checker<span className="heading-period">.</span></h1><p>Separate what’s true from what’s trending.</p></div><div className="heading-chip"><ShieldCheck size={15}/> Evidence-first analysis</div></div>
    <div className="input-card">
      <div className="input-top"><div className="input-title"><div className="input-icon"><Search size={18}/></div><div><strong>What would you like to investigate?</strong><small>Paste a claim, headline, or URL to preview demo output.</small></div></div><div className="mode-switch">{['Claim','URL'].map(m=><button key={m} onClick={()=>{setMode(m);resetAnalysis()}} className={mode===m?'selected':''} disabled={analysisState==='loading'}>{m==='Claim'?<MessageSquareText size={13}/>:<Link2 size={13}/>} {m}</button>)}</div></div>
      <textarea aria-label={mode==='URL'?'Article or post URL':'Claim to investigate'} value={claim} onChange={e=>{setClaim(e.target.value);resetAnalysis()}} placeholder={mode==='URL'?'Paste an article or post URL...':'Type or paste a claim you want to fact-check...'} disabled={analysisState==='loading'} />
      <div className="image-attachment">
        {image ? <div className="image-preview"><img src={imagePreview} alt={`Preview of ${image.name}`} /><div className="image-details"><strong>{image.name}</strong><small>{(image.size / 1024 / 1024).toFixed(2)} MB · Attached image</small></div><button className="image-remove" type="button" aria-label="Remove attached image" disabled={analysisState==='loading'} onClick={()=>{setImage(null);setImageError('');resetAnalysis()}}><X size={15}/></button></div> : <button className="image-attach-button" type="button" disabled={analysisState==='loading'} onClick={()=>imageInput.current?.click()}><ImagePlus size={16}/><span>Attach an image</span><small>PNG, JPG, GIF, or other image formats</small></button>}
        <input ref={imageInput} className="image-file-input" type="file" accept="image/*" onChange={selectImage} aria-label="Choose an image to attach" />
        {imageError && <small className="image-error" role="alert">{imageError}</small>}
      </div>
      <div className="input-bottom"><div className="input-hint"><Sparkles size={14}/> Demo responses are examples, not fact checks.</div><button className="btn-primary run-btn" onClick={runCheck} disabled={analysisState==='loading' || (!claim.trim() && !image)}>{analysisState==='loading'?<><span className="spinner"/> Preparing demo…</>:analysisState==='error'?'Retry demo analysis':'Run demo analysis'} <ArrowRight size={15}/></button></div>
    </div>
    <div className="analysis-note"><div className="note-icon"><Zap size={16}/></div><div><strong>Demo mode</strong><span>This preview uses local sample data. It does not verify claims or consult live sources.</span>{methodologyOpen && <p className="methodology-details">Sample outcomes are rotated locally to preview the interface. A real verification workflow requires a connected service and reviewed sources.</p>}</div><button className="text-btn" type="button" aria-expanded={methodologyOpen} onClick={()=>setMethodologyOpen(open=>!open)}>Our methodology <ArrowUpRight size={14}/></button></div>
    <AnalysisFeedback state={analysisState} analysis={analysis} error={analysisError} onRetry={runCheck}/>
  </div>
}
function EvidenceExplorer() {
  const [evidence,setEvidence] = useState([])
  const [loadState,setLoadState] = useState('loading')
  const [loadError,setLoadError] = useState('')
  const [filter,setFilter] = useState('All')
  const [search,setSearch] = useState('')
  const [expanded,setExpanded] = useState({})
  const [reload,setReload] = useState(0)

  useEffect(() => {
    let active = true
    setLoadState('loading')
    getEvidenceEntries().then(entries => {
      if(!active) return
      setEvidence(entries)
      setLoadState('success')
      setLoadError('')
    }).catch(error => {
      if(!active) return
      setLoadError(error instanceof Error ? error.message : 'Unable to load demo evidence.')
      setLoadState('error')
    })
    return () => { active = false }
  },[reload])

  const query = search.trim().toLowerCase()
  const filteredEvidence = evidence.filter(item => {
    const matchesFilter = filter==='All' || item.stance===filter.toLowerCase()
    const matchesSearch = !query || [item.sourceName,item.title,item.url,item.sourceType,item.stance].some(value => value.toLowerCase().includes(query))
    return matchesFilter && matchesSearch
  })
  const filters = ['All','Supporting','Contradicting','Neutral']
  const getCount = stance => stance==='All' ? evidence.length : evidence.filter(item => item.stance===stance.toLowerCase()).length

  return <div className="page-content evidence-explorer">
    <div className="page-heading"><div><div className="eyebrow">DISCOVER THE CONTEXT</div><h1>Evidence Explorer<span className="heading-period">.</span></h1><p>Browse sources and compare sample perspectives.</p></div><div className="heading-chip"><Globe2 size={15}/> Source landscape</div></div>
    <div className="evidence-demo-notice"><AlertCircle size={16}/><div><strong>DEMO DATA — NOT VERIFIED EVIDENCE</strong><span>These sample records, dates, stance labels and credibility scores are illustrative only. Links lead to publisher websites; the listed metadata is not a real source assessment.</span></div></div>
    <div className="content-card evidence-browser">
      <div className="evidence-browser-heading"><div><h2>Sample evidence collection</h2><p>{evidence.length} demo records · Climate and public health</p></div><span className="evidence-demo-tag">DEMO DATA</span></div>
      <label className="evidence-search"><Search size={16}/><input aria-label="Search evidence" type="search" value={search} onChange={event=>setSearch(event.target.value)} placeholder="Search title, source, URL or type..." /></label>
      <div className="evidence-filters" role="group" aria-label="Filter evidence by stance">{filters.map(option=><button type="button" key={option} onClick={()=>setFilter(option)} className={`evidence-filter ${filter===option?'selected':''}`}>{option}<span>{getCount(option)}</span></button>)}</div>
      {loadState==='loading' && <div className="analysis-state is-loading" role="status"><div className="analysis-state-content"><div className="analysis-state-icon"><span className="spinner"/></div><div><strong>Loading demo evidence…</strong><p>Retrieving sample records from the local mock service.</p></div></div></div>}
      {loadState==='error' && <div className="analysis-state is-error" role="alert"><div className="analysis-state-content"><div className="analysis-state-icon"><AlertCircle size={19}/></div><div><strong>Could not load evidence</strong><p>{loadError}</p><button className="btn-secondary" type="button" onClick={()=>setReload(value=>value+1)}>Try again</button></div></div></div>}
      {loadState==='success' && !filteredEvidence.length && <div className="analysis-state evidence-empty"><div className="analysis-state-content"><div className="analysis-state-icon"><Search size={19}/></div><div><strong>No matching demo evidence</strong><p>Try another search or choose a different stance filter.</p></div></div></div>}
      {loadState==='success' && filteredEvidence.length>0 && <><div className="evidence-results-meta">Showing {filteredEvidence.length} of {evidence.length} sample records</div><div className="evidence-grid">{filteredEvidence.map(item=>{
        let safeUrl = ''
        try {
          const parsedUrl = new URL(item.url)
          if(parsedUrl.protocol==='https:') safeUrl = parsedUrl.href
        } catch {}
        const isExpanded = Boolean(expanded[item.id])
        return <article className={`evidence-card stance-${item.stance}`} key={item.id}>
          <div className="evidence-card-top"><span className="evidence-type">{item.sourceType}</span><span className={`evidence-stance ${item.stance}`}>{item.stance}</span></div>
          <div className="evidence-source"><span className="evidence-source-icon"><Globe2 size={16}/></span><div><strong>{item.sourceName}</strong><small>Demo record</small></div></div>
          <button type="button" className="evidence-card-title" aria-expanded={isExpanded} onClick={()=>setExpanded(current=>({...current,[item.id]:!current}))}>{item.title}<ChevronDown size={16}/></button>
          <div className="evidence-publication"><span>Published <time dateTime={item.publicationDate}>{new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeZone:'UTC'}).format(new Date(`${item.publicationDate}T00:00:00Z`))}</time></span><span className="evidence-date-demo">Demo date</span></div>
          <div className="evidence-credibility"><div className="evidence-credibility-heading"><span>Credibility indicator <small>(demo)</small></span><strong>{item.credibilityLabel} · {item.credibilityScore}%</strong></div><div className={`evidence-meter ${item.credibilityScore>=80?'high':'limited'}`}><i style={{width:`${Math.max(0,Math.min(100,item.credibilityScore))}%`}}/></div></div>
          {isExpanded && <p className="evidence-summary">{item.summary}</p>}
          <div className="evidence-card-footer">{safeUrl ? <a href={safeUrl} target="_blank" rel="noopener noreferrer" title={safeUrl} aria-label={`Open source URL ${safeUrl}`}><span>{safeUrl}</span><ArrowUpRight size={14}/></a> : <span className="evidence-invalid-url">{item.url || 'No valid source URL provided'}</span>}<span className="evidence-demo-tag">DEMO</span></div>
        </article>
      })}</div></>}
    </div>
  </div>
}
function AnalysisHistory({experiments,historyLoaded,historyError,onClear}) {
  const [filter,setFilter] = useState('All')
  const [search,setSearch] = useState('')
  const [selectedId,setSelectedId] = useState('')
  const records = experiments.map((experiment,index)=>({
    id:`${experiment.submittedAt}-${index}`,
    experiment
  })).reverse()
  const query = search.trim().toLowerCase()
  const filters = ['All','True','False','Misleading']
  const matchingRecords = records.filter(({experiment})=>{
    const verdict = experiment.analysis?.verdict || ''
    const matchesFilter = filter==='All' || verdict.toLowerCase()===filter.toLowerCase()
    const matchesSearch = !query || [experiment.claim,verdict,experiment.mode,experiment.analysis?.explanation,experiment.submittedAt].some(value=>String(value || '').toLowerCase().includes(query))
    return matchesFilter && matchesSearch
  })
  const getCount = option => option==='All'
    ? records.length
    : records.filter(({experiment})=>experiment.analysis?.verdict?.toLowerCase()===option.toLowerCase()).length
  const clearHistory = () => {
    if(!window.confirm('Clear all saved demo analysis history? This cannot be undone.')) return
    setSelectedId('')
    onClear()
  }
  const formatDate = timestamp => new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(new Date(timestamp))

  return <div className="page-content analysis-history">
    <div className="page-heading"><div><div className="eyebrow">YOUR LOCAL RECORDS</div><h1>Analysis History<span className="heading-period">.</span></h1><p>Review demo analyses saved in this browser.</p></div><button className="btn-secondary history-clear" type="button" onClick={clearHistory} disabled={!experiments.length && !historyError}><Trash2 size={15}/> Clear history</button></div>
    <div className="history-demo-banner"><AlertCircle size={16}/><div><strong>DEMO HISTORY — NOT VERIFIED RESULTS</strong><span>Verdicts, scores, explanations and evidence are generated sample data. They are not genuine fact checks.</span></div></div>
    {historyError && <div className="history-storage-error" role="alert"><AlertCircle size={15}/><span>{historyError} History remains available for this session where possible.</span></div>}
    <div className="content-card history-browser">
      <label className="history-search"><Search size={16}/><input aria-label="Search analysis history" type="search" value={search} onChange={event=>setSearch(event.target.value)} placeholder="Search claims, verdicts or dates..." /></label>
      <div className="history-filters" role="group" aria-label="Filter demo analyses by verdict">{filters.map(option=><button type="button" key={option} onClick={()=>setFilter(option)} className={`history-filter ${filter===option?'selected':''}`}>{option}<span>{getCount(option)}</span></button>)}</div>
      {!historyLoaded && <div className="analysis-state is-loading" role="status"><div className="analysis-state-content"><div className="analysis-state-icon"><span className="spinner"/></div><div><strong>Loading saved history…</strong><p>Reading demo records from this browser.</p></div></div></div>}
      {historyLoaded && !matchingRecords.length && <div className="analysis-state history-empty-state"><div className="analysis-state-content"><div className="analysis-state-icon"><Bookmark size={19}/></div><div><strong>{records.length ? 'No matching analyses' : 'No saved analyses yet'}</strong><p>{records.length ? 'Try another search or verdict filter.' : 'Run a demo analysis from Fact checker and it will appear here.'}</p></div></div></div>}
      {historyLoaded && matchingRecords.length>0 && <div className="history-record-list">{matchingRecords.map(({id,experiment})=>{
        const analysis = experiment.analysis || {}
        const selected = id===selectedId
        return <article className={`history-record ${selected?'is-selected':''}`} key={id}>
          <button type="button" className="history-record-button" aria-expanded={selected} onClick={()=>setSelectedId(selected?'':id)}>
            <div className="history-record-main"><span className={`history-verdict verdict-${(analysis.verdict || 'demo').toLowerCase()}`}>{analysis.verdict || 'Demo'}</span><strong>{experiment.claim}</strong><span className="history-record-date">{formatDate(experiment.submittedAt)}</span></div>
            <div className="history-record-meta"><span className="history-score-value">{analysis.credibilityScore ?? '—'}<small>/100</small></span><span className="history-demo-tag">DEMO</span><ChevronDown size={16}/></div>
          </button>
          {selected && <div className="history-detail">
            <div className="demo-disclaimer"><AlertCircle size={15}/><div><strong>DEMO DATA — NOT A FACT-CHECK</strong><span>This verdict was selected for demonstration only. It was not determined from the claim or supporting sources.</span></div></div>
            <div className="history-detail-stats"><div><small>Sample verdict</small><strong>{analysis.verdict || 'Demo'}</strong></div><div><small>Sample credibility</small><strong>{analysis.credibilityScore ?? '—'} / 100</strong></div><div><small>Submitted</small><strong>{formatDate(experiment.submittedAt)}</strong></div></div>
            <section className="history-detail-section"><h3>Sample explanation</h3><p>{analysis.explanation || 'No sample explanation is available.'}</p></section>
            <section className="history-detail-section"><h3>Example evidence</h3>{analysis.evidence?.length ? analysis.evidence.map((item,index)=><div className="history-evidence-item" key={`${item.title}-${index}`}><strong>{item.title}</strong><span>{item.source}</span><p>{item.summary}</p></div>) : <p>No sample evidence is attached to this record.</p>}</section>
            {experiment.imageName && <span className="history-attachment">Image attached: {experiment.imageName}</span>}
          </div>}
        </article>
      })}</div>}
    </div>
  </div>
}
function Overview({setActive, experiments}) {
  return <div className="page-content">
    <div className="page-heading"><div><div className="eyebrow">YOUR INTELLIGENCE HUB</div><h1>Good evening, Sanjana<span className="heading-period">.</span></h1><p>Stay curious. Stay critical. Know what’s real.</p></div><button className="btn-primary" onClick={()=>setActive('Fact checker')}><Plus size={16}/> Start an investigation</button></div>
    <div className="welcome-banner"><div className="banner-orb orb-one"/><div className="banner-orb orb-two"/><div className="banner-content"><div className="banner-kicker"><Sparkles size={14}/> THE TRUTH, WITHOUT THE NOISE</div><h2>Don't just read it.<br/><em>TruthScan it.</em></h2><p>Make sense of the information around you with AI-powered fact checking and transparent evidence.</p><button className="banner-button" onClick={()=>setActive('Fact checker')}>Verify a claim <ArrowRight size={15}/></button></div><div className="banner-art"><div className="orbit orbit-a"/><div className="orbit orbit-b"/><div className="core-shield"><Fingerprint size={57}/><i/></div><div className="float-tag tag-top"><ShieldCheck size={14}/> Evidence network</div><div className="float-tag tag-bottom"><Activity size={14}/> Intelligence hub</div></div></div>
    <div className="stats-grid"><div className="stat-card"><div className="stat-top"><span>Experiments recorded</span><div className="stat-icon purple"><Search size={17}/></div></div><strong>{experiments.length}</strong><small>Submitted in this session</small></div><div className="stat-card"><div className="stat-top"><span>Verified analyses</span><div className="stat-icon cyan"><Target size={17}/></div></div><strong>0</strong><small>No connected analysis service</small></div><div className="stat-card"><div className="stat-top"><span>Verified sources</span><div className="stat-icon green"><Globe2 size={17}/></div></div><strong>0</strong><small>Demo evidence excluded</small></div><div className="stat-card"><div className="stat-top"><span>Verified confidence</span><div className="stat-icon amber"><Activity size={17}/></div></div><strong>—</strong><small>No verified analyses yet</small></div></div>
    <div className="overview-grid"><div className="content-card"><div className="card-heading"><div><h3>Recent experiments</h3><p>Submissions and demo runs this session</p></div><button className="text-btn" onClick={()=>setActive('Analysis History')}>View history <ArrowRight size={14}/></button></div><div className="history-list">{experiments.length ? experiments.slice().reverse().map((experiment,i)=><div className="history-row" key={`${experiment.submittedAt}-${i}`}><div className="history-symbol"><FileText size={17}/></div><div className="history-copy"><strong>{experiment.claim}</strong><small>{formatExperimentTime(experiment.submittedAt)} · {experiment.mode}{experiment.image && ' · Image attached'}</small></div><span className="experiment-status">Demo only</span></div>) : <div className="history-empty">No experiments recorded yet.</div>}</div></div>
      <div className="content-card pulse-card"><div className="card-heading"><div><h3>Truth pulse</h3><p>Live claim trends</p></div></div><div className="pulse-empty"><Globe2 size={22}/><strong>No live trend data</strong><span>Connect a data source to see verified trends.</span></div></div></div>
  </div>
}
function Placeholder({active,setActive}) {
  if(active==='Evidence Explorer') return <EvidenceExplorer/>
  return <div className="page-content placeholder-page"><div className="page-heading"><div><div className="eyebrow">TRUTHSCAN WORKSPACE</div><h1>{active}<span className="heading-period">.</span></h1><p>This area is ready for the next stage of your product.</p></div></div><div className="empty-state"><div className="empty-icon"><Layers3 size={26}/></div><h2>{active} is coming into focus.</h2><p>We're building this experience as a modular frontend. Connect the backend when your team is ready.</p><button className="btn-primary" onClick={()=>setActive('Fact checker')}>Open fact checker <ArrowRight size={15}/></button></div></div>
}
function App() {
  const [active,setActive] = useState('Overview')
  const [mobileOpen,setMobileOpen] = useState(false)
  const [experiments,setExperiments] = useState([])
  const [historyLoaded,setHistoryLoaded] = useState(false)
  const [historyReady,setHistoryReady] = useState(false)
  const [historyError,setHistoryError] = useState('')
  useEffect(() => {
    try {
      setExperiments(getAnalysisHistory())
      setHistoryReady(true)
    } catch (error) {
      setHistoryError(error instanceof Error ? error.message : 'Saved demo history could not be loaded.')
    } finally {
      setHistoryLoaded(true)
    }
  },[])
  useEffect(() => {
    if(!historyReady) return
    try {
      saveAnalysisHistory(experiments)
      setHistoryError('')
    } catch (error) {
      setHistoryError(error instanceof Error ? error.message : 'Demo history could not be saved.')
    }
  },[experiments,historyReady])
  const recordExperiment = experiment => setExperiments(current => [...current, experiment])
  const clearHistory = () => {
    try {
      clearSavedAnalysisHistory()
      setExperiments([])
      setHistoryError('')
      setHistoryReady(true)
    } catch (error) {
      setHistoryError(error instanceof Error ? error.message : 'Demo history could not be cleared.')
    }
  }
  return <div className="app-shell">
    <Suspense fallback={null}><NeuralBackground/></Suspense>
    <Sidebar active={active} setActive={setActive} open={mobileOpen} setOpen={setMobileOpen} experimentCount={experiments.length}/>
    <main className="main-area" id="top">
      <Topbar active={active} setOpen={setMobileOpen}/>
      {active==='Overview'
        ? <Overview setActive={setActive} experiments={experiments}/>
        : active==='Fact checker'
          ? <FactChecker onExperiment={recordExperiment}/>
          : active==='Analysis History'
            ? <AnalysisHistory experiments={experiments} historyLoaded={historyLoaded} historyError={historyError} onClear={clearHistory}/>
            : <Placeholder active={active} setActive={setActive}/>}
      <footer className="footer"><span>© 2026 TruthScan AI</span><span><i/> Hackathon demo · Local sample data only</span><a href="#top">Back to top ↑</a></footer>
    </main>
  </div>
}
createRoot(document.getElementById('root')).render(<App/>)
