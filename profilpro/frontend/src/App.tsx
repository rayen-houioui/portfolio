import { useEffect, useMemo, useRef, useState } from "react";

type IconName =
  | "grid" | "users" | "spark" | "cluster" | "compass" | "book" | "chart"
  | "settings" | "search" | "bell" | "plus" | "upload" | "download"
  | "arrow" | "more" | "clock" | "check" | "brain" | "briefcase"
  | "graduation" | "family" | "filter" | "file" | "chevron" | "close";

const iconPaths: Record<IconName, React.ReactNode> = {
  grid: <><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></>,
  users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></>,
  spark: <><path d="m12 3-1.5 4.5L6 9l4.5 1.5L12 15l1.5-4.5L18 9l-4.5-1.5L12 3Z"/><path d="m5 15-.7 2.3L2 18l2.3.7L5 21l.7-2.3L8 18l-2.3-.7L5 15Zm14-2-.7 2.3-2.3.7 2.3.7L19 19l.7-2.3L22 16l-2.3-.7L19 13Z"/></>,
  cluster: <><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="12" cy="18" r="3"/><path d="m8.5 8 2 7M15.5 8l-2 7M9 6h6"/></>,
  compass: <><circle cx="12" cy="12" r="9"/><path d="m16 8-2.5 5.5L8 16l2.5-5.5L16 8Z"/></>,
  book: <><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/></>,
  chart: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></>,
  settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21H9.6v-.1A1.7 1.7 0 0 0 8.5 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.1 15a1.7 1.7 0 0 0-.6-1A1.7 1.7 0 0 0 2.4 13.6H2V9.6h.4A1.7 1.7 0 0 0 4.1 8.5a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 8.5 4.1a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V2h4v.4A1.7 1.7 0 0 0 15 4.1a1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 8.5a1.7 1.7 0 0 0 .6 1 1.7 1.7 0 0 0 1.1.4h.4v4h-.4A1.7 1.7 0 0 0 19.4 15Z"/></>,
  search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></>,
  plus: <path d="M12 5v14M5 12h14"/>, upload: <><path d="M12 16V4m0 0L7 9m5-5 5 5"/><path d="M4 15v5h16v-5"/></>,
  download: <><path d="M12 4v12m0 0 5-5m-5 5-5-5"/><path d="M4 19v2h16v-2"/></>,
  arrow: <path d="m9 18 6-6-6-6"/>, more: <><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>, check: <path d="m5 12 4 4L19 6"/>,
  brain: <><path d="M9.5 4A3.5 3.5 0 0 0 6 7.5V9a3 3 0 0 0-1 5.8V16a4 4 0 0 0 4 4h2V4H9.5ZM14.5 4A3.5 3.5 0 0 1 18 7.5V9a3 3 0 0 1 1 5.8V16a4 4 0 0 1-4 4h-2V4h1.5Z"/><path d="M8 10h3M13 14h3"/></>,
  briefcase: <><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V4h8v3M3 12h18M10 12v2h4v-2"/></>,
  graduation: <><path d="m2 10 10-5 10 5-10 5L2 10Z"/><path d="M6 12.5V17c3 2 9 2 12 0v-4.5M22 10v6"/></>,
  family: <><circle cx="9" cy="7" r="3"/><circle cx="17" cy="9" r="2"/><path d="M3 21v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3M15 15h2a3 3 0 0 1 3 3v3"/></>,
  filter: <path d="M3 5h18l-7 8v6l-4 2v-8L3 5Z"/>, file: <><path d="M6 2h8l5 5v15H6V2Z"/><path d="M14 2v6h5M9 13h6M9 17h6"/></>,
  chevron: <path d="m8 10 4 4 4-4"/>, close: <path d="m6 6 12 12M18 6 6 18"/>
};

function Icon({ name, size = 19 }: { name: IconName; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{iconPaths[name]}</svg>;
}

const navigation = [
  { id: "dashboard", label: "Tableau de bord", icon: "grid" },
  { id: "profiles", label: "Gestion des profils", icon: "users" },
  { id: "analysis", label: "Analyse des profils", icon: "spark" },
  { id: "segmentation", label: "Segmentation RH", icon: "cluster" },
  { id: "orientation", label: "Orientation professionnelle", icon: "compass" },
  { id: "training", label: "Formation et compétences", icon: "book" },
  { id: "education-prediction", label: "Prédiction du niveau d’éducation", icon: "graduation" },
  { id: "settings", label: "Paramètres", icon: "settings" },
] as const;

const services = [
  { icon: "chart", title: "Classification des revenus", desc: "Classification de la catégorie de revenu avec les variables compatibles.", algo: "Classification", color: "blue" },
  { icon: "clock", title: "Régression des heures de travail", desc: "Estimation du nombre d'heures travaillées par semaine.", algo: "Régression", color: "teal" },
  { icon: "graduation", title: "Orientation professionnelle — KNN", desc: "Prédiction de l'éducation uniquement si cette donnée est inconnue.", algo: "KNN", color: "violet" },
  { icon: "cluster", title: "Segmentation professionnelle", desc: "Regroupement des profils en groupes statistiquement similaires.", algo: "K-Means", color: "amber" },
  { icon: "compass", title: "Règles d'association", desc: "Associations statistiques entre formation, métier et autres variables.", algo: "Association", color: "rose" },
  { icon: "family", title: "Segmentation des profils familiaux", desc: "Situe le candidat parmi des profils familiaux types et propose des pistes d'accompagnement.", algo: "Clustering", color: "cyan" },
  { icon: "briefcase", title: "Prédiction du métier (CatBoost)", desc: "Prédit la catégorie de poste du candidat (service peu qualifié, bureau/gestion, métier technique) à partir de son profil.", algo: "Classification", color: "orange" },
] as const;

type CvMeta = { source: "ia" | "simplifiee"; provider: string; warning: string; notes: string };

type AnalysisDraft = {
  extraction?: CvMeta;
  fileName: string;
  fileSize: string;
  step: 1 | 2 | 3;
  selected: number[];
  profile: {
    formation: string;
    educationCategory: string;
    occupation: string;
    experience: string;
    skills: string;
    age: string;
    familyStatus: string;
    educationNum: string;
    maritalStatus: string;
    relationship: string;
    sex: string;
    occupationCategory: string;
    hours: string;
    capitalGain: string;
    capitalLoss: string;
    incomeHigh?: string; // segmentation professionnelle : "" (inconnu) | "0" (≤ 50K $) | "1" (> 50K $)
    workclass: string; // prédiction du métier (CatBoost)
    race: string; // prédiction du métier (CatBoost)
  };
};

const emptyAnalysisDraft: AnalysisDraft = {
  fileName: "",
  fileSize: "",
  step: 1,
  selected: [],
  profile: {
    formation: "",
    educationCategory: "À faire correspondre",
    occupation: "",
    experience: "",
    skills: "",
    age: "",
    familyStatus: "",
    educationNum: "",
    maritalStatus: "",
    relationship: "",
    sex: "",
    occupationCategory: "",
    hours: "40",
    capitalGain: "0",
    capitalLoss: "0",
    workclass: "",
    race: "",
  },
};

const FR_LABELS = {
  relationship: { Husband: "Époux", Wife: "Épouse", "Not-in-family": "Hors cercle familial", "Own-child": "Enfant au foyer", Unmarried: "Non marié(e) en foyer", "Other-relative": "Autre parent" } as Record<string, string>,
  marital: { Divorced: "Divorcé(e)", "Married-AF-spouse": "Marié(e) (conjoint militaire)", "Married-civ-spouse": "Marié(e)", "Married-spouse-absent": "Marié(e), conjoint absent", "Never-married": "Célibataire", Separated: "Séparé(e)", Widowed: "Veuf / veuve" } as Record<string, string>,
  sex: { Female: "Femme", Male: "Homme" } as Record<string, string>,
};
const INCOME_SERVICE = 0; // index de « Classification des revenus » dans `services`
const INCOME_OCCUPATIONS: [string, string][] = [
  ["Exec-managerial", "Direction / management"], ["Prof-specialty", "Profession spécialisée / intellectuelle (ingénieur, développeur, enseignant…)"],
  ["Tech-support", "Support technique"], ["Sales", "Vente / commerce"], ["Adm-clerical", "Administratif / secrétariat"],
  ["Craft-repair", "Artisanat / réparation"], ["Machine-op-inspct", "Opérateur machine / contrôle"], ["Transport-moving", "Transport / logistique"],
  ["Handlers-cleaners", "Manutention / nettoyage"], ["Protective-serv", "Sécurité / protection"], ["Farming-fishing", "Agriculture / pêche"],
  ["Other-service", "Autres services"], ["Priv-house-serv", "Services à domicile"], ["Armed-Forces", "Forces armées"],
];
const FAMILY_SERVICE = 5; // index de « Segmentation des profils familiaux » dans `services`
const PRO_SERVICE = 3; // index de « Segmentation professionnelle » (K-Means) dans `services`
const HOURS_SERVICE = 1; // index de « Régression des heures de travail » (XGBoost) dans `services`
const OCCUPATION_SERVICE = 6; // index de « Prédiction du métier (CatBoost) » dans `services`
const CONNECTED_SERVICES: number[] = [FAMILY_SERVICE, INCOME_SERVICE, PRO_SERVICE, HOURS_SERVICE, OCCUPATION_SERVICE];
// Listes du modèle CatBoost de prédiction du métier (mêmes catégories Adult que la prédiction d'éducation)
const OCCUPATION_WORKCLASSES: [string, string][] = [
  ["Private", "Secteur privé"], ["Self-emp-not-inc", "Indépendant (hors société)"], ["Self-emp-inc", "Indépendant (société)"],
  ["Federal-gov", "Fonction publique fédérale"], ["Local-gov", "Collectivité locale"], ["State-gov", "Administration d'État"],
  ["Without-pay", "Bénévole / sans rémunération"], ["Never-worked", "Jamais travaillé"],
];
const OCCUPATION_RACES: [string, string][] = [
  ["White", "Blanc"], ["Black", "Noir"], ["Asian-Pac-Islander", "Asiatique / Îles du Pacifique"],
  ["Amer-Indian-Eskimo", "Amérindien / Esquimau"], ["Other", "Autre"],
];
const EDUCATION_CATEGORIES: [string, string, string][] = [
  ["Doctorate", "Doctorat", "16"], ["Prof-school", "École professionnelle (médecine, droit…)", "15"], ["Masters", "Master / ingénieur (bac+5)", "14"],
  ["Bachelors", "Licence (bac+3)", "13"], ["Assoc-acdm", "Bac+2 général", "12"], ["Assoc-voc", "BTS / DUT / BUT (bac+2 pro)", "11"],
  ["Some-college", "Études supérieures partielles", "10"], ["HS-grad", "Baccalauréat", "9"], ["12th", "Terminale sans bac", "8"],
  ["11th", "Première", "7"], ["10th", "Seconde", "6"], ["9th", "Troisième", "5"], ["7th-8th", "5e-4e", "4"], ["5th-6th", "CM1-6e", "3"], ["1st-4th", "CP-CE2", "2"], ["Preschool", "Maternelle", "1"],
];
const EDUCATION_NUM: Record<string, string> = Object.fromEntries(EDUCATION_CATEGORIES.map(([v, , n]) => [v, n]));

const profiles = [
  ["PRF-1048", "34", "Master", "Services", "Analyste financier", "41 h"],
  ["PRF-1047", "29", "Licence", "Technologie", "Développeuse", "39 h"],
  ["PRF-1046", "46", "Baccalauréat", "Industrie", "Responsable production", "45 h"],
  ["PRF-1045", "38", "Master", "Éducation", "Consultante formation", "37 h"],
  ["PRF-1044", "52", "Doctorat", "Recherche", "Chercheur", "43 h"],
  ["PRF-1043", "26", "Licence", "Commerce", "Chargé de clientèle", "40 h"],
  ["PRF-1042", "41", "BTS / DUT", "Santé", "Coordinateur", "38 h"],
];

function Button({ children, icon, variant = "primary", onClick, disabled, type = "button" }: { children: React.ReactNode; icon?: IconName; variant?: "primary" | "secondary" | "ghost"; onClick?: () => void; disabled?: boolean; type?: "button" | "submit" }) {
  return <button className={`btn btn-${variant}`} onClick={onClick} disabled={disabled} type={type}>{icon && <Icon name={icon} size={17}/>}<span>{children}</span></button>;
}

function PageHeader({ title, subtitle, actions }: { title: string; subtitle: string; actions?: React.ReactNode }) {
  return <div className="page-heading"><div><h1>{title}</h1><p>{subtitle}</p></div>{actions && <div className="heading-actions">{actions}</div>}</div>;
}

function Badge({ children, tone = "success" }: { children: React.ReactNode; tone?: "success" | "info" | "warning" | "neutral" }) {
  return <span className={`badge badge-${tone}`}><span className="badge-dot"/>{children}</span>;
}

type Stats = { total: number; avg_hours: number; avg_age: number; high_income_pct: number;
  education: { label: string; count: number; pct: number }[]; occupations: { label: string; count: number }[] };

const fmt = (n: number) => n.toLocaleString("fr-FR");

function useStats() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    fetch("/api/stats/").then(r => r.json()).then(d => d.total ? setStats(d) : setError(d.message || "Base vide."))
      .catch(() => setError("API injoignable : lancez le serveur Django."));
  }, []);
  return { stats, error };
}

function BarChart({ data }: { data: { label: string; count: number }[] }) {
  const max = Math.max(1, ...data.map(d => d.count));
  const ticks = [1, 0.75, 0.5, 0.25, 0].map(t => fmt(Math.round(max * t)));
  return <div className="bar-chart">
    <div className="chart-y">{ticks.map((t, i) => <span key={i}>{t}</span>)}</div>
    <div className="bar-area">{data.map(d => <div className="bar-col" key={d.label} title={`${d.label} : ${fmt(d.count)}`}><div className="bar" style={{ height: `${(d.count / max) * 100}%` }}/><span>{d.label.length > 9 ? d.label.slice(0, 8) + "." : d.label}</span></div>)}</div>
  </div>;
}

function Donut({ total, data }: { total?: number; data: { label: string; pct: number }[] }) {
  const colors = ["#3b82f6", "#14b8a6", "#8b5cf6", "#cbd5e1"];
  let acc = 0;
  const stops = data.map((d, i) => { const from = acc; acc += d.pct; return `${colors[i]} ${from}% ${acc}%`; }).join(", ");
  return <div className="donut-wrap"><div className="donut" style={stops ? { background: `conic-gradient(${stops})` } : undefined}><div><strong>{total ? fmt(total) : "…"}</strong><span>profils</span></div></div><div className="legend">
    {data.map((d, i) => <div key={d.label}><span className={`legend-dot l${i + 1}`}/><span>{d.label}</span><strong>{String(d.pct).replace(".", ",")} %</strong></div>)}
  </div></div>;
}

function LineChart() {
  return <div className="line-chart"><div className="line-labels"><span>48 h</span><span>44 h</span><span>40 h</span><span>36 h</span></div><svg viewBox="0 0 620 155" preserveAspectRatio="none"><defs><linearGradient id="area" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#3B82F6" stopOpacity=".18"/><stop offset="1" stopColor="#3B82F6" stopOpacity="0"/></linearGradient></defs><path className="gridline" d="M0 15H620M0 55H620M0 95H620M0 135H620"/><path className="area" d="M0 118 C55 110 70 68 125 77 S200 105 250 72 S325 30 375 54 S455 100 500 68 S570 50 620 27 L620 150 L0 150Z"/><path className="line" d="M0 118 C55 110 70 68 125 77 S200 105 250 72 S325 30 375 54 S455 100 500 68 S570 50 620 27"/><circle cx="375" cy="54" r="5"/><circle cx="620" cy="27" r="5"/></svg><div className="line-x"><span>Jan.</span><span>Fév.</span><span>Mars</span><span>Avr.</span><span>Mai</span><span>Juin</span></div></div>;
}

function Dashboard({ navigate }: { navigate: (p: string) => void }) {
  const { stats, error } = useStats();
  return <>
    <PageHeader title="Bienvenue sur ProfilPro RH" subtitle="Transformez les données en décisions RH plus éclairées." actions={<><span className="sim-tag">Données simulées</span><Button icon="plus" onClick={() => navigate("analysis")}>Nouvelle analyse</Button></>}/>
    <div className="kpi-grid">
      {[
        ["Profils analysés", stats ? fmt(stats.total) : "…", "Base MySQL", "users", "blue"],
        ["Groupes identifiés", "6", "Stable", "cluster", "teal"],
        ["Services ML disponibles", "6", "Tous actifs", "brain", "violet"],
        ["Analyses réalisées", "1 284", "+8,2 %", "chart", "amber"],
      ].map((k) => <div className="kpi-card" key={k[0]}><div className={`kpi-icon ${k[4]}`}><Icon name={k[3] as IconName}/></div><div className="kpi-top"><span>{k[0]}</span><Icon name="more"/></div><div className="kpi-value">{k[1]}</div><div className="kpi-foot"><strong>{k[2]}</strong>{k[0] !== "Profils analysés" && <span> vs. mois dernier</span>}</div></div>)}
    </div>
    <div className="charts-grid">
      <section className="card wide"><div className="card-head"><div><h2>Répartition des profils</h2><p>8 professions les plus fréquentes (données réelles)</p></div></div>{error ? <p role="alert" style={{ padding: 22, color: "#b45309" }}>{error}</p> : <BarChart data={stats?.occupations ?? []}/>}</section>
      <section className="card"><div className="card-head"><div><h2>Niveaux d'éducation</h2><p>Sur l'ensemble des profils</p></div><button className="icon-btn"><Icon name="more"/></button></div><Donut total={stats?.total} data={stats?.education ?? []}/></section>
    </div>
    <section className="card work-card"><div className="card-head"><div><h2>Temps de travail hebdomadaire moyen</h2><p>Moyenne observée sur tous les profils</p></div><div className="metric-inline"><strong>{stats ? `${String(stats.avg_hours).replace(".", ",")} h` : "…"}</strong><span>âge moyen {stats ? String(stats.avg_age).replace(".", ",") : "…"} ans</span></div></div></section>
    <div className="section-title"><div><h2>Services intelligents</h2><p>Six modèles complémentaires pour explorer vos données RH.</p></div><button className="link-button" onClick={() => navigate("analysis")}>Voir tous les services <Icon name="arrow"/></button></div>
    <div className="service-grid">{services.map(s => <button className="service-card" onClick={() => navigate("analysis")} key={s.title}><div className={`service-icon ${s.color}`}><Icon name={s.icon as IconName}/></div><div className="service-copy"><h3>{s.title}</h3><p>{s.desc}</p><span>{s.algo}</span></div><Icon name="arrow"/></button>)}</div>
    <RecentTable/>
  </>;
}

function RecentTable() {
  const rows = [
    ["PRF-1048", "Estimation du temps de travail", "Aujourd'hui, 10:42", "Terminée"],
    ["PRF-1032", "Segmentation socioprofessionnelle", "Hier, 16:08", "Terminée"],
    ["PRF-1029", "Orientation professionnelle", "12 juin 2025", "En révision"],
    ["PRF-1017", "Analyse du niveau d'éducation", "11 juin 2025", "Terminée"],
  ];
  return <section className="card table-card"><div className="card-head"><div><h2>Analyses récentes</h2><p>Dernières activités réalisées sur la plateforme</p></div><button className="link-button">Tout afficher <Icon name="arrow"/></button></div><div className="table-scroll"><table><thead><tr><th>IDENTIFIANT</th><th>TYPE D'ANALYSE</th><th>DATE</th><th>STATUT</th><th></th></tr></thead><tbody>{rows.map((r, i) => <tr key={r[0]}><td><span className="profile-id"><span>{i + 1}</span>{r[0]}</span></td><td>{r[1]}</td><td className="muted">{r[2]}</td><td><Badge tone={r[3] === "Terminée" ? "success" : "warning"}>{r[3]}</Badge></td><td><button className="icon-btn"><Icon name="more"/></button></td></tr>)}</tbody></table></div></section>;
}

function Profiles() {
  const [modal, setModal] = useState(false);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<{ total: number; size: number; results: { id: string; age: number; education: string; workclass: string; occupation: string; hours: number }[] }>({ total: 0, size: 10, results: [] });
  const [loadError, setLoadError] = useState("");
  useEffect(() => {
    const t = setTimeout(() => {
      fetch(`/api/people/?page=${page}&size=10&q=${encodeURIComponent(query)}`).then(r => r.json()).then(d => { setData(d); setLoadError(""); })
        .catch(() => setLoadError("API injoignable : lancez le serveur Django."));
    }, 250);
    return () => clearTimeout(t);
  }, [page, query]);
  const lastPage = Math.max(1, Math.ceil(data.total / data.size));
  return <>
    <PageHeader title="Gestion des profils" subtitle="Centralisez et explorez les profils professionnels de votre organisation." actions={<><Button variant="secondary" icon="upload">Importer un CSV</Button><Button icon="plus" onClick={() => setModal(true)}>Ajouter un profil</Button></>}/>
    <section className="card table-card profiles-card"><div className="toolbar"><label className="search-field"><Icon name="search"/><input placeholder="Rechercher un identifiant, un métier..." value={query} onChange={e => { setQuery(e.target.value); setPage(1); }}/></label><div className="toolbar-right"><button className="filter-btn"><Icon name="filter"/> Niveau d'éducation <Icon name="chevron"/></button><button className="filter-btn"><Icon name="briefcase"/> Secteur <Icon name="chevron"/></button><Button variant="secondary" icon="download">Exporter</Button></div></div>
      <div className="table-scroll"><table><thead><tr>{["Identifiant", "Âge", "Niveau d'éducation", "Secteur", "Profession", "Heures / sem.", "Actions"].map(h => <th key={h}>{h.toUpperCase()}</th>)}</tr></thead><tbody>{data.results.map(r => <tr key={r.id}><td><span className="profile-id"><span>{r.id.slice(-2)}</span>{r.id}</span></td><td>{r.age} ans</td><td>{r.education}</td><td>{r.workclass}</td><td className="strong">{r.occupation}</td><td>{r.hours} h</td><td><button className="row-action">Voir le profil <Icon name="arrow" size={16}/></button></td></tr>)}</tbody></table></div>
      <div className="pagination"><span>{loadError || `Page ${page} sur ${fmt(lastPage)} · ${fmt(data.total)} profils`}</span><div><button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Précédent</button><button className="active">{page}</button><button disabled={page >= lastPage} onClick={() => setPage(p => p + 1)}>Suivant</button></div></div>
    </section>
    {modal && <div className="modal-backdrop" onMouseDown={() => setModal(false)}><div className="modal" onMouseDown={e => e.stopPropagation()}><div className="modal-head"><div><h2>Ajouter un profil</h2><p>Renseignez des données fictives à des fins d'analyse.</p></div><button className="icon-btn" onClick={() => setModal(false)}><Icon name="close"/></button></div><div className="form-grid"><label><span>Identifiant</span><input placeholder="PRF-1049"/></label><label><span>Âge</span><input type="number" placeholder="35"/></label><label><span>Niveau d'éducation</span><select><option>Sélectionner</option><option>Licence</option><option>Master</option></select></label><label><span>Secteur d'activité</span><select><option>Sélectionner</option><option>Technologie</option><option>Services</option></select></label><label className="full"><span>Profession</span><input placeholder="Ex. Analyste de données"/></label><label><span>Heures par semaine</span><input type="number" placeholder="40"/></label><label><span>Statut professionnel</span><select><option>Temps plein</option><option>Temps partiel</option></select></label></div><div className="info-note">Utilisez uniquement des données fictives. Aucune information personnelle réelle ne doit être saisie.</div><div className="modal-actions"><Button variant="ghost" onClick={() => setModal(false)}>Annuler</Button><Button onClick={() => setModal(false)}>Créer le profil</Button></div></div></div>}
  </>;
}

function Analysis({ draft, setDraft, onLaunch }: { draft: AnalysisDraft; setDraft: React.Dispatch<React.SetStateAction<AnalysisDraft>>; onLaunch: () => void }) {
  const [extracting, setExtracting] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const updateProfile = (key: keyof AnalysisDraft["profile"], value: string) => setDraft(current => ({ ...current, profile: { ...current.profile, [key]: value } }));
  const onFile = (file?: File) => {
    setError("");
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError("Format non pris en charge. Importez uniquement un fichier PDF.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("Ce fichier dépasse la taille maximale autorisée de 10 Mo.");
      return;
    }
    setFile(file);
    setDraft({ ...emptyAnalysisDraft, fileName: file.name, fileSize: `${(file.size / 1024 / 1024).toFixed(1)} Mo` });
  };
  const extract = async () => {
    if (!draft.fileName) {
      setError("Importez un CV au format PDF avant de lancer l'extraction.");
      return;
    }
    if (!file) {
      setError("Le fichier n'est plus en mémoire : réimportez le CV.");
      return;
    }
    setError("");
    setExtracting(true);
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch("/api/cv/analyze/", { method: "POST", body });
      const d = await res.json();
      if (!res.ok) throw new Error(d.error || "Erreur du serveur.");
      setDraft(current => ({
        ...current,
        step: 2,
        extraction: { source: d.source, provider: d.provider || "", warning: d.warning || "", notes: d.notes || "" },
        profile: {
          formation: d.formation || "",
          educationCategory: d.education_category || "À faire correspondre",
          occupation: d.occupation || "",
          experience: d.experience || "",
          skills: (d.skills || []).join(", "),
          age: d.age ? String(d.age) : "",
          familyStatus: "",
          educationNum: d.education_num ? String(d.education_num) : "",
          maritalStatus: d.marital_status || "",
          relationship: d.relationship || "",
          sex: d.sex || "",
          occupationCategory: "",
          hours: "40",
          capitalGain: "0",
          capitalLoss: "0",
          workclass: "",
          race: "",
        },
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de joindre le serveur.");
    } finally {
      setExtracting(false);
    }
  };
  const validateExtraction = () => {
    if (!draft.profile.formation.trim() && !draft.profile.occupation.trim()) {
      setError("Renseignez au moins la formation ou l'expérience professionnelle avant de continuer.");
      return;
    }
    // Un seul endroit de validation pour tous les champs obligatoires communs aux modèles : impossible
    // d'arriver à l'étape de sélection des services avec un profil incomplet, quel que soit le service visé ensuite.
    const age = Number(draft.profile.age), edu = Number(draft.profile.educationNum), h = Number(draft.profile.hours || 40);
    const missing: string[] = [];
    if (!(age >= 17 && age <= 90)) missing.push("âge (17 à 90)");
    if (!(edu >= 1 && edu <= 16)) missing.push("niveau d'études (1 à 16)");
    if (!draft.profile.maritalStatus) missing.push("statut marital");
    if (!draft.profile.relationship) missing.push("rôle dans la famille");
    if (!draft.profile.sex) missing.push("sexe");
    if (!draft.profile.workclass) missing.push("catégorie d'emploi");
    if (!draft.profile.race) missing.push("origine ethnique");
    if (!(h >= 1 && h <= 99)) missing.push("heures par semaine (1 à 99)");
    if (Number(draft.profile.capitalGain) < 0 || Number(draft.profile.capitalLoss) < 0) missing.push("gains/pertes en capital (0 ou plus)");
    if (missing.length) {
      setError(`Complétez les champs obligatoires avant de continuer : ${missing.join(", ")}.`);
      return;
    }
    setError("");
    setDraft(current => ({ ...current, step: 3 }));
  };
  const toggleService = (index: number) => setDraft(current => ({
    ...current,
    selected: current.selected.includes(index) ? current.selected.filter(item => item !== index) : [...current.selected, index],
  }));
  const launch = () => {
    // Le profil est déjà validé en entier à l'étape précédente (validateExtraction) : tous les champs
    // nécessaires à n'importe quel modèle sont garantis remplis ici, quel que soit le service choisi.
    if (!draft.selected.length) {
      setError("Sélectionnez au moins un service d'analyse.");
      return;
    }
    setError("");
    setLaunching(true);
    window.setTimeout(() => {
      setLaunching(false);
      onLaunch();
    }, 700);
  };
  return <>
    <PageHeader title="Analyse intelligente" subtitle="Importez un CV, validez les informations utiles puis choisissez les services à exécuter." actions={<Badge tone="success">Backend connecté</Badge>}/>
    <div className="analysis-progress">
      {["Import du CV", "Vérification", "Choix des services", "Résultats"].map((label, index) => <div className={`${draft.step >= index + 1 ? "active" : ""} ${draft.step === index + 1 ? "current" : ""}`} key={label}><span>{draft.step > index + 1 ? <Icon name="check" size={14}/> : index + 1}</span><strong>{label}</strong></div>)}
    </div>
    {error && <div className="analysis-error"><strong>Action requise</strong><span>{error}</span><button onClick={() => setError("")}><Icon name="close" size={16}/></button></div>}

    {draft.step === 1 && <section className="card cv-import-card">
      <div className="import-intro"><div className="step-number">1</div><div><h2>Importer le CV du candidat</h2><p>Le CV devient la source du profil utilisé par les services sélectionnés.</p></div></div>
      {!draft.fileName ? <label className="drop-zone">
        <input type="file" accept=".pdf,application/pdf" onChange={event => onFile(event.target.files?.[0])}/>
        <span className="upload-visual"><Icon name="upload" size={25}/></span>
        <strong>Déposez un CV PDF ici</strong>
        <span>ou cliquez pour parcourir vos fichiers</span>
        <small>PDF uniquement · 10 Mo maximum</small>
      </label> : <div className="uploaded-file">
        <div className="pdf-icon"><Icon name="file" size={22}/><span>PDF</span></div>
        <div><strong>{draft.fileName}</strong><span>{draft.fileSize} · Prêt pour l'analyse</span></div>
        <Badge tone="success">Fichier valide</Badge>
        <label className="file-action"><input type="file" accept=".pdf,application/pdf" onChange={event => onFile(event.target.files?.[0])}/>Remplacer</label>
        <button className="icon-btn danger" onClick={() => setDraft(emptyAnalysisDraft)} aria-label="Supprimer le CV"><Icon name="close"/></button>
      </div>}
      <div className="privacy-note"><Icon name="settings"/><div><strong>Traitement confidentiel à prévoir</strong><p>L'interface est prête pour un envoi sécurisé vers FastAPI. Dans ce prototype, aucun fichier n'est transmis ni réellement analysé.</p></div></div>
      <div className="import-actions"><Button icon="spark" onClick={extract}>{extracting ? "Analyse du document…" : "Analyser le CV avec l'IA"}</Button></div>
      {extracting && <div className="extracting-overlay"><div className="spinner"/><strong>Préparation de l'extraction</strong><span>Simulation de l'appel au futur endpoint FastAPI</span></div>}
    </section>}

    {draft.step === 2 && <section className="card extraction-card">
      <div className="extraction-heading"><div><span className="eyebrow">INFORMATIONS EXTRAITES</span><h2>Vérifiez le profil du candidat</h2><p>Corrigez ou complétez chaque information avant de sélectionner les modèles.</p></div><Badge tone="warning">Validation requise</Badge></div>
      {draft.extraction && <div className={draft.extraction.source === "ia" && !draft.extraction.warning ? "ai-banner" : "demo-warning"}><Icon name="spark"/><div><strong>{draft.extraction.source === "ia" ? `Informations extraites par IA (${draft.extraction.provider === "claude" ? "Claude" : "Gemini"})` : "Extraction locale simplifiée"}</strong><p>{draft.extraction.warning || "Relisez chaque champ avant de valider : l'IA peut se tromper."}{draft.extraction.notes ? ` ${draft.extraction.notes}` : ""}</p></div></div>}
      <div className="extraction-grid">
        <label><span>Formation extraite du CV</span><input value={draft.profile.formation} onChange={e => updateProfile("formation", e.target.value)} placeholder="Ex. Licence en informatique"/></label>
        <label><span>Métier ou domaine d'expérience</span><input value={draft.profile.occupation} onChange={e => updateProfile("occupation", e.target.value)} placeholder="Ex. Développement logiciel"/></label>
        <label><span>Expérience professionnelle</span><input value={draft.profile.experience} onChange={e => updateProfile("experience", e.target.value)} placeholder="Ex. 3 à 5 ans"/></label>
        <label><span>Compétences identifiées</span><input value={draft.profile.skills} onChange={e => updateProfile("skills", e.target.value)} placeholder="Séparez les compétences par une virgule"/></label>
        <label><span>Âge, si disponible</span><input value={draft.profile.age} onChange={e => updateProfile("age", e.target.value)} placeholder="Information non renseignée"/></label>
        <label><span>Situation familiale, si disponible</span><input value={draft.profile.familyStatus} onChange={e => updateProfile("familyStatus", e.target.value)} placeholder="Information non renseignée"/></label>
      </div>
      <div className="education-mapping">
        <div className="mapping-icon"><Icon name="graduation"/></div>
        <div><strong>Catégorie d'éducation utilisée par les modèles</strong><p>Déduite automatiquement du diplôme le plus élevé ; modifiable.</p></div>
        <select value={draft.profile.educationCategory} onChange={e => { updateProfile("educationCategory", e.target.value); const n = EDUCATION_NUM[e.target.value]; if (n) updateProfile("educationNum", n); }}>
          <option value="À faire correspondre">À faire correspondre</option>{EDUCATION_CATEGORIES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}<option value="Inconnue">Inconnue</option></select>
      </div>
      <div className="family-vars">
        <div><strong>Informations nécessaires aux modèles</strong><p>Ces champs servent à un ou plusieurs services d'analyse (familial, revenu, professionnel, métier, heures). Les champs marqués * sont obligatoires pour que les modèles puissent fonctionner et ne sont jamais déduits automatiquement du CV : renseignez-les même si le candidat ne les a pas communiqués dans son CV.</p></div>
        <div className="extraction-grid">
          <label><span>Âge (17 à 90) *</span><input type="number" min="17" max="90" value={draft.profile.age} onChange={e => updateProfile("age", e.target.value)} placeholder="Ex. 34"/></label>
          <label><span>Niveau d'études (1 à 16 ; 9 = bac, 13 = licence, 14 = master, 16 = doctorat) *</span><input type="number" min="1" max="16" value={draft.profile.educationNum} onChange={e => updateProfile("educationNum", e.target.value)} placeholder="Ex. 13"/></label>
          <label><span>Statut marital *</span><select value={draft.profile.maritalStatus} onChange={e => updateProfile("maritalStatus", e.target.value)}><option value="">Sélectionner</option>{marital.map(m => <option key={m} value={m}>{FR_LABELS.marital[m]}</option>)}</select></label>
          <label><span>Rôle dans la famille *</span><select value={draft.profile.relationship} onChange={e => updateProfile("relationship", e.target.value)}><option value="">Sélectionner</option>{relationships.map(r => <option key={r} value={r}>{FR_LABELS.relationship[r]}</option>)}</select></label>
          <label><span>Sexe *</span><select value={draft.profile.sex} onChange={e => updateProfile("sex", e.target.value)}><option value="">Sélectionner</option>{sexes.map(x => <option key={x} value={x}>{FR_LABELS.sex[x]}</option>)}</select></label>
          <label><span>Catégorie d'emploi *</span><select value={draft.profile.workclass} onChange={e => updateProfile("workclass", e.target.value)}><option value="">Sélectionner</option>{OCCUPATION_WORKCLASSES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
          <label><span>Origine ethnique *</span><select value={draft.profile.race} onChange={e => updateProfile("race", e.target.value)}><option value="">Sélectionner</option>{OCCUPATION_RACES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
          <label><span>Heures travaillées par semaine (1 à 99) *</span><input type="number" min="1" max="99" value={draft.profile.hours} onChange={e => updateProfile("hours", e.target.value)} placeholder="Ex. 40"/></label>
          <label><span>Gains en capital annuels ($, 0 si aucun) *</span><input type="number" min="0" value={draft.profile.capitalGain} onChange={e => updateProfile("capitalGain", e.target.value)} placeholder="0"/></label>
          <label><span>Pertes en capital annuelles ($, 0 si aucune) *</span><input type="number" min="0" value={draft.profile.capitalLoss} onChange={e => updateProfile("capitalLoss", e.target.value)} placeholder="0"/></label>
          <label><span>Métier (catégorie du modèle) — optionnel</span><select value={draft.profile.occupationCategory} onChange={e => updateProfile("occupationCategory", e.target.value)}><option value="">Automatique (d'après le métier du CV)</option>{INCOME_OCCUPATIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
          <label><span>Revenu annuel supérieur à 50 000 $ ? — optionnel</span><select value={draft.profile.incomeHigh ?? ""} onChange={e => updateProfile("incomeHigh", e.target.value)}><option value="">Non renseigné (estimation automatique)</option><option value="0">Non (50 000 $ ou moins)</option><option value="1">Oui (plus de 50 000 $)</option></select></label>
        </div>
      </div>
      <div className="knn-rule"><strong>Règle du service KNN</strong><p>La formation déclarée reste distincte de la catégorie modèle. Une éducation KNN ne sera prédite que si la formation est inconnue et si les variables requises sont disponibles. Elle ne vérifie jamais un diplôme.</p></div>
      <div className="validation-actions"><Button variant="secondary" onClick={() => setDraft(current => ({ ...current, step: 1 }))}>Retour au fichier</Button><Button icon="check" onClick={validateExtraction}>Valider les informations</Button></div>
    </section>}

    {draft.step === 3 && <>
      <div className="selection-summary card"><div className="summary-check"><Icon name="check"/></div><div><strong>Profil vérifié</strong><span>{draft.profile.formation || "Formation inconnue"} · {draft.profile.occupation || "Métier non renseigné"}</span></div><button onClick={() => setDraft(current => ({ ...current, step: 2 }))}>Modifier les informations</button></div>
      <div className="section-title compact"><div><h2>Sélectionnez un ou plusieurs services</h2><p>Chaque module recevra uniquement les variables compatibles avec son schéma d'entraînement.</p></div><Badge tone="info">{draft.selected.length} sélectionné{draft.selected.length > 1 ? "s" : ""}</Badge></div>
      <div className="analysis-services multi-select">{services.map((service, index) => {
        const selected = draft.selected.includes(index);
        const knnKnown = index === 2 && draft.profile.educationCategory !== "Inconnue" && draft.profile.educationCategory !== "À faire correspondre";
        return <article className={`analysis-service ${selected ? "selected" : ""}`} key={service.title}>
          <div className={`service-icon ${service.color}`}><Icon name={service.icon as IconName}/></div>
          <div className="analysis-card-top"><span>{service.algo}</span><span className={`checkbox ${selected ? "checked" : ""}`}>{selected && <Icon name="check" size={12}/>}</span></div>
          <h3>{service.title}</h3><p>{service.desc}</p>
          {knnKnown && <div className="service-note">Formation connue : correspondance analysée, sans prédiction KNN.</div>}
          <Button variant={selected ? "primary" : "secondary"} onClick={() => toggleService(index)}>{selected ? "Service sélectionné" : "Sélectionner"}</Button>
        </article>;
      })}</div>
      <div className="launch-bar"><div><strong>{draft.selected.length || "Aucun"} service{draft.selected.length > 1 ? "s" : ""} sélectionné{draft.selected.length > 1 ? "s" : ""}</strong><span>Les résultats s'ouvriront sur une page dédiée.</span></div><Button icon="spark" onClick={launch}>{launching ? "Préparation…" : "Lancer l'analyse"}</Button></div>
    </>}
  </>;
}

function AnalysisResults({ draft, onBack, onRestart }: { draft: AnalysisDraft; onBack: () => void; onRestart: () => void }) {
  const [incomeResult, setIncomeResult] = useState<IncomeAnalysis | null>(null);
  const downloadReport = () => {
    const inc = incomeResult ? `\n\n--- Classification des revenus ---\n${incomeResult.prediction.label_fr} — probabilité de revenu élevé : ${incomeResult.prediction.proba_high} % (confiance ${incomeResult.prediction.confidence})\n${incomeResult.prediction.summary}\n\nFacteurs : ${incomeResult.factors.map(f => `${f.label} (${f.value}) ${f.direction === "up" ? "+" : "-"}`).join(" ; ")}\n${incomeResult.comparisons.map(c => `${c.label} : ${c.rate} % de revenus élevés`).join("\n")}\n\n${incomeResult.warnings.join("\n")}` : "";
    const content = `ProfilPro RH — Rapport\nCV : ${draft.fileName}\nFormation déclarée : ${draft.profile.formation}\nCatégorie modèle : ${draft.profile.educationCategory}\nMétier : ${draft.profile.occupation}${inc}`;
    const url = URL.createObjectURL(new Blob([content], { type: "text/plain;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "rapport-profilpro-provisoire.txt";
    link.click();
    URL.revokeObjectURL(url);
  };
  return <>
    <PageHeader title="Résultats de l'analyse du candidat" subtitle="Synthèse modulaire des services sélectionnés pour ce CV." actions={<><Button variant="secondary" icon="arrow" onClick={onBack}>Retour aux services</Button><Button icon="download" onClick={downloadReport}>Télécharger le rapport</Button></>}/>
    {draft.selected.some(i => !CONNECTED_SERVICES.includes(i)) && <div className="results-status"><div><Icon name="settings"/><div><strong>Connexion aux modèles requise</strong><p>Aucune prédiction n'est générée dans ce prototype. Les modules ci-dessous sont prêts à recevoir les réponses des futurs endpoints FastAPI.</p></div></div><Badge tone="warning">Intégration en attente</Badge></div>}
    <section className="card candidate-result-summary"><div className="candidate-initials"><Icon name="file" size={24}/></div><div className="candidate-title"><span>PROFIL EXTRAIT DU CV</span><h2>{draft.fileName}</h2><p>{draft.profile.occupation || "Métier non renseigné"} · {draft.profile.experience || "Expérience non renseignée"}</p></div><div className="candidate-facts"><div><span>Formation déclarée</span><strong>{draft.profile.formation || "Inconnue"}</strong></div><div><span>Catégorie modèle validée</span><strong>{draft.profile.educationCategory}</strong></div><div><span>Compétences</span><strong>{draft.profile.skills || "Non renseignées"}</strong></div></div></section>
    <div className="result-service-chips"><span>Services sélectionnés</span>{draft.selected.map(index => <div key={services[index].title}><Icon name={services[index].icon as IconName} size={14}/>{services[index].title}</div>)}</div>
    <div className="modular-results">{draft.selected.map((index, order) => {
      const service = services[index];
      return <section className="card result-module" key={service.title}>
        <div className="module-header"><div className={`service-icon ${service.color}`}><Icon name={service.icon as IconName}/></div><div><span>ANALYSE {String(order + 1).padStart(2, "0")} · {service.algo.toUpperCase()}</span><h2>{service.title}</h2><p>{service.desc}</p></div><Badge tone={CONNECTED_SERVICES.includes(index) ? "success" : "neutral"}>{CONNECTED_SERVICES.includes(index) ? "Connecté" : "En attente"}</Badge></div>
        {index === FAMILY_SERVICE ? <FamilyClusteringModule profile={draft.profile}/> : index === PRO_SERVICE ? <ProfessionalClusteringModule profile={draft.profile}/> : index === HOURS_SERVICE ? <HoursModule profile={draft.profile}/> : index === INCOME_SERVICE ? <IncomeModule profile={draft.profile} onData={setIncomeResult} candidateName={draft.fileName}/> : index === OCCUPATION_SERVICE ? <OccupationModule profile={draft.profile}/> : <>
        {index === 2 && <div className="education-distinction"><div><span>Formation extraite du CV</span><strong>{draft.profile.formation || "Inconnue"}</strong></div><Icon name="arrow"/><div><span>Catégorie dataset validée</span><strong>{draft.profile.educationCategory}</strong></div><Icon name="arrow"/><div><span>Prédiction KNN</span><strong>{draft.profile.educationCategory === "Inconnue" ? "À connecter" : "Non requise"}</strong></div></div>}
        <div className="integration-placeholder"><div className="placeholder-chart"><span/><span/><span/><span/><span/></div><div><Icon name="brain" size={25}/><h3>Résultats en attente d'intégration</h3><p>Ce conteneur accueillera la prédiction, les indicateurs, les graphiques et l'interprétation retournés par le modèle <strong>{service.algo}</strong>.</p><code>POST /api/analyses/{index + 1}</code></div></div>
        <div className="module-footer"><span>Variables et prétraitement à valider avec le pipeline du modèle</span><button>Documentation d'intégration <Icon name="arrow" size={14}/></button></div>
        </>}
      </section>;
    })}</div>
    <div className="results-actions"><Button variant="secondary" icon="arrow" onClick={onBack}>Retour aux services</Button><Button icon="upload" onClick={onRestart}>Analyser un autre CV</Button></div>
  </>;
}

type Share = { label: string; pct: number };
type ClusterCard = { cluster: number; short: string; name: string; count: number; pct: number; age_mean: number; education_mean: number; hours_mean: number; pct_high_income: number; dominant_role: string; dominant_status: string; dominant_sex: string; composition: { relationship: Share[]; marital: Share[]; sex: Share[] }; pistes: string[] };
type FamilyAnalysis = {
  candidate: { cluster: number; profile_name: string; fiche: ClusterCard; distances: Record<string, number> };
  clusters: ClusterCard[];
  overall: { age_mean: number; education_mean: number; hours_mean: number; pct_high_income: number };
  model: { k: number; individuals: number; source: string; silhouette: number; stability_ari: number; pc1_pct: number; pc2_pct: number };
  graphs: { id: string; title: string; caption: string; image: string }[];
};

const nf = (n: number) => n.toLocaleString("fr-FR", { maximumFractionDigits: 1 });
function educationLabel(n: number) {
  if (n < 9) return "Avant le bac";
  if (n < 10) return "Niveau bac";
  if (n < 13) return "Bac à bac+2";
  if (n < 14) return "Licence (bac+3)";
  if (n < 15) return "Master (bac+5)";
  return "Doctorat / études longues";
}

function CompareRow({ label, value, group, overall, unit = "", max, display }: { label: string; value: number; group: number; overall: number; unit?: string; max: number; display?: (n: number) => string }) {
  const show = display ?? ((n: number) => `${nf(n)}${unit}`);
  const pct = (n: number) => `${Math.min(100, (n / max) * 100)}%`;
  return <div className="cmp-row">
    <div className="cmp-label"><strong>{label}</strong><span>Candidat : <b>{show(value)}</b> · Son profil : {show(group)} · Ensemble : {show(overall)}</span></div>
    <div className="cmp-bars">
      <div className="cmp-track"><span className="cmp-fill cand" style={{ width: pct(value) }}/><span className="cmp-mark group" style={{ left: pct(group) }} title="Moyenne de son profil"/><span className="cmp-mark all" style={{ left: pct(overall) }} title="Moyenne de l'ensemble"/></div>
    </div>
  </div>;
}

function ShareBars({ title, data }: { title: string; data: Share[] }) {
  return <div className="share-block"><h5>{title}</h5>{data.map(d => <div className="share-row" key={d.label}><span>{d.label}</span><div><i style={{ width: `${d.pct}%` }}/></div><b>{nf(d.pct)} %</b></div>)}</div>;
}

function FamilyClusteringModule({ profile }: { profile: AnalysisDraft["profile"] }) {
  const [data, setData] = useState<FamilyAnalysis | null>(null);
  const [error, setError] = useState("");
  const [zoom, setZoom] = useState<{ title: string; image: string } | null>(null);
  useEffect(() => {
    let cancelled = false;
    setData(null); setError("");
    fetch("/api/segmentation/analyze/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ age: Number(profile.age), education_num: Number(profile.educationNum), marital_status: profile.maritalStatus, relationship: profile.relationship, sex: profile.sex }),
    })
      .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "Erreur du serveur."); return d as FamilyAnalysis; })
      .then(d => { if (!cancelled) setData(d); })
      .catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : "Impossible de joindre le serveur."); });
    return () => { cancelled = true; };
  }, [profile.age, profile.educationNum, profile.maritalStatus, profile.relationship, profile.sex]);

  if (error) return <div className="family-state error" role="alert"><strong>L'analyse n'a pas pu être calculée</strong><p>{error}</p></div>;
  if (!data) return <div className="family-state"><div className="spinner"/><strong>Analyse en cours…</strong><p>Comparaison du candidat avec la population (quelques secondes la première fois).</p></div>;
  const { candidate, clusters, model, graphs, overall } = data;
  const f = candidate.fiche;
  const age = Number(profile.age), edu = Number(profile.educationNum);
  const plan = graphs.find(g => g.id === "plan");
  return <div className="family-results">
    <div className="family-hero">
      <div className="family-hero-badge">P{candidate.cluster + 1}</div>
      <div>
        <span>PROFIL FAMILIAL DU CANDIDAT</span>
        <h3>{candidate.profile_name}</h3>
        <p>Ce candidat ({age} ans, {FR_LABELS.relationship[profile.relationship]?.toLowerCase()}, {FR_LABELS.marital[profile.maritalStatus]?.toLowerCase()}) ressemble le plus au <strong>{f.short}</strong>, qui représente <strong>{nf(f.pct)} %</strong> des personnes analysées ({f.count.toLocaleString("fr-FR")} personnes sur {model.individuals.toLocaleString("fr-FR")}).</p>
        <div className="family-pistes"><strong>Pistes d'accompagnement suggérées</strong><ul>{f.pistes.map(p => <li key={p}>{p}</li>)}</ul><small>Indications générales à valider avec un conseiller RH.</small></div>
      </div>
    </div>

    <h4 className="family-title">Où se situe le candidat ?</h4>
    <div className="cmp-card">
      <CompareRow label="Âge" value={age} group={f.age_mean} overall={overall.age_mean} max={90} unit=" ans"/>
      <CompareRow label="Niveau d'études" value={edu} group={f.education_mean} overall={overall.education_mean} max={16} display={n => educationLabel(n)}/>
      <div className="cmp-legend"><span><i className="cand"/>Candidat</span><span><i className="group"/>Moyenne de son profil</span><span><i className="all"/>Moyenne de l'ensemble</span></div>
    </div>

    <h4 className="family-title">Les {model.k} profils identifiés dans la population</h4>
    <div className="profile-cards">{clusters.map(c => <article key={c.cluster} className={`profile-card ${c.cluster === candidate.cluster ? "mine" : ""}`}>
      <header><strong>{c.name}</strong>{c.cluster === candidate.cluster && <Badge tone="info">Ce candidat</Badge>}</header>
      <div className="profile-weight"><div><i style={{ width: `${c.pct}%` }}/></div><span>{nf(c.pct)} % de la population</span></div>
      <ul>
        <li><span>Âge moyen</span><b>{nf(c.age_mean)} ans</b></li>
        <li><span>Niveau d'études moyen</span><b>{educationLabel(c.education_mean)}</b></li>
        <li><span>Situation dominante</span><b>{c.dominant_status}</b></li>
        <li><span>Rôle dans la famille</span><b>{c.dominant_role}</b></li>
        <li><span>Genre dominant</span><b>{c.dominant_sex}</b></li>
        <li><span>Revenu élevé (&gt;50K $)</span><b>{nf(c.pct_high_income)} %</b></li>
        <li><span>Heures travaillées / semaine</span><b>{nf(c.hours_mean)} h</b></li>
      </ul>
      <footer><span>Accompagnement</span><p>{c.pistes.join(" ; ")}</p></footer>
    </article>)}</div>

    <h4 className="family-title">Qui compose le {f.short} ?</h4>
    <div className="share-grid card-soft">
      <ShareBars title="Rôle dans la famille" data={f.composition.relationship}/>
      <ShareBars title="Situation matrimoniale" data={f.composition.marital}/>
      <ShareBars title="Répartition femmes / hommes" data={f.composition.sex}/>
    </div>

    {plan && <><h4 className="family-title">Carte des profils</h4>
      <figure className="family-graph wide">
        <button type="button" onClick={() => setZoom({ title: plan.title, image: plan.image })} aria-label="Agrandir la carte des profils"><img src={plan.image} alt={plan.title}/></button>
        <figcaption><strong>{plan.title}</strong><span>{plan.caption}</span></figcaption>
      </figure></>}

    <details className="family-tech">
      <summary>Détails techniques (pour les équipes data)</summary>
      <p>Méthode : StandardScaler + One-Hot → ACP → K-Means avec k = {model.k} (choisi par silhouette). Silhouette : {model.silhouette} · Stabilité (ARI) : {model.stability_ari} · Information portée par la carte : {nf(model.pc1_pct + model.pc2_pct)} % · Données : {model.source}.</p>
    </details>
    {zoom && <div className="modal-backdrop" onMouseDown={() => setZoom(null)}><div className="modal family-zoom" onMouseDown={e => e.stopPropagation()}><div className="modal-head"><h2>{zoom.title}</h2><button className="icon-btn" onClick={() => setZoom(null)}><Icon name="close"/></button></div><img src={zoom.image} alt={zoom.title}/></div></div>}
  </div>;
}

type IncomeAnalysis = {
  prediction: { label: string; label_fr: string; proba_high: number; confidence: string; summary: string };
  occupation: { value: string; label: string; source: string };
  inputs: { age: number; education_num: number; hours_per_week: number; capital_gain: number; capital_loss: number; relationship: string; sex: string };
  factors: { feature: string; label: string; value: string; impact: number; weight_pct: number; direction: "up" | "down"; sensitive: boolean }[];
  comparisons: { label: string; rate: number; n: number }[];
  similar: { n: number; rate: number; criteria: string[] } | null;
  charts: unknown;
  levers: unknown[];
  overall: { rate: number; n: number };
  model: { name: string; iterations: number | null; depth: number | null; version: string | null; source: string; explanations: boolean };
  warnings: string[];
};

const usdFormat = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const usd = (value: number) => usdFormat.format(value);

function incomeBody(profile: AnalysisDraft["profile"]) {
  return {
    age: Number(profile.age), education_num: Number(profile.educationNum), relationship: profile.relationship, sex: profile.sex,
    hours_per_week: Number(profile.hours || 40), capital_gain: Number(profile.capitalGain || 0), capital_loss: Number(profile.capitalLoss || 0),
    occupation: profile.occupationCategory, occupation_text: profile.occupation,
  };
}

type Salary = {
  available: boolean; message: string | null; source: string; reference_date: string;
  role: { key: string; label: string; url: string } | null; roles: { key: string; label: string }[];
  level: string | null; level_label?: string; years: number | null;
  annual: { min: number; advised: number; max: number; market_p10: number; market_median: number; market_p90: number } | null;
  monthly: { min: number; advised: number; max: number } | null;
  justification: string[];
  comparison: { expected_monthly: number; position: "below" | "within" | "above"; text: string; diff_vs_advised: number; diff_pct: number | null } | null;
};

function SalaryPanel({ profile, candidateName }: { profile: AnalysisDraft["profile"]; candidateName: string }) {
  const detectedYears = profile.experience.match(/\d+/);
  const [role, setRole] = useState("");
  const [years, setYears] = useState(detectedYears ? detectedYears[0] : "");
  const [level, setLevel] = useState("auto");
  const [expected, setExpected] = useState("");
  const [sal, setSal] = useState<Salary | null>(null);
  const [salError, setSalError] = useState("");
  const [pdfBusy, setPdfBusy] = useState(false);
  const [pdfError, setPdfError] = useState("");

  const salaryInputs = () => ({
    role: role || undefined,
    occupation_text: profile.occupation,
    years: years === "" ? null : Number(years),
    level: level === "auto" ? null : level,
    expected_monthly: expected === "" ? null : Number(expected),
  });

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      fetch("/api/salary/recommend/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(salaryInputs()) })
        .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "Erreur du serveur."); return d as Salary; })
        .then(d => { if (!cancelled) { setSal(d); setSalError(""); } })
        .catch(e => { if (!cancelled) setSalError(e instanceof Error ? e.message : "Impossible de joindre le serveur."); });
    }, 200);
    return () => { cancelled = true; window.clearTimeout(timer); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role, years, level, expected, profile.occupation]);

  const downloadPdf = async () => {
    setPdfBusy(true); setPdfError("");
    try {
      const r = await fetch("/api/income/report/", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...incomeBody(profile), ...salaryInputs(), candidate_name: candidateName }),
      });
      if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.error || "Le rapport n'a pas pu être généré."); }
      const url = URL.createObjectURL(await r.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = `rapport-${(candidateName || "candidat").replace(/[^a-z0-9]+/gi, "-").toLowerCase()}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setPdfError(e instanceof Error ? e.message : "Le rapport n'a pas pu être généré.");
    } finally {
      setPdfBusy(false);
    }
  };

  const selectedRole = role || sal?.role?.key || "";
  const cmp = sal?.comparison;
  return <>
    <h4 className="family-title">Recommandation salariale (USD)</h4>
    <section className="card-soft salary-panel">
      <div className="salary-controls">
        <label><span>Métier de référence</span>
          <select value={selectedRole} onChange={e => setRole(e.target.value)}>
            <option value="">Choisir un métier</option>
            {(sal?.roles ?? []).map(r => <option key={r.key} value={r.key}>{r.label}</option>)}
          </select></label>
        <label><span>Années d'expérience</span>
          <input type="number" min={0} max={60} value={years} onChange={e => setYears(e.target.value)} placeholder="Ex. 4"/></label>
        <label><span>Niveau</span>
          <select value={level} onChange={e => setLevel(e.target.value)}>
            <option value="auto">Automatique (selon l'expérience)</option>
            <option value="junior">Junior</option>
            <option value="confirme">Confirmé</option>
            <option value="senior">Senior</option>
          </select></label>
      </div>

      {salError && <div className="family-state error" role="alert"><p>{salError}</p></div>}
      {!sal && !salError && <p className="key-empty">Calcul de la recommandation…</p>}

      {sal && !sal.available && <div className="salary-unavailable" role="status">
        <strong>Données salariales indisponibles</strong><p>{sal.message}</p>
      </div>}

      {sal?.available && sal.monthly && sal.annual && <>
        <div className="salary-kpis">
          <div><span>Fourchette mensuelle</span><strong>{usd(sal.monthly.min)} – {usd(sal.monthly.max)}</strong></div>
          <div className="advised"><span>Salaire conseillé / mois</span><strong>{usd(sal.monthly.advised)}</strong></div>
          <div><span>Estimation annuelle</span><strong>{usd(sal.annual.advised)}</strong></div>
        </div>
        <p className="salary-market">
          Niveau : <b>{sal.level_label}</b> · Marché {sal.role?.label} (annuel) : {usd(sal.annual.market_p10)} (10e) · {usd(sal.annual.market_median)} (médiane) · {usd(sal.annual.market_p90)} (90e)
        </p>
        <h5 className="salary-subtitle">Justification</h5>
        <ul className="salary-justification">{sal.justification.map(line => <li key={line}>{line}</li>)}</ul>
      </>}

      <h5 className="salary-subtitle">Comparer un salaire proposé</h5>
      <div className="salary-compare">
        <label><span>Salaire mensuel proposé (USD)</span>
          <input type="number" min={0} value={expected} onChange={e => setExpected(e.target.value)} placeholder="Ex. 6 500"/></label>
        {cmp && sal?.monthly && <div className={`salary-verdict ${cmp.position}`} role="status">
          <strong>{cmp.text}</strong>
          <span>{usd(cmp.expected_monthly)} / mois · {cmp.diff_vs_advised >= 0 ? "+" : "−"}{usd(Math.abs(cmp.diff_vs_advised))} par rapport au salaire conseillé{cmp.diff_pct !== null ? ` (${cmp.diff_pct > 0 ? "+" : ""}${cmp.diff_pct} %)` : ""}</span>
        </div>}
      </div>

      <div className="salary-footer">
        <small>Source : {sal?.source ?? "—"}, {sal?.reference_date ?? ""}. Montants en dollars américains.</small>
        <button className="pdf-button" onClick={downloadPdf} disabled={pdfBusy}>{pdfBusy ? "Génération…" : "Télécharger le rapport PDF"}</button>
      </div>
      {pdfError && <p className="salary-error" role="alert">{pdfError}</p>}
    </section>
  </>;
}

function IncomeModule({ profile, onData, candidateName }: { profile: AnalysisDraft["profile"]; onData?: (d: IncomeAnalysis | null) => void; candidateName: string }) {
  const [data, setData] = useState<IncomeAnalysis | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    setData(null); setError(""); onData?.(null);
    fetch("/api/income/analyze/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(incomeBody(profile)),
    })
      .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "Erreur du serveur."); return d as IncomeAnalysis; })
      .then(d => { if (!cancelled) { setData(d); onData?.(d); } })
      .catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : "Impossible de joindre le serveur."); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile.age, profile.educationNum, profile.relationship, profile.sex, profile.hours, profile.capitalGain, profile.capitalLoss, profile.occupationCategory, profile.occupation]);

  if (error) return <div className="family-state error" role="alert"><strong>L'analyse du candidat n'a pas pu être calculée</strong><p>{error}</p></div>;
  if (!data) return <div className="family-state"><div className="spinner"/><strong>Analyse en cours…</strong><p>Estimation du profil du candidat.</p></div>;

  const { prediction: p, factors, comparisons, similar, occupation, overall } = data;
  const high = p.label === ">50K";
  const pct = Math.round(p.proba_high);
  const uncertain = Math.abs(p.proba_high - 50) <= 10;
  const keyFactors = factors.filter(f => !f.sensitive).slice(0, 4);
  const benchmarks = [
    { label: "Population de référence", rate: overall.rate, n: overall.n },
    ...comparisons.filter(c => c.label.startsWith("Même métier")).map(c => ({ label: "Même métier", rate: c.rate, n: c.n })),
    ...(similar ? [{ label: "Profil proche", rate: similar.rate, n: similar.n }] : []),
  ];
  const confidenceTone = p.confidence === "élevée" ? "success" : p.confidence === "moyenne" ? "info" : "warning";

  return <div className="family-results income-results">
    <section className="card-soft ia-card">
      <div className="ia-head">
        <div><span className="ia-kicker">ANALYSE DU CANDIDAT</span><h3>{profile.occupation || occupation.label}</h3></div>
        <Badge tone={confidenceTone}>Fiabilité {p.confidence}</Badge>
      </div>
      <div className="ia-grid">
        <div className="ia-cell"><span>Catégorie prédite</span><strong className={high ? "cat high" : "cat std"}>{high ? ">50K" : "<=50K"}</strong></div>
        <div className="ia-cell"><span>Revenu annuel du jeu de données</span><strong>{high ? "Plus de 50 000 $" : "50 000 $ ou moins"}</strong></div>
        <div className="ia-cell"><span>Probabilité estimée</span><strong>{pct} %</strong><small>Valeur illustrative uniquement</small></div>
      </div>
      {uncertain
        ? <div className="ia-uncertain" role="status"><strong>Résultat incertain — analyse complémentaire recommandée</strong><p>Les deux catégories sont presque équiprobables pour ce profil ({pct} % de revenu élevé contre {100 - pct} %).</p></div>
        : <p className="ia-note">Le résultat est suffisamment marqué pour servir d'indication, sans valoir décision.</p>}
      {occupation.source === "inconnu" && <small className="income-hint">Métier non identifié : précisez-le via « Modifier les informations » pour affiner l'analyse.</small>}
    </section>

    <SalaryPanel profile={profile} candidateName={candidateName}/>

    <h4 className="family-title">Points clés</h4>
    {keyFactors.length ? <ul className="key-points">
      {keyFactors.map(f => <li key={f.feature} className={f.direction}>
        <strong>{f.label} : {f.value}</strong>
        <span>{f.direction === "up" ? "Joue en faveur d'un revenu élevé" : "Joue en faveur d'un revenu standard"}</span>
      </li>)}
    </ul> : <p className="key-empty">Aucun point clé disponible pour ce profil.</p>}

    <h4 className="family-title">Comparaison avec des profils similaires</h4>
    <section className="card-soft bench-chart">
      <div className="bench-legend"><span><i className="cand"/>Candidat (probabilité estimée)</span><span><i className="ref"/>Référence (taux observé)</span></div>
      {benchmarks.map(b => <div className="bench-row" key={b.label} title={`${b.n.toLocaleString("fr-FR")} personnes`}>
        <span>{b.label}<small>{b.n.toLocaleString("fr-FR")} personnes</small></span>
        <div className="bench-track">
          <i style={{ width: `${b.rate}%` }}/>
          <b style={{ left: `${p.proba_high}%` }}/>
        </div>
        <strong>{nf(b.rate)} %</strong>
      </div>)}
      <small className="benchmark-note">Part des personnes gagnant plus de 50 000 $ par an (recensement américain de 1994).</small>
    </section>

    <div className="income-warnings"><strong>À lire avant d'utiliser ce résultat</strong><ul>{data.warnings.map(w => <li key={w}>{w}</li>)}</ul></div>
  </div>;
}

// ======================= Régression des heures de travail (XGBoost : models/xgboost_hours.pkl) =======================
type HoursBar = { label: string; mean: number; n: number; mine: boolean };
type HoursAnalysis = {
  prediction: { hours: number; low: number; high: number; category: string; category_label: string; vs_population: number; reliability: string; summary: string };
  occupation: { value: string | null; label: string; source: string };
  inputs: { age: number; education_num: number; sex: string; marital_status: string; relationship: string; income: string | null };
  factors: { feature: string; label: string; value: string; impact: number; weight_pct: number; direction: "up" | "down"; sensitive: boolean }[];
  comparisons: { label: string; mean: number; n: number }[];
  similar: { n: number; mean: number; criteria: string[]; pct_40_plus: number } | null;
  charts: { distribution: { label: string; pct: number; n: number; mine: boolean }[]; education: HoursBar[]; age: HoursBar[]; occupation: HoursBar[] };
  levers: { label: string; hours: number; delta: number }[];
  overall: { mean: number; n: number };
  model: { name: string; mae: number; rmse: number; r2: number; baseline_mae: number; n_train: number; n_test: number; source: string; interval: string };
  warnings: string[];
};

const HOURS_SCALE = 80; // échelle des graphiques (heures par semaine)
const hoursPct = (h: number) => Math.min(100, Math.max(0, (h / HOURS_SCALE) * 100));
const signed = (n: number) => `${n > 0 ? "+" : ""}${nf(n)} h`;

function hoursBody(profile: AnalysisDraft["profile"]) {
  return {
    age: Number(profile.age), education_num: Number(profile.educationNum), marital_status: profile.maritalStatus,
    relationship: profile.relationship, sex: profile.sex, occupation: profile.occupationCategory, occupation_text: profile.occupation,
    income_sup50k: profile.incomeHigh === "1" ? 1 : profile.incomeHigh === "0" ? 0 : null,
  };
}

function HoursBars({ rows, hours }: { rows: { label: string; mean: number; n: number; mine?: boolean }[]; hours: number }) {
  return <>{rows.map(r => <div className={`bench-row ${r.mine ? "mine" : ""}`} key={r.label} title={`${r.n.toLocaleString("fr-FR")} personnes`}>
    <span>{r.label}<small>{r.n.toLocaleString("fr-FR")} personnes</small></span>
    <div className="bench-track"><i style={{ width: `${hoursPct(r.mean)}%` }}/><b style={{ left: `${hoursPct(hours)}%` }}/></div>
    <strong>{nf(r.mean)} h</strong>
  </div>)}</>;
}

function HoursModule({ profile }: { profile: AnalysisDraft["profile"] }) {
  const [data, setData] = useState<HoursAnalysis | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"occupation" | "education" | "age">("occupation");
  useEffect(() => {
    let cancelled = false;
    setData(null); setError("");
    fetch("/api/hours/analyze/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(hoursBody(profile)),
    })
      .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "Erreur du serveur."); return d as HoursAnalysis; })
      .then(d => { if (!cancelled) setData(d); })
      .catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : "Impossible de joindre le serveur."); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile.age, profile.educationNum, profile.maritalStatus, profile.relationship, profile.sex, profile.occupationCategory, profile.occupation, profile.incomeHigh]);

  if (error) return <div className="family-state error" role="alert"><strong>La prédiction des heures n'a pas pu être calculée</strong><p>{error}</p></div>;
  if (!data) return <div className="family-state"><div className="spinner"/><strong>Prédiction en cours…</strong><p>Le premier calcul après un démarrage peut prendre quelques secondes (entraînement du modèle).</p></div>;

  const { prediction: p, factors, comparisons, similar, charts, levers, overall, model, occupation } = data;
  const keyFactors = factors.filter(f => !f.sensitive).slice(0, 4);
  const benchmarks = [
    ...comparisons.filter(c => !c.label.startsWith("Ensemble")).map(c => ({ label: c.label, mean: c.mean, n: c.n })),
    ...(similar ? [{ label: "Profil proche", mean: similar.mean, n: similar.n }] : []),
    { label: "Ensemble de la population", mean: overall.mean, n: overall.n },
  ];
  const tabs = [["occupation", "Par métier"], ["education", "Par niveau d'études"], ["age", "Par tranche d'âge"]] as const;
  const maxPct = Math.max(...charts.distribution.map(d => d.pct), 1);

  return <div className="family-results income-results hours-results">
    <section className="card-soft ia-card">
      <div className="ia-head">
        <div><span className="ia-kicker">HEURES DE TRAVAIL PRÉDITES</span><h3>{profile.occupation || occupation.label}</h3></div>
        <Badge tone="warning">Fiabilité {p.reliability}</Badge>
      </div>
      <div className="ia-grid">
        <div className="ia-cell"><span>Heures par semaine (prédiction)</span><strong>{nf(p.hours)} h</strong><small>{p.category_label}</small></div>
        <div className="ia-cell"><span>Fourchette indicative</span><strong>{nf(p.low)} à {nf(p.high)} h</strong><small>Couvre {model.interval}</small></div>
        <div className="ia-cell"><span>Écart avec la moyenne</span><strong>{signed(p.vs_population)}</strong><small>Moyenne de la population : {nf(overall.mean)} h</small></div>
      </div>
      <div>
        <div className="bench-track hours-scale"><i style={{ left: `${hoursPct(p.low)}%`, width: `${hoursPct(p.high) - hoursPct(p.low)}%` }}/><b style={{ left: `${hoursPct(p.hours)}%` }}/></div>
        <div className="hours-ticks">{[0, 20, 40, 60, 80].map(t => <span key={t}>{t} h</span>)}</div>
      </div>
      <p className="ia-note">{p.summary}</p>
      {occupation.source === "inconnu" && <small className="income-hint">Métier non identifié : précisez-le via « Modifier les informations » pour affiner la prédiction.</small>}
    </section>

    <h4 className="family-title">Points clés</h4>
    {keyFactors.length ? <ul className="key-points">
      {keyFactors.map(f => <li key={f.feature} className={f.direction}>
        <strong>{f.label} : {f.value}</strong>
        <span>{f.direction === "up" ? "Allonge" : "Raccourcit"} la durée prédite de {nf(Math.abs(f.impact))} h par rapport à un profil moyen</span>
      </li>)}
    </ul> : <p className="key-empty">Aucun point clé disponible pour ce profil.</p>}

    <h4 className="family-title">Comparaison avec des profils similaires</h4>
    <section className="card-soft bench-chart">
      <div className="bench-legend"><span><i className="cand"/>Candidat (heures prédites)</span><span><i className="ref"/>Référence (moyenne observée)</span></div>
      <HoursBars rows={benchmarks} hours={p.hours}/>
      {similar && <small className="benchmark-note">Profils proches ({similar.criteria.join(", ")}) : {nf(similar.pct_40_plus)} % travaillent 40 h ou plus.</small>}
    </section>

    <h4 className="family-title">Répartition des horaires dans la population</h4>
    <section className="card-soft">
      <div className="hours-hist" role="img" aria-label="Répartition des heures travaillées par semaine">
        {charts.distribution.map(d => <div key={d.label} className={d.mine ? "mine" : ""} title={`${d.n.toLocaleString("fr-FR")} personnes`}>
          <small>{nf(d.pct)} %</small><i style={{ height: `${(d.pct / maxPct) * 100}%` }}/><span>{d.label}</span>
        </div>)}
      </div>
      <small className="benchmark-note">La barre rose correspond à la tranche de la prédiction ({nf(p.hours)} h). Beaucoup de personnes travaillent exactement 40 h.</small>
    </section>

    <h4 className="family-title">Heures moyennes observées</h4>
    <section className="card-soft bench-chart">
      <div className="hours-tabs" role="tablist">{tabs.map(([id, label]) => <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>{label}</button>)}</div>
      <HoursBars rows={charts[tab]} hours={p.hours}/>
      <small className="benchmark-note">Le trait rose marque les heures prédites pour ce candidat ; la ligne mise en avant est celle de son profil.</small>
    </section>

    {levers.length > 0 && <>
      <h4 className="family-title">Et si le profil changeait ?</h4>
      <ul className="key-points">
        {levers.map(l => <li key={l.label} className={l.delta > 0 ? "up" : "down"}>
          <strong>{l.label} : {nf(l.hours)} h</strong>
          <span>{signed(l.delta)} par rapport à la prédiction actuelle (simulation du modèle, pas une recommandation)</span>
        </li>)}
      </ul>
    </>}

    <h4 className="family-title">Qualité du modèle</h4>
    <section className="card-soft hours-model">
      <div className="ia-cell"><span>Erreur moyenne (MAE)</span><strong>{nf(model.mae)} h</strong><small>Référence « toujours la médiane » : {nf(model.baseline_mae)} h</small></div>
      <div className="ia-cell"><span>R²</span><strong>{model.r2.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong><small>Part de la variation des horaires expliquée</small></div>
      <div className="ia-cell"><span>Données d'entraînement</span><strong>{model.n_train.toLocaleString("fr-FR")}</strong><small>{model.name}</small></div>
    </section>

    <div className="income-warnings"><strong>À lire avant d'utiliser ce résultat</strong><ul>{data.warnings.map(w => <li key={w}>{w}</li>)}</ul></div>
  </div>;
}

// ======================= Prédiction du métier (CatBoost fourni séparément) =======================
type OccupationAnalysis = {
  prediction: { code: string; label: string; description: string; probability: number };
  probabilities: { code: string; label: string; probability: number }[];
  inputs: Record<string, unknown>;
  model: { name: string; classes: string[]; n_features: number };
  warnings: string[];
};

function occupationBody(profile: AnalysisDraft["profile"]) {
  return {
    age: Number(profile.age), education_num: Number(profile.educationNum), workclass: profile.workclass,
    marital_status: profile.maritalStatus, relationship: profile.relationship, race: profile.race, sex: profile.sex,
    hours_per_week: Number(profile.hours || 40), capital_gain: Number(profile.capitalGain || 0),
    capital_loss: Number(profile.capitalLoss || 0),
    income_high: profile.incomeHigh ? Number(profile.incomeHigh) : null,
  };
}

function OccupationModule({ profile }: { profile: AnalysisDraft["profile"] }) {
  const [data, setData] = useState<OccupationAnalysis | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    setData(null); setError("");
    fetch("/api/occupation/analyze/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(occupationBody(profile)),
    })
      .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "Erreur du serveur."); return d as OccupationAnalysis; })
      .then(d => { if (!cancelled) setData(d); })
      .catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : "Impossible de joindre le serveur."); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile.age, profile.educationNum, profile.workclass, profile.maritalStatus, profile.relationship, profile.race, profile.sex, profile.hours, profile.capitalGain, profile.capitalLoss, profile.incomeHigh]);

  if (error) return <div className="family-state error" role="alert"><strong>La prédiction n'a pas pu être calculée</strong><p>{error}</p></div>;
  if (!data) return <div className="family-state"><div className="spinner"/><strong>Prédiction en cours…</strong><p>Classification de la catégorie de poste du candidat.</p></div>;

  const { prediction: p, probabilities } = data;
  const bars: Share[] = probabilities.map(pr => ({ label: pr.label, pct: pr.probability }));
  return <div className="family-results income-results">
    <section className="card-soft ia-card">
      <div className="ia-head"><div><span className="ia-kicker">CATÉGORIE DE POSTE PRÉDITE</span><h3>{p.label}</h3></div><Badge tone="info">{nf(p.probability)} % de confiance</Badge></div>
      <p className="ia-note">{p.description}</p>
    </section>
    <h4 className="family-title">Probabilités par catégorie</h4>
    <section className="card-soft"><ShareBars title="Répartition des probabilités" data={bars}/></section>
    <div className="income-warnings"><strong>À lire avant d'utiliser ce résultat</strong><ul>{data.warnings.map(w => <li key={w}>{w}</li>)}</ul></div>
  </div>;
}

const points = [
  [12, 68, 0], [18, 58, 0], [26, 73, 0], [32, 61, 0], [20, 82, 0],
  [44, 35, 1], [52, 46, 1], [58, 27, 1], [48, 19, 1], [63, 40, 1],
  [67, 72, 2], [75, 82, 2], [83, 64, 2], [72, 58, 2], [90, 76, 2],
  [28, 31, 3], [34, 18, 3], [21, 23, 3], [38, 43, 3]
];

const marital = ["Divorced", "Married-AF-spouse", "Married-civ-spouse", "Married-spouse-absent", "Never-married", "Separated", "Widowed"];
const relationships = ["Husband", "Not-in-family", "Other-relative", "Own-child", "Unmarried", "Wife"];
const sexes = ["Female", "Male"];

type FamilyResult = { cluster: number; profile_name: string; distances: Record<string, number>; model_consistent: boolean };

// ======================= Segmentation professionnelle (K-Means : kmeans_profils_socio_economiques.pkl) =======================
type ProCard = { cluster: number; name: string; short: string; color: string; count: number; pct: number; age_mean: number; age_p10: number; age_p90: number; education_mean: number; hours_mean: number; pct_high_income: number; occupations: Share[]; pistes: string[] };
type ProModel = { k: number; individuals: number; source: string; silhouette: number; inertia: number; pc1_pct: number; pc2_pct: number; features: string[] };
type ProGraph = { id: string; title: string; caption: string; image: string };
type ProOverall = { age_mean: number; education_mean: number; hours_mean: number; pct_high_income: number };
type ProOverview = { clusters: ProCard[]; overall: ProOverall; model: ProModel; graph: ProGraph };
type ProAnalysis = ProOverview & {
  candidate: { cluster: number; profile_name: string; fiche: ProCard; color: string; inputs: { age: number; education_num: number; hours_per_week: number; income_sup50k: number; income_source: "declared" | "estimated" }; distances: Record<string, number>; second_cluster: number | null; confidence: "forte" | "moyenne" | "limite"; closeness_ratio: number };
};

function ProMap({ graph, onZoom }: { graph: ProGraph; onZoom: (z: { title: string; image: string }) => void }) {
  return <figure className="family-graph wide pro-map">
    <button type="button" onClick={() => onZoom({ title: graph.title, image: graph.image })} aria-label="Agrandir la carte des individus"><img src={graph.image} alt={graph.title}/></button>
    <figcaption><strong>{graph.title}</strong><span>{graph.caption}</span></figcaption>
  </figure>;
}

function ProZoom({ zoom, onClose }: { zoom: { title: string; image: string } | null; onClose: () => void }) {
  if (!zoom) return null;
  return <div className="modal-backdrop" onMouseDown={onClose}><div className="modal family-zoom" onMouseDown={e => e.stopPropagation()}><div className="modal-head"><h2>{zoom.title}</h2><button className="icon-btn" onClick={onClose}><Icon name="close"/></button></div><img src={zoom.image} alt={zoom.title}/></div></div>;
}

function ProfessionalClusteringModule({ profile }: { profile: AnalysisDraft["profile"] }) {
  const [data, setData] = useState<ProAnalysis | null>(null);
  const [error, setError] = useState("");
  const [zoom, setZoom] = useState<{ title: string; image: string } | null>(null);
  useEffect(() => {
    let cancelled = false;
    setData(null); setError("");
    fetch("/api/professional/analyze/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ age: Number(profile.age), education_num: Number(profile.educationNum), hours_per_week: Number(profile.hours || 40), income_sup50k: profile.incomeHigh === "1" ? 1 : profile.incomeHigh === "0" ? 0 : null }),
    })
      .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "Erreur du serveur."); return d as ProAnalysis; })
      .then(d => { if (!cancelled) setData(d); })
      .catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : "Impossible de joindre le serveur."); });
    return () => { cancelled = true; };
  }, [profile.age, profile.educationNum, profile.hours, profile.incomeHigh]);

  if (error) return <div className="family-state error" role="alert"><strong>L'analyse n'a pas pu être calculée</strong><p>{error}</p></div>;
  if (!data) return <div className="family-state"><div className="spinner"/><strong>Analyse en cours…</strong><p>Classement du candidat avec le modèle K-Means (quelques secondes la première fois).</p></div>;
  const { candidate, clusters, model, overall, graph } = data;
  const f = candidate.fiche;
  const inp = candidate.inputs;
  const second = candidate.second_cluster !== null ? clusters[candidate.second_cluster] : null;
  const confidenceText = candidate.confidence === "forte" ? "Affectation nette : le candidat est nettement plus proche de ce profil que des autres."
    : candidate.confidence === "moyenne" ? "Affectation correcte : le candidat reste plus proche de ce profil, avec un écart modéré."
    : `Profil à la frontière : le candidat est aussi proche du ${second?.short ?? "profil voisin"}. Interprétez avec prudence.`;
  return <div className="family-results pro-results">
    <div className="family-hero pro-hero" style={{ borderColor: candidate.color }}>
      <div className="family-hero-badge" style={{ background: candidate.color }}>C{candidate.cluster}</div>
      <div>
        <span>PROFIL PROFESSIONNEL DU CANDIDAT · CLUSTER {candidate.cluster}</span>
        <h3>{candidate.profile_name}</h3>
        <p>Ce candidat ({inp.age} ans, {educationLabel(inp.education_num).toLowerCase()}, {inp.hours_per_week} h par semaine) appartient au <strong>cluster {candidate.cluster}</strong> : le {f.short}, qui regroupe <strong>{nf(f.pct)} %</strong> des personnes analysées ({f.count.toLocaleString("fr-FR")} sur {model.individuals.toLocaleString("fr-FR")}).</p>
        <p className="pro-confidence"><b>Fiabilité de l'affectation : {candidate.confidence}.</b> {confidenceText}</p>
        <div className="family-pistes"><strong>Pistes d'accompagnement suggérées</strong><ul>{f.pistes.map(p => <li key={p}>{p}</li>)}</ul><small>Indications générales à valider avec un conseiller RH.</small></div>
      </div>
    </div>

    <h4 className="family-title">Caractéristiques moyennes de ce profil</h4>
    <div className="pro-stats">
      <div className="pro-stat"><span>Âge moyen</span><strong>{nf(f.age_mean)} ans</strong><small>Tranche courante : {f.age_p10}–{f.age_p90} ans</small></div>
      <div className="pro-stat"><span>Niveau d'études moyen</span><strong>{nf(f.education_mean)} / 16</strong><small>{educationLabel(f.education_mean)}</small></div>
      <div className="pro-stat"><span>Heures travaillées</span><strong>{nf(f.hours_mean)} h</strong><small>par semaine en moyenne</small></div>
      <div className="pro-stat"><span>Revenu supérieur à 50 000 $</span><strong>{nf(f.pct_high_income)} %</strong><small>des personnes du profil</small></div>
    </div>
    {f.occupations.length > 0 && <div className="share-grid card-soft pro-jobs"><ShareBars title="Métiers les plus fréquents dans ce profil" data={f.occupations}/></div>}

    <h4 className="family-title">Où se situe le candidat ?</h4>
    <div className="cmp-card">
      <CompareRow label="Âge" value={inp.age} group={f.age_mean} overall={overall.age_mean} max={90} unit=" ans"/>
      <CompareRow label="Niveau d'études" value={inp.education_num} group={f.education_mean} overall={overall.education_mean} max={16} display={n => educationLabel(n)}/>
      <CompareRow label="Heures par semaine" value={inp.hours_per_week} group={f.hours_mean} overall={overall.hours_mean} max={99} unit=" h"/>
      <div className="cmp-legend"><span><i className="cand"/>Candidat</span><span><i className="group"/>Moyenne de son profil</span><span><i className="all"/>Moyenne de l'ensemble</span></div>
    </div>
    <div className="pro-note">{inp.income_source === "declared"
      ? `Revenu pris en compte : ${inp.income_sup50k >= 0.5 ? "supérieur" : "inférieur ou égal"} à 50 000 $ par an (information saisie).`
      : `Revenu non renseigné : il a été estimé à ${nf(inp.income_sup50k * 100)} % de chances d'être supérieur à 50 000 $, d'après l'âge, les études et les heures. Renseignez-le à l'étape « Modifier les informations » pour un classement plus précis.`}</div>

    <h4 className="family-title">Les {model.k} profils identifiés dans la population</h4>
    <div className="profile-cards">{clusters.map(c => <article key={c.cluster} className={`profile-card ${c.cluster === candidate.cluster ? "mine" : ""}`} style={c.cluster === candidate.cluster ? { borderColor: c.color, boxShadow: `0 0 0 2px ${c.color}33` } : undefined}>
      <header><strong><i className="pro-dot" style={{ background: c.color }}/>Cluster {c.cluster} · {c.name}</strong>{c.cluster === candidate.cluster && <Badge tone="info">Ce candidat</Badge>}</header>
      <div className="profile-weight"><div><i style={{ width: `${c.pct}%`, background: c.color }}/></div><span>{nf(c.pct)} % de la population</span></div>
      <ul>
        <li><span>Âge moyen</span><b>{nf(c.age_mean)} ans</b></li>
        <li><span>Niveau d'études moyen</span><b>{educationLabel(c.education_mean)}</b></li>
        <li><span>Heures travaillées / semaine</span><b>{nf(c.hours_mean)} h</b></li>
        <li><span>Revenu élevé (&gt;50K $)</span><b>{nf(c.pct_high_income)} %</b></li>
        <li><span>Métier le plus fréquent</span><b>{c.occupations[0]?.label ?? "—"}</b></li>
      </ul>
    </article>)}</div>

    <h4 className="family-title">Carte des individus</h4>
    <ProMap graph={graph} onZoom={setZoom}/>

    <details className="family-tech">
      <summary>Détails techniques (pour les équipes data)</summary>
      <p>Méthode : StandardScaler + K-Means (k = {model.k}) sur {model.features.join(", ")}, modèle chargé depuis kmeans_profils_socio_economiques.pkl. Distances au centre de chaque cluster : {Object.entries(candidate.distances).map(([k, d]) => `C${k} = ${d}`).join(" · ")}. Silhouette : {model.silhouette} · Inertie : {nf(model.inertia)} · Information portée par la carte : {nf(model.pc1_pct + model.pc2_pct)} % · Données : {model.source} ({model.individuals.toLocaleString("fr-FR")} individus).</p>
    </details>
    <ProZoom zoom={zoom} onClose={() => setZoom(null)}/>
  </div>;
}

function ProfessionalOverview() {
  const [data, setData] = useState<ProOverview | null>(null);
  const [error, setError] = useState("");
  const [cluster, setCluster] = useState(0);
  const [zoom, setZoom] = useState<{ title: string; image: string } | null>(null);
  useEffect(() => {
    let cancelled = false;
    fetch("/api/professional/clusters/")
      .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error || "Erreur du serveur."); return d as ProOverview; })
      .then(d => { if (!cancelled) setData(d); })
      .catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : "Impossible de joindre le serveur."); });
    return () => { cancelled = true; };
  }, []);
  if (error) return <div className="family-state error card" role="alert"><strong>Les profils professionnels n'ont pas pu être chargés</strong><p>{error}</p></div>;
  if (!data) return <div className="family-state card"><div className="spinner"/><strong>Chargement des profils…</strong><p>Application du modèle K-Means aux données (quelques secondes la première fois).</p></div>;
  const { clusters, model, graph, overall } = data;
  const c = clusters[cluster] ?? clusters[0];
  return <>
    <div className="segment-grid">
      <section className="card scatter-card pro-overview-map">
        <div className="card-head"><div><h2>Carte des individus par profil</h2><p>Projection ACP en 2 dimensions · {model.individuals.toLocaleString("fr-FR")} personnes</p></div><Badge tone="info">{model.k} clusters</Badge></div>
        <button type="button" className="pro-map-btn" onClick={() => setZoom({ title: graph.title, image: graph.image })} aria-label="Agrandir la carte"><img src={graph.image} alt={graph.title}/></button>
        <div className="cluster-legend">{clusters.map(x => <button className={cluster === x.cluster ? "active" : ""} onClick={() => setCluster(x.cluster)} key={x.cluster}><i style={{ background: x.color }}/>Cluster {x.cluster}</button>)}</div>
      </section>
      <aside className="card cluster-detail">
        <div className="cluster-badge" style={{ background: c.color }}>C{c.cluster}</div><span>PROFIL SÉLECTIONNÉ</span><h2>{c.name}</h2>
        <p>{nf(c.pct)} % de la population analysée. Cliquez sur un cluster de la légende pour afficher sa fiche.</p>
        <div className="cluster-stats"><div><strong>{c.count.toLocaleString("fr-FR")}</strong><span>Profils</span></div><div><strong>{nf(c.age_mean)} ans</strong><span>Âge moyen</span></div><div><strong>{nf(c.hours_mean)} h</strong><span>Temps moyen</span></div></div>
        <h3>Caractéristiques dominantes</h3>
        {[{ label: "Revenu supérieur à 50 000 $", pct: c.pct_high_income }, ...c.occupations.slice(0, 3)].map(x => <div className="trait" key={x.label}><div><span>{x.label}</span><strong>{nf(x.pct)} %</strong></div><div><span style={{ width: `${Math.min(100, x.pct)}%`, background: c.color }}/></div></div>)}
        <div className="info-note">Ces groupes décrivent des corrélations, sans établir de lien causal ni de niveau de performance.</div>
      </aside>
    </div>
    <section className="card table-card"><div className="card-head"><div><h2>Comparaison des profils</h2><p>Moyennes calculées par le modèle K-Means sur les données de l'application · Ensemble : {nf(overall.age_mean)} ans, {nf(overall.hours_mean)} h / semaine, {nf(overall.pct_high_income)} % de revenus élevés</p></div></div>
      <div className="table-scroll"><table><thead><tr>{["GROUPE", "PROFILS", "ÂGE MOYEN", "NIVEAU D'ÉTUDES", "HEURES / SEM.", "REVENU > 50K $", "MÉTIER PRINCIPAL"].map(h => <th key={h}>{h}</th>)}</tr></thead>
        <tbody>{clusters.map(x => <tr key={x.cluster}><td><span className="cluster-name"><i style={{ background: x.color }}/>C{x.cluster} · {x.name}</span></td><td>{x.count.toLocaleString("fr-FR")} ({nf(x.pct)} %)</td><td>{nf(x.age_mean)} ans</td><td>{educationLabel(x.education_mean)}</td><td>{nf(x.hours_mean)} h</td><td>{nf(x.pct_high_income)} %</td><td>{x.occupations[0]?.label ?? "—"}</td></tr>)}</tbody></table></div></section>
    <ProZoom zoom={zoom} onClose={() => setZoom(null)}/>
  </>;
}

function ProfessionalQuickPanel() {
  const [form, setForm] = useState({ age: "", educationNum: "", hours: "40", incomeHigh: "" });
  const [result, setResult] = useState<ProAnalysis | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [zoom, setZoom] = useState<{ title: string; image: string } | null>(null);
  const update = (field: keyof typeof form, value: string) => setForm(current => ({ ...current, [field]: value }));
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const age = Number(form.age), edu = Number(form.educationNum), h = Number(form.hours);
    if (!(age >= 17 && age <= 90) || !(edu >= 1 && edu <= 16) || !(h >= 1 && h <= 99)) {
      setError("Renseignez l'âge (17-90), les années d'études (1-16) et les heures par semaine (1-99).");
      return;
    }
    setError(""); setResult(null); setLoading(true);
    try {
      const res = await fetch("/api/professional/analyze/", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ age, education_num: edu, hours_per_week: h, income_sup50k: form.incomeHigh === "" ? null : Number(form.incomeHigh) }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Erreur du serveur.");
      setResult(data as ProAnalysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de joindre le serveur.");
    } finally {
      setLoading(false);
    }
  };
  const f = result?.candidate.fiche;
  return <section className="card" style={{ marginBottom: 20 }}>
    <div className="card-head"><div><h2>Segmentation professionnelle</h2><p>Classez un profil avec votre modèle K-Means (kmeans_profils_socio_economiques.pkl) : âge, études, heures par semaine et revenu.</p></div></div>
    <form onSubmit={submit}>
      <div className="form-grid">
        <label><span>Âge *</span><input type="number" min="17" max="90" value={form.age} onChange={e => update("age", e.target.value)} placeholder="Ex. 34"/></label>
        <label><span>Années d’études (education-num, 1 à 16) *</span><input type="number" min="1" max="16" value={form.educationNum} onChange={e => update("educationNum", e.target.value)} placeholder="Ex. 13"/></label>
        <label><span>Heures par semaine (1 à 99) *</span><input type="number" min="1" max="99" value={form.hours} onChange={e => update("hours", e.target.value)} placeholder="Ex. 40"/></label>
        <label><span>Revenu annuel supérieur à 50 000 $ ?</span><select value={form.incomeHigh} onChange={e => update("incomeHigh", e.target.value)}><option value="">Non renseigné (estimation automatique)</option><option value="0">Non</option><option value="1">Oui</option></select></label>
      </div>
      <div style={{ padding: "0 22px 22px", display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
        <Button type="submit" icon="cluster" disabled={loading}>{loading ? "Calcul en cours..." : "Lancer la segmentation"}</Button>
        {error && <span role="alert" style={{ color: "#dc2626", fontSize: 13 }}>{error}</span>}
      </div>
    </form>
    {result && f && <div style={{ padding: "0 22px 22px" }}>
      <strong style={{ fontSize: 16 }}><i className="pro-dot" style={{ background: result.candidate.color }}/>Cluster {result.candidate.cluster} : {result.candidate.profile_name}</strong>
      <p style={{ margin: "6px 0 0", fontSize: 13, color: "#475569" }}>Moyennes de ce profil : {nf(f.age_mean)} ans · études {nf(f.education_mean)}/16 · {nf(f.hours_mean)} h/semaine · {nf(f.pct_high_income)} % de revenus &gt; 50K $ · {nf(f.pct)} % de la population.</p>
      <p style={{ margin: "6px 0 0", fontSize: 13, color: "#475569" }}>Distance aux centres : {Object.entries(result.candidate.distances).map(([k, v]) => `C${k} = ${v}`).join(" · ")} · fiabilité {result.candidate.confidence}{result.candidate.inputs.income_source === "estimated" ? " · revenu estimé" : ""}.</p>
      <ProMap graph={result.graph} onZoom={setZoom}/>
    </div>}
    <ProZoom zoom={zoom} onClose={() => setZoom(null)}/>
  </section>;
}

function FamilySegmentationPanel() {
  const [form, setForm] = useState({ age: "", educationNum: "", maritalStatus: "", relationship: "", sex: "" });
  const [result, setResult] = useState<FamilyResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const update = (field: keyof typeof form, value: string) => setForm(current => ({ ...current, [field]: value }));
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.age || !form.educationNum || !form.maritalStatus || !form.relationship || !form.sex) {
      setError("Complétez tous les champs avant de lancer la segmentation.");
      return;
    }
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const res = await fetch("/api/segmentation/predict/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ age: Number(form.age), education_num: Number(form.educationNum), marital_status: form.maritalStatus, relationship: form.relationship, sex: form.sex }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Erreur du serveur.");
      setResult(data as FamilyResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de joindre le serveur.");
    } finally {
      setLoading(false);
    }
  };
  return <section className="card" style={{ marginBottom: 20 }}>
    <div className="card-head"><div><h2>Segmentation des profils familiaux</h2><p>Classez un profil avec le modèle K-Means (ACP + K-Means) servi par le back-end Django.</p></div></div>
    <form onSubmit={submit}>
      <div className="form-grid">
        <label><span>Âge *</span><input type="number" min="17" max="90" value={form.age} onChange={e => update("age", e.target.value)} placeholder="Ex. 34"/></label>
        <label><span>Années d’études (education-num, 1 à 16) *</span><input type="number" min="1" max="16" value={form.educationNum} onChange={e => update("educationNum", e.target.value)} placeholder="Ex. 13"/></label>
        <label><span>Statut marital *</span><select value={form.maritalStatus} onChange={e => update("maritalStatus", e.target.value)}><option value="">Sélectionner</option>{marital.map(m => <option key={m}>{m}</option>)}</select></label>
        <label><span>Rôle dans la famille *</span><select value={form.relationship} onChange={e => update("relationship", e.target.value)}><option value="">Sélectionner</option>{relationships.map(r => <option key={r}>{r}</option>)}</select></label>
        <label><span>Sexe *</span><select value={form.sex} onChange={e => update("sex", e.target.value)}><option value="">Sélectionner</option>{sexes.map(x => <option key={x}>{x}</option>)}</select></label>
      </div>
      <div style={{ padding: "0 22px 22px", display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
        <Button type="submit" icon="cluster" disabled={loading}>{loading ? "Calcul en cours..." : "Lancer la segmentation"}</Button>
        {error && <span role="alert" style={{ color: "#dc2626", fontSize: 13 }}>{error}</span>}
      </div>
    </form>
    {result && <div style={{ padding: "0 22px 22px" }}>
      <strong style={{ fontSize: 16 }}>{result.profile_name}</strong>
      <p style={{ margin: "6px 0 0", fontSize: 13, color: "#475569" }}>Distance aux centres : {Object.entries(result.distances).map(([k, v]) => `C${k} = ${v}`).join(" · ")}</p>
      {!result.model_consistent && <p role="alert" style={{ margin: "8px 0 0", fontSize: 13, color: "#b45309" }}>Attention : le fichier .pkl est incohérent, ce résultat n’est pas fiable (voir le README).</p>}
    </div>}
  </section>;
}

function Segmentation() {
  return <>
    <PageHeader title="Segmentation RH" subtitle="Explorez les regroupements socioprofessionnels identifiés par K-Means." actions={<><Badge tone="success">Modèle K-Means connecté</Badge><Button variant="secondary" icon="download">Exporter la vue</Button></>}/>
    <ProfessionalQuickPanel/>
    <ProfessionalOverview/>
  </>;
}

function Orientation() {
  return <>
    <PageHeader title="Orientation professionnelle" subtitle="Explorez des trajectoires possibles à partir de règles d'association." actions={<Button variant="secondary" icon="file">Générer une synthèse</Button>}/>
    <div className="orientation-grid"><aside className="card profile-summary"><div className="summary-avatar">48</div><Badge tone="info">Profil fictif</Badge><h2>PRF-1048</h2><p>Analyste financier · Services</p><div className="summary-list"><div><span>Niveau d'éducation</span><strong>Master</strong></div><div><span>Expérience estimée</span><strong>8–12 ans</strong></div><div><span>Temps de travail</span><strong>41 h / semaine</strong></div><div><span>Cluster</span><strong>G1 · Cadres qualifiés</strong></div></div><Button variant="secondary">Changer de profil</Button></aside>
      <div className="orientation-main"><section className="card pathway"><div className="card-head"><div><h2>Carte des associations</h2><p>Liens statistiques entre formation, métiers et secteurs</p></div><span className="sim-tag">Exploration</span></div><div className="path-map"><div className="path-col"><span>FORMATION</span><button className="node education"><Icon name="graduation"/> Master économie</button><button className="node"><Icon name="book"/> Finance</button></div><div className="connections"><svg viewBox="0 0 250 220" preserveAspectRatio="none"><path d="M0 55 C100 55 150 35 250 35"/><path d="M0 55 C100 55 150 110 250 110"/><path d="M0 165 C100 165 150 110 250 110"/><path d="M0 165 C100 165 150 185 250 185"/></svg></div><div className="path-col"><span>MÉTIERS ASSOCIÉS</span><button className="node occupation"><Icon name="briefcase"/> Contrôle de gestion</button><button className="node occupation"><Icon name="chart"/> Analyste données</button><button className="node occupation"><Icon name="compass"/> Conseil financier</button></div></div></section>
        <div className="section-title compact"><div><h2>Professions à explorer</h2><p>Classées selon la force des associations observées.</p></div></div>
        <div className="recommendation-list">{[
          ["Contrôleur de gestion", "Services financiers", 82, 74, "1,8"],
          ["Analyste de données", "Technologie & conseil", 71, 68, "1,6"],
          ["Consultant financier", "Conseil", 64, 61, "1,4"]
        ].map((r, i) => <article className="recommendation" key={r[0]}><div className="rank">0{i + 1}</div><div className="rec-copy"><h3>{r[0]}</h3><p>{r[1]}</p><div className="training-tags"><span>{i === 0 ? "Pilotage budgétaire" : "Data visualisation"}</span><span>{i === 2 ? "Conseil stratégique" : "Outils BI"}</span></div></div><div className="indicators"><div><span>Support</span><strong>{r[2]} %</strong></div><div><span>Confiance</span><strong>{r[3]} %</strong></div><div><span>Lift</span><strong>{r[4]}</strong></div></div><button className="icon-btn"><Icon name="arrow"/></button></article>)}</div>
      </div>
    </div><div className="disclaimer"><Icon name="spark"/><div><strong>Recommandations exploratoires</strong><p>Ces pistes reposent sur des associations statistiques et nécessitent une validation humaine. Elles ne constituent ni une promesse d'évolution, ni une décision RH automatisée.</p></div></div>
  </>;
}

type EduOption = { value: string; label: string };
type EduOptions = {
  workclass: EduOption[]; marital_status: EduOption[]; occupation: EduOption[]; relationship: EduOption[];
  race: EduOption[]; sex: EduOption[]; native_country: EduOption[]; income: EduOption[];
  age: { min: number; max: number }; hours: { min: number; max: number };
};
type EduResult = {
  prediction: { code: string; label: string; short: string; description: string; probability: number };
  probabilities: { code: string; label: string; probability: number }[];
  summary: { label: string; value: string }[];
  model: { name: string; n_features: number; n_classes: number; xgboost_version_trained?: string };
};

const emptyEducationForm = {
  age: "", sex: "", race: "", native_country: "", marital_status: "", relationship: "",
  workclass: "", occupation: "", hours_per_week: "", income: "",
};
type EduForm = typeof emptyEducationForm;
type EduKey = keyof EduForm;

function validateEducation(form: EduForm, opts: EduOptions): Partial<Record<EduKey, string>> {
  const errors: Partial<Record<EduKey, string>> = {};
  const checkNumber = (key: "age" | "hours_per_week", min: number, max: number, label: string) => {
    const raw = form[key].trim();
    if (!raw) errors[key] = `${label} est obligatoire.`;
    else if (!/^\d+$/.test(raw) || Number(raw) < min || Number(raw) > max) errors[key] = `${label} doit être un nombre entier entre ${min} et ${max}.`;
  };
  checkNumber("age", opts.age.min, opts.age.max, "L'âge");
  checkNumber("hours_per_week", opts.hours.min, opts.hours.max, "Le nombre d'heures par semaine");
  (["sex", "race", "native_country", "marital_status", "relationship", "workclass", "occupation", "income"] as const).forEach(key => {
    if (!form[key]) errors[key] = "Sélectionnez une valeur dans la liste.";
  });
  return errors;
}

function EduField({ id, label, hint, error, children }: { id: string; label: string; hint?: string; error?: string; children: React.ReactNode }) {
  return <div className={`edu-field${error ? " has-error" : ""}`}>
    <label htmlFor={id}>{label} <abbr title="obligatoire" aria-hidden="true">*</abbr></label>
    {children}
    {hint && !error && <small id={`${id}-hint`}>{hint}</small>}
    {error && <small className="field-error" id={`${id}-err`} role="alert">{error}</small>}
  </div>;
}

function EducationPrediction() {
  const [opts, setOpts] = useState<EduOptions | null>(null);
  const [optsError, setOptsError] = useState("");
  const [form, setForm] = useState<EduForm>(emptyEducationForm);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<EduKey, string>>>({});
  const [result, setResult] = useState<EduResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const resultRef = useRef<HTMLElement>(null);

  const loadOptions = () => {
    setOptsError("");
    fetch("/api/education/options/").then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(setOpts)
      .catch(() => setOptsError("Impossible de charger les listes de choix du modèle. Vérifiez que le serveur Django est démarré."));
  };
  useEffect(loadOptions, []);

  const update = (field: EduKey, value: string) => {
    setForm(current => ({ ...current, [field]: value }));
    setFieldErrors(current => { if (!current[field]) return current; const { [field]: _removed, ...rest } = current; return rest; });
  };
  const fieldProps = (field: EduKey) => ({
    id: `edu-${field}`, value: form[field], required: true,
    "aria-invalid": fieldErrors[field] ? true : undefined,
    "aria-describedby": fieldErrors[field] ? `edu-${field}-err` : undefined,
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => update(field, e.target.value),
  });
  const select = (field: EduKey, list: EduOption[]) => <select {...fieldProps(field)}>
    <option value="">Sélectionner…</option>{list.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
  </select>;

  const focusField = (field: string) => window.setTimeout(() => document.getElementById(`edu-${field}`)?.focus(), 0);
  const order: EduKey[] = ["age", "sex", "race", "native_country", "marital_status", "relationship", "workclass", "occupation", "hours_per_week", "income"];

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!opts || loading) return;
    const errors = validateEducation(form, opts);
    setFieldErrors(errors);
    const first = order.find(f => errors[f]);
    if (first) { setError("Corrigez les champs signalés avant de lancer la prédiction."); focusField(first); return; }
    setError(""); setLoading(true); setResult(null);
    try {
      const res = await fetch("/api/education/predict/", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, age: Number(form.age), hours_per_week: Number(form.hours_per_week) }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        if (data.fields) { setFieldErrors(data.fields); const f = order.find(k => data.fields[k]); if (f) focusField(f); }
        setError(data.error || "La prédiction a échoué.");
        return;
      }
      setResult(data as EduResult);
      window.setTimeout(() => { resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }); resultRef.current?.focus({ preventScroll: true }); }, 50);
    } catch {
      setError("Le serveur est injoignable. Vérifiez que l'application Django est démarrée.");
    } finally {
      setLoading(false);
    }
  };
  const reset = () => { setForm(emptyEducationForm); setFieldErrors({}); setError(""); setResult(null); focusField("age"); };
  const newPrediction = () => { setResult(null); setError(""); window.scrollTo({ top: 0, behavior: "smooth" }); focusField("age"); };

  const best = result?.prediction;
  return <>
    <PageHeader title="Prédiction du niveau d’éducation" subtitle="Estimez le niveau d’éducation probable à partir des caractéristiques personnelles et professionnelles d’un individu." actions={<Badge tone="info">XGBoost · UCI Adult</Badge>}/>
    {optsError && <div className="prediction-error" role="alert"><Icon name="close" size={17}/><div><strong>Formulaire indisponible</strong><span>{optsError}</span></div><button onClick={loadOptions}>Réessayer</button></div>}
    {error && <div className="prediction-error" role="alert"><Icon name="close" size={17}/><div><strong>Prédiction impossible</strong><span>{error}</span></div><button onClick={() => setError("")} aria-label="Fermer le message"><Icon name="close" size={15}/></button></div>}
    <div className="prediction-layout">
      <form className="card prediction-form" onSubmit={submit} onReset={e => { e.preventDefault(); reset(); }} noValidate aria-busy={loading}>
        <div className="prediction-card-heading"><div className="service-icon violet"><Icon name="brain"/></div><div><span className="eyebrow">DONNÉES DU PROFIL</span><h2>Caractéristiques de l’individu</h2><p>Tous les champs sont obligatoires (<abbr title="obligatoire">*</abbr>). Le niveau d’éducation est la valeur prédite : il n’est pas demandé.</p></div></div>
        {!opts && !optsError && <div className="prediction-empty" role="status"><div className="spinner"/><p>Chargement du formulaire…</p></div>}
        {opts && <div className="prediction-groups">
          <fieldset className="prediction-fieldset"><legend>Informations personnelles</legend><div className="prediction-form-grid">
            <EduField id="edu-age" label="Âge (ans)" hint={`Entre ${opts.age.min} et ${opts.age.max}`} error={fieldErrors.age}><input type="number" inputMode="numeric" min={opts.age.min} max={opts.age.max} step={1} placeholder="Ex. 38" {...fieldProps("age")}/></EduField>
            <EduField id="edu-sex" label="Sexe" error={fieldErrors.sex}>{select("sex", opts.sex)}</EduField>
            <EduField id="edu-race" label="Origine ethnique" error={fieldErrors.race}>{select("race", opts.race)}</EduField>
            <EduField id="edu-native_country" label="Pays d’origine" error={fieldErrors.native_country}>{select("native_country", opts.native_country)}</EduField>
          </div></fieldset>
          <fieldset className="prediction-fieldset"><legend>Situation familiale</legend><div className="prediction-form-grid">
            <EduField id="edu-marital_status" label="Statut marital" error={fieldErrors.marital_status}>{select("marital_status", opts.marital_status)}</EduField>
            <EduField id="edu-relationship" label="Rôle dans la famille" error={fieldErrors.relationship}>{select("relationship", opts.relationship)}</EduField>
          </div></fieldset>
          <fieldset className="prediction-fieldset"><legend>Situation professionnelle</legend><div className="prediction-form-grid">
            <EduField id="edu-workclass" label="Catégorie d’emploi" error={fieldErrors.workclass}>{select("workclass", opts.workclass)}</EduField>
            <EduField id="edu-occupation" label="Métier" error={fieldErrors.occupation}>{select("occupation", opts.occupation)}</EduField>
            <EduField id="edu-hours_per_week" label="Heures travaillées par semaine" hint={`Entre ${opts.hours.min} et ${opts.hours.max}`} error={fieldErrors.hours_per_week}><input type="number" inputMode="numeric" min={opts.hours.min} max={opts.hours.max} step={1} placeholder="Ex. 40" {...fieldProps("hours_per_week")}/></EduField>
          </div></fieldset>
          <fieldset className="prediction-fieldset"><legend>Caractéristiques financières</legend><div className="prediction-form-grid">
            <EduField id="edu-income" label="Tranche de revenu annuel" hint="Variable utilisée par le modèle (seuil de 50 000 $)." error={fieldErrors.income}>{select("income", opts.income)}</EduField>
          </div></fieldset>
        </div>}
        <div className="prediction-form-footer"><div><Icon name="settings" size={16}/><span>Les données saisies servent uniquement au calcul et ne sont pas enregistrées.</span></div><div className="prediction-actions"><button className="btn btn-secondary" type="reset" disabled={loading || !opts}><span>Réinitialiser</span></button><Button icon="spark" type="submit" disabled={loading || !opts}>{loading ? "Prédiction en cours…" : "Prédire le niveau d'éducation"}</Button></div></div>
      </form>

      <aside className="card prediction-result" ref={resultRef} tabIndex={-1} aria-label="Résultat de la prédiction">
        <div className="prediction-result-head"><div><span className="eyebrow">RÉSULTAT DU MODÈLE</span><h2>Estimation du niveau</h2></div>{result && <Badge tone="success">Prédiction terminée</Badge>}</div>
        <div aria-live="polite" aria-atomic="true">
        {loading ? <div className="prediction-empty" role="status"><div className="spinner"/><h3>Analyse du profil en cours</h3><p>Le modèle calcule le niveau d’éducation le plus probable.</p></div> : result && best ? <div className="prediction-result-content">
          <div className="education-result-visual"><div><Icon name="graduation" size={29}/></div><span>NIVEAU D’ÉDUCATION PRÉDIT</span><strong>{best.label}</strong><small>{best.short}</small></div>
          <div className="prediction-confidence"><div><span>Probabilité attribuée par le modèle</span><strong>{best.probability.toLocaleString("fr-FR")} %</strong></div><div aria-hidden="true"><span style={{ width: `${best.probability}%` }}/></div><small>Probabilité estimée par le modèle (predict_proba), et non une garantie d’exactitude.</small></div>
          <div className="prob-block"><strong>Probabilité de chaque niveau</strong>
            <ul className="prob-bars">{result.probabilities.map(p => <li key={p.code} className={p.code === best.code ? "top" : ""}><span className="prob-label">{p.label}</span><span className="prob-track" aria-hidden="true"><i style={{ width: `${p.probability}%` }}/></span><span className="prob-value">{p.probability.toLocaleString("fr-FR")} %</span></li>)}</ul>
          </div>
          <div className="prediction-interpretation"><strong>Interprétation</strong><p>{best.description}</p><p>Il s’agit du niveau le plus fréquent observé dans le jeu de données pour des profils présentant des caractéristiques similaires. Ce n’est ni une information vérifiée sur la personne, ni une preuve de diplôme.</p></div>
          <div className="used-information"><strong>Résumé du profil</strong><dl className="profile-summary-list">{result.summary.map(s => <div key={s.label}><dt>{s.label}</dt><dd>{s.value}</dd></div>)}</dl></div>
          <details className="prediction-details"><summary>Voir les détails de la prédiction</summary><div>
            <table><thead><tr><th>Niveau</th><th>Probabilité</th></tr></thead><tbody>{result.probabilities.map(p => <tr key={p.code}><td>{p.label} <small>({p.code})</small></td><td>{p.probability.toLocaleString("fr-FR")} %</td></tr>)}</tbody></table>
            <p>Modèle : {result.model.name} · {result.model.n_features} variables d’entrée · {result.model.n_classes} classes{result.model.xgboost_version_trained ? ` · entraîné avec XGBoost ${result.model.xgboost_version_trained}` : ""}.</p>
            <p>Données d’entraînement : recensement américain de 1994 (UCI Adult). Le résultat est indicatif et peut refléter les biais de ces données.</p>
          </div></details>
          <div className="prediction-disclaimer"><Icon name="spark" size={17}/><p>Le sexe, l’origine ethnique et le pays d’origine sont des variables sensibles du modèle : ne les utilisez jamais pour une décision d’embauche, de rémunération ou d’orientation.</p></div>
          <Button variant="secondary" icon="plus" onClick={newPrediction}>Nouvelle prédiction</Button>
        </div> : <div className="prediction-empty"><div className="empty-result-icon"><Icon name="graduation" size={27}/></div><h3>Aucune prédiction pour le moment</h3><p>Complétez le formulaire puis cliquez sur « Prédire le niveau d'éducation ».</p></div>}
        </div>
      </aside>
    </div>
  </>;
}

function Training() {
  return <><PageHeader title="Formation et compétences" subtitle="Identifiez des pistes de développement cohérentes avec les profils explorés." actions={<Button icon="plus">Créer un parcours</Button>}/><div className="training-hero card"><div><span className="eyebrow">PARCOURS RECOMMANDÉ</span><h2>De l'analyse financière à la data visualisation</h2><p>Un parcours progressif construit à partir du profil PRF-1048 et de ses objectifs exploratoires.</p><div><Button>Voir le parcours</Button><Button variant="ghost">Modifier</Button></div></div><div className="progress-ring"><strong>68%</strong><span>Adéquation</span></div></div><div className="section-title"><div><h2>Domaines suggérés</h2><p>Compétences fréquemment associées aux trajectoires proposées.</p></div></div><div className="learning-grid">{[["Data visualisation", "Intermédiaire", 72], ["Outils de Business Intelligence", "Débutant", 54], ["Pilotage budgétaire", "Avancé", 81], ["Conseil stratégique", "Intermédiaire", 63]].map((x, i) => <article className="card learning" key={x[0]}><div className={`service-icon ${["blue","teal","violet","amber"][i]}`}><Icon name={i < 2 ? "chart" : "book"}/></div><Badge tone="neutral">{x[1]}</Badge><h3>{x[0]}</h3><p>Compétence à explorer dans le cadre d'un parcours validé avec un conseiller.</p><div className="trait"><div><span>Pertinence</span><strong>{x[2]} %</strong></div><div><span style={{width:`${x[2]}%`}}/></div></div></article>)}</div></>;
}

function Placeholder({ page }: { page: string }) {
  return <><PageHeader title={page} subtitle="Configurez votre espace ProfilPro RH et vos préférences."/><section className="card placeholder"><div><Icon name="settings" size={32}/></div><h2>Configuration de la plateforme</h2><p>Gérez les accès, les notifications, la confidentialité des données et les paramètres des modèles.</p><Button>Ouvrir les préférences</Button></section></>;
}

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const [analysisDraft, setAnalysisDraft] = useState<AnalysisDraft>(emptyAnalysisDraft);
  const currentLabel = useMemo(() => page === "analysis-results" ? "Résultats de l'analyse" : navigation.find(n => n.id === page)?.label ?? "", [page]);
  const go = (id: string) => { setPage(id); window.scrollTo({ top: 0, behavior: "smooth" }); };
  return <div className={`app-shell ${collapsed ? "sidebar-collapsed" : ""}`}>
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><span/><span/><span/></div><div><strong>ProfilPro</strong><small>RH</small></div><button className="collapse-btn" onClick={() => setCollapsed(!collapsed)} aria-label="Réduire la navigation"><Icon name="arrow" size={16}/></button></div>
      <nav aria-label="Navigation principale">{navigation.map(n => <button key={n.id} className={page === n.id ? "active" : ""} onClick={() => go(n.id)}><Icon name={n.icon as IconName}/><span>{n.label}</span>{page === n.id && <i/>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="help-card"><div><Icon name="spark"/></div><strong>Besoin d'aide ?</strong><p>Consultez le guide de la plateforme.</p><button>Voir le guide</button></div><div className="version"><span>Projet académique</span><small>Version 1.0 · Données simulées</small></div></div>
    </aside>
    <div className="main-area"><header className="topbar"><div className="mobile-brand">ProfilPro RH</div><label className="global-search"><Icon name="search"/><input placeholder="Rechercher un profil, une analyse..."/><kbd>⌘ K</kbd></label><div className="top-actions"><button className="notification"><Icon name="bell"/><span/></button><div className="top-divider"/><button className="user-menu"><span className="avatar">CM</span><span><strong>Claire Martin</strong><small>Responsable RH</small></span><Icon name="chevron" size={16}/></button></div></header>
      <main><div className="breadcrumb"><span>ProfilPro RH</span><Icon name="arrow" size={14}/><strong>{currentLabel}</strong></div>
        {page === "dashboard" && <Dashboard navigate={go}/>}
        {page === "profiles" && <Profiles/>}
        {page === "analysis" && <Analysis draft={analysisDraft} setDraft={setAnalysisDraft} onLaunch={() => go("analysis-results")}/>}
        {page === "analysis-results" && <AnalysisResults draft={analysisDraft} onBack={() => go("analysis")} onRestart={() => { setAnalysisDraft(emptyAnalysisDraft); go("analysis"); }}/>}
        {page === "segmentation" && <Segmentation/>}
        {page === "orientation" && <Orientation/>}
        {page === "training" && <Training/>}
        {page === "education-prediction" && <EducationPrediction/>}
        {page === "settings" && <Placeholder page="Paramètres"/>}
      </main>
    </div>
  </div>;
}
