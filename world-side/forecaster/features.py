"""Feature extraction helpers for the World Side forecaster.

The functions in this module are intentionally deterministic and stdlib-only.
They turn markdown corpus text or Cyber Side candidate dictionaries into the
same compact feature representation so other workers can score analogies
without reparsing prose.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Any, Iterable, Mapping


_CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s)>]+")
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9+._/-]*")


@dataclass(frozen=True)
class FeatureSet:
    """Normalized strategic and cyber features extracted from text."""

    actors: tuple[str, ...] = ()
    actor_countries: tuple[str, ...] = ()
    actor_types: tuple[str, ...] = ()
    target_regions: tuple[str, ...] = ()
    target_sectors: tuple[str, ...] = ()
    trigger_classes: tuple[str, ...] = ()
    vector_classes: tuple[str, ...] = ()
    burn_classes: tuple[str, ...] = ()
    objectives: tuple[str, ...] = ()
    products: tuple[str, ...] = ()
    techniques: tuple[str, ...] = ()
    cves: tuple[str, ...] = ()
    timing_markers: tuple[str, ...] = ()
    source_urls: tuple[str, ...] = ()
    raw_terms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActorRule:
    actor: str
    country: str
    actor_type: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class KeywordRule:
    feature: str
    keywords: tuple[str, ...]


ACTOR_RULES: tuple[ActorRule, ...] = (
    ActorRule("Sandworm / GRU Unit 74455", "Russia", "state_military_intelligence", ("sandworm", "gru unit 74455", "unit 74455", "apt44", "voodoo bear")),
    ActorRule("APT28 / GRU Unit 26165", "Russia", "state_military_intelligence", ("apt28", "fancy bear", "gru 26165", "unit 26165")),
    ActorRule("APT29 / SVR", "Russia", "state_foreign_intelligence", ("apt29", "cozy bear", "svr", "unc2452", "nobelium", "solarwinds")),
    ActorRule("Russian state or state-tolerated actor", "Russia", "state_or_tolerated_proxy", ("russia", "russian", "fsb", "tsniikhm", "killnet", "noname057", "cyberarmyofrussia")),
    ActorRule("Cl0p / TA505", "Russia", "criminal_state_tolerated", ("cl0p", "clop", "ta505", "fin11", "lace tempest")),
    ActorRule("Lazarus / RGB", "North Korea", "state_financial_theft", ("lazarus", "apt38", "beagleboyz", "bluenoroff", "rgb", "dprk", "north korea", "tradertraitor")),
    ActorRule("PRC MSS-linked actor", "China", "state_intelligence", ("prc", "china", "chinese", "mss", "mps", "apt27", "i-soon", "isoon", "anxun", "flax typhoon")),
    ActorRule("Volt Typhoon", "China", "state_prepositioning", ("volt typhoon", "bronze silhouette", "vanguard panda", "insidious taurus")),
    ActorRule("UNC5221", "China", "state_or_suspected_state", ("unc5221", "hafnium", "silk typhoon")),
    ActorRule("Iran IRGC-linked actor", "Iran", "state_or_proxy", ("iran", "iranian", "irgc", "apt35", "apt42", "mint sandstorm", "emennet", "cyberav3ngers", "mois")),
    ActorRule("US / Israel", "United States / Israel", "state", ("unit 8200", "nsa", "cia", "olympic games", "stuxnet")),
)


TRIGGER_RULES: tuple[KeywordRule, ...] = (
    KeywordRule("sanctions_pressure", ("sanction", "ofac", "sdn", "embargo", "tariff", "designation", "delisting", "eu package", "oil cap")),
    KeywordRule("legal_retaliation", ("indictment", "indicted", "charged", "extradition", "extradited", "sentencing", "trial", "prosecution", "seizure", "takedown")),
    KeywordRule("election_cycle", ("election", "primary", "midterm", "campaign", "vote", "voter", "ballot", "certification", "poll")),
    KeywordRule("diplomatic_summit", ("summit", "unga", "nato", "g7", "g20", "apec", "asean", "brics", "cop31", "bilateral", "dialogue", "ministerial")),
    KeywordRule("anniversary_symbolism", ("anniversary", "independence day", "russia day", "tiananmen", "9/11", "foundation day", "national day", "constitution day")),
    KeywordRule("holiday_response_gap", ("holiday", "long weekend", "memorial day", "thanksgiving", "black friday", "cyber monday", "lailat al qadr", "friday weekend")),
    KeywordRule("kinetic_or_military_crisis", ("invasion", "kinetic", "h-hour", "military", "missile", "blockade", "mobilization", "force buildup", "carrier", "war")),
    KeywordRule("financial_pressure", ("fomc", "swift", "federal reserve", "crypto", "currency", "foreign-currency", "revenue", "oil", "bank", "payment")),
    KeywordRule("critical_infra_stress", ("hurricane", "landfall", "evac", "winter", "heating", "utility stress", "coastal", "storm")),
    KeywordRule("standing_collection", ("standing collection", "espionage", "pre-position", "preposition", "dwell", "long-fuse", "collection mission")),
)


VECTOR_RULES: tuple[KeywordRule, ...] = (
    KeywordRule("edge_appliance_exploitation", ("edge", "vpn", "gateway", "firewall", "router", "soho", "fortinet", "fortigate", "ivanti", "connect secure", "citrix", "netscaler", "sonicwall", "globalprotect", "pan-os")),
    KeywordRule("software_supply_chain", ("supply-chain", "supply chain", "trojanized update", "build pipeline", "update server", "orion", "m.e.doc", "vendor")),
    KeywordRule("credential_phishing", ("spearphishing", "spear-phishing", "phishing", "credential harvest", "spoofed login", "bitly", "google login")),
    KeywordRule("living_off_the_land", ("living-off-the-land", "lotl", "wmic", "ntdsutil", "netsh", "powershell", "certutil", "psexec", "wmi")),
    KeywordRule("managed_file_transfer", ("managed file-transfer", "managed file transfer", "moveit", "goanywhere", "accellion", "mft", "secure-comms")),
    KeywordRule("wiper_malware", ("wiper", "wipe", "disttrack", "shamoon", "hermeticwiper", "whispergate", "notpetya", "acidrain", "caddywiper", "zerocleare")),
    KeywordRule("ransomware_or_extortion", ("ransomware", "extortion", "data-leak", "leak site", "cl0p", "lockbit", "phobos", "blacksuit", "royal")),
    KeywordRule("financial_messaging_or_crypto", ("swift", "mt103", "alliance access", "crypto", "defi", "bridge", "custody", "wallet", "exchange")),
    KeywordRule("ics_scada", ("ics", "scada", "plc", "profibus", "siemens", "s7", "opc da", "iec 60870", "iec 61850", "triconex", "sis", "tristation")),
    KeywordRule("ddos_or_defacement", ("ddos", "defacement", "deface", "botnet", "traffic flood")),
    KeywordRule("webshell_or_backdoor", ("webshell", "backdoor", "rat", "passive backdoor", "x-agent", "x-tunnel", "zipline", "glasstoken", "lightwire", "warpwired")),
    KeywordRule("information_operation_leak", ("hack-and-leak", "leak", "guccifer", "dcleaks", "cut-out persona", "influence", "disinformation")),
)


BURN_RULES: tuple[KeywordRule, ...] = (
    KeywordRule("destructive_wiper", ("wiper", "destructive", "destroy", "unbootable", "disk", "mass workstation destruction", "worm-wiper")),
    KeywordRule("disruption_or_shutdown", ("shutdown", "outage", "knocked offline", "disruption", "disable", "deny", "denial-of-service", "reboot", "maintenance mode")),
    KeywordRule("espionage_collection", ("espionage", "collection", "reconnaissance", "selective second-stage", "stealth exploitation")),
    KeywordRule("prepositioning_for_conflict", ("pre-position", "preposition", "persistent access", "future crisis", "conflict", "dormant")),
    KeywordRule("financial_theft", ("theft", "heist", "fraudulent swift", "laundered", "stolen", "crypto heist", "revenue")),
    KeywordRule("extortion", ("extortion", "ransom", "data theft", "leak", "ransomware")),
    KeywordRule("influence_or_leak", ("hack-and-leak", "influence", "curated leaks", "persona", "disinformation")),
    KeywordRule("physical_effects", ("physical", "centrifuge", "safety", "petrochemical", "grid", "substation", "plant")),
    KeywordRule("initial_access_brokerage", ("initial access", "broad initial access", "downstream selection", "access broker")),
)


OBJECTIVE_RULES: tuple[KeywordRule, ...] = (
    KeywordRule("deny_or_degrade_operations", ("shutdown", "disrupt", "outage", "disable", "deny", "degrade")),
    KeywordRule("steal_funds", ("steal", "heist", "fraudulent", "launder", "revenue", "foreign-currency")),
    KeywordRule("collect_intelligence", ("espionage", "collection", "reconnaissance", "policy drafts", "negotiation staff")),
    KeywordRule("shape_information_environment", ("influence", "hack-and-leak", "disinformation", "propaganda", "defacement")),
    KeywordRule("preposition_for_later", ("pre-position", "preposition", "persistent access", "dwell", "future crisis")),
    KeywordRule("demonstrate_capability", ("capability demonstration", "demonstrative", "symbolic", "signal")),
    KeywordRule("cause_physical_effect", ("physical", "centrifuge", "safety system", "petrochemical", "grid", "substation")),
)


SECTOR_RULES: tuple[KeywordRule, ...] = (
    KeywordRule("government", ("government", "federal", "agency", "ministry", "treasury", "commerce", "state department", "dhs", "doe", "doj")),
    KeywordRule("defense", ("defense", "military", "indopacom", "nato", "defense contractor", "defence")),
    KeywordRule("election_political", ("election", "campaign", "party", "dnc", "dcc", "voter", "secretary of state", "sos")),
    KeywordRule("financial", ("bank", "swift", "federal reserve", "payment", "fomc", "financial", "aml")),
    KeywordRule("crypto", ("crypto", "defi", "exchange", "bridge", "wallet", "mixer", "otc")),
    KeywordRule("energy", ("energy", "electric", "grid", "substation", "power", "wind", "solar", "utility", "utilities")),
    KeywordRule("water", ("water", "wastewater", "public drinking water")),
    KeywordRule("oil_gas", ("oil", "gas", "lng", "petrochemical", "refining", "aramco", "rasgas", "pipeline")),
    KeywordRule("communications", ("communications", "telecom", "satellite", "viasat", "ka-sat", "cdn")),
    KeywordRule("transportation", ("transport", "airport", "rail", "port", "shipping", "logistics", "transit")),
    KeywordRule("healthcare", ("hospital", "healthcare", "medical", "ehr", "medical-tech")),
    KeywordRule("education", ("school", "university", "education")),
    KeywordRule("media", ("media", "journalist", "broadcaster", "tv", "news")),
    KeywordRule("enterprise_saas", ("enterprise", "saas", "managed file-transfer", "mft", "b2b", "ticketing")),
    KeywordRule("critical_infrastructure", ("critical infrastructure", "water", "energy", "communications", "transportation", "hospital", "utility")),
    KeywordRule("industrial_control", ("ics", "scada", "plc", "industrial", "safety instrumented", "plant", "nuclear")),
    KeywordRule("retail", ("retail", "e-commerce", "black friday", "cyber monday", "shopping", "payment processor")),
)


REGION_RULES: tuple[KeywordRule, ...] = (
    KeywordRule("United States", ("united states", " u.s.", " us ", "usa", "american", "alabama", "california", "new jersey", "washington")),
    KeywordRule("Ukraine", ("ukraine", "ukrainian", "kyiv", "donbas", "crimea", "chernobyl")),
    KeywordRule("Russia", ("russia", "russian", "moscow", "kremlin")),
    KeywordRule("China / Taiwan", ("china", "prc", "taiwan", "taiwan strait", "beijing")),
    KeywordRule("Korean Peninsula", ("north korea", "dprk", "korea", "pyongyang")),
    KeywordRule("Iran / Gulf", ("iran", "iranian", "saudi", "aramco", "qatar", "gulf", "hormuz", "uae", "bahrain")),
    KeywordRule("Europe / NATO", ("europe", "eu ", "nato", "estonia", "latvia", "sweden", "poland", "france", "turkiye", "netherlands")),
    KeywordRule("ASEAN / Indo-Pacific", ("asean", "philippines", "singapore", "indopacific", "indo-pacific", "guam", "hawaii")),
    KeywordRule("Latin America", ("colombia", "peru", "brazil", "venezuela")),
)


PRODUCT_RULES: tuple[KeywordRule, ...] = (
    KeywordRule("Ivanti Connect Secure", ("ivanti connect secure", "policy secure", "pulse connect secure")),
    KeywordRule("Fortinet / FortiGate", ("fortinet", "fortigate", "fortiguard")),
    KeywordRule("Citrix NetScaler", ("citrix", "netscaler", "citrixbleed")),
    KeywordRule("Palo Alto PAN-OS", ("palo alto", "pan-os", "globalprotect")),
    KeywordRule("Cisco / SOHO routers", ("cisco", "netgear", "asus", "soho router", "ios xe")),
    KeywordRule("Progress MOVEit", ("moveit", "progress moveit")),
    KeywordRule("GoAnywhere MFT", ("goanywhere",)),
    KeywordRule("Accellion FTA", ("accellion",)),
    KeywordRule("SolarWinds Orion", ("solarwinds", "orion")),
    KeywordRule("Microsoft Exchange", ("microsoft exchange", "proxylogon")),
    KeywordRule("Microsoft Windows / SMB", ("windows", "smb", "eternalblue", "eternalromance", "ms17-010")),
    KeywordRule("Siemens SIMATIC / S7", ("siemens", "simatic", "s7-315", "s7-417")),
    KeywordRule("Schneider Triconex", ("triconex", "tricon", "tristation", "schneider electric")),
    KeywordRule("M.E.Doc", ("m.e.doc", "medoc")),
)


TECHNIQUE_RULES: tuple[KeywordRule, ...] = (
    KeywordRule("auth_bypass", ("auth bypass", "authentication bypass", "unauthenticated", "bypass")),
    KeywordRule("command_injection", ("command injection", "execute commands", "rce", "remote code execution")),
    KeywordRule("sql_injection", ("sql injection", "sqli")),
    KeywordRule("privilege_escalation", ("privilege escalation", "privesc")),
    KeywordRule("credential_theft", ("credential theft", "credential harvest", "mimikatz", "password", "tokens")),
    KeywordRule("lateral_movement", ("lateral movement", "psexec", "wmi", "wmic")),
    KeywordRule("signed_driver_abuse", ("signed driver", "rawdisk", "driver")),
    KeywordRule("living_off_the_land", ("living-off-the-land", "lotl", "powershell", "certutil", "netsh")),
    KeywordRule("webshell", ("webshell",)),
    KeywordRule("botnet_proxying", ("botnet", "kv-botnet", "proxy", "obscure traffic")),
)


TIMING_RULES: tuple[KeywordRule, ...] = (
    KeywordRule("hours_to_days", ("hours-to-days", "hours", "24-48 hours", "0 days", "72h", "h-hour")),
    KeywordRule("weeks", ("week", "weeks", "30 days", "45 days", "4-6 wks", "4–6 wks")),
    KeywordRule("months", ("month", "months", "6 months", "9 months", "12 months")),
    KeywordRule("years", ("year", "years", "multi-year", "5+ years", "12-24 months", "12–24 months")),
    KeywordRule("calendar_locked", ("calendar-locked", "anniversary", "holiday", "election day", "opening match", "final")),
)


def extract_features(text: str, *, extra_terms: Iterable[str] = ()) -> FeatureSet:
    """Extract normalized feature buckets from arbitrary text."""

    normalized = _normalize_text(text)
    actors: set[str] = set()
    actor_countries: set[str] = set()
    actor_types: set[str] = set()
    for rule in ACTOR_RULES:
        if _contains_any(normalized, rule.aliases):
            actors.add(rule.actor)
            actor_countries.add(rule.country)
            actor_types.add(rule.actor_type)

    raw_terms = set(_interesting_terms(normalized))
    raw_terms.update(_clean_token(term) for term in extra_terms if _clean_token(term))

    return FeatureSet(
        actors=_sorted(actors),
        actor_countries=_sorted(actor_countries),
        actor_types=_sorted(actor_types),
        target_regions=_features_from_rules(normalized, REGION_RULES),
        target_sectors=_features_from_rules(normalized, SECTOR_RULES),
        trigger_classes=_features_from_rules(normalized, TRIGGER_RULES),
        vector_classes=_features_from_rules(normalized, VECTOR_RULES),
        burn_classes=_features_from_rules(normalized, BURN_RULES),
        objectives=_features_from_rules(normalized, OBJECTIVE_RULES),
        products=_features_from_rules(normalized, PRODUCT_RULES),
        techniques=_features_from_rules(normalized, TECHNIQUE_RULES),
        cves=_sorted(cve.upper() for cve in _CVE_RE.findall(text)),
        timing_markers=_features_from_rules(normalized, TIMING_RULES),
        source_urls=_sorted(_URL_RE.findall(text)),
        raw_terms=_sorted(raw_terms),
    )


def normalize_candidate(candidate: Mapping[str, Any] | str) -> FeatureSet:
    """Normalize a Stage 1 candidate dictionary or JSON string into features."""

    parsed: Any = candidate
    if isinstance(candidate, str):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            parsed = candidate

    extra_terms: list[str] = []
    if isinstance(parsed, Mapping):
        for key in (
            "candidate_type",
            "candidate_label",
            "attack_vector",
            "intended_effect",
            "destructiveness",
            "target_sector",
            "target_region",
            "actor_hint",
        ):
            value = parsed.get(key)
            if isinstance(value, str):
                extra_terms.append(value)
        attack_hypothesis = parsed.get("attack_hypothesis")
        if isinstance(attack_hypothesis, Mapping):
            extra_terms.extend(str(value) for value in attack_hypothesis.values() if isinstance(value, str))

    return extract_features(_flatten_for_features(parsed), extra_terms=extra_terms)


def merge_feature_sets(*feature_sets: FeatureSet) -> FeatureSet:
    """Union multiple feature sets while preserving deterministic ordering."""

    merged: dict[str, set[str]] = {field: set() for field in FeatureSet.__dataclass_fields__}
    for feature_set in feature_sets:
        for field, value in feature_set.to_dict().items():
            merged[field].update(value)
    return FeatureSet(**{field: _sorted(values) for field, values in merged.items()})


def feature_overlap(left: FeatureSet, right: FeatureSet) -> dict[str, Any]:
    """Return overlap counts by feature bucket plus a simple weighted score."""

    weights = {
        "actors": 3.0,
        "actor_countries": 2.0,
        "target_sectors": 2.0,
        "trigger_classes": 2.5,
        "vector_classes": 3.0,
        "burn_classes": 2.5,
        "objectives": 2.0,
        "products": 2.0,
        "techniques": 1.5,
        "timing_markers": 1.0,
    }
    buckets: dict[str, list[str]] = {}
    score = 0.0
    for field, weight in weights.items():
        overlap = sorted(set(getattr(left, field)) & set(getattr(right, field)))
        if overlap:
            buckets[field] = overlap
            score += weight * len(overlap)
    return {"score": round(score, 3), "overlap": buckets}


def _features_from_rules(text: str, rules: Iterable[KeywordRule]) -> tuple[str, ...]:
    return _sorted(rule.feature for rule in rules if _contains_any(text, rule.keywords))


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(_contains_keyword(text, keyword) for keyword in keywords)


def _contains_keyword(text: str, keyword: str) -> bool:
    keyword = _normalize_text(keyword)
    if not keyword:
        return False
    if not keyword.replace("-", "").isalnum():
        return keyword in text
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text) is not None


def _flatten_for_features(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        parts: list[str] = []
        for key, item in value.items():
            parts.append(str(key))
            parts.append(_flatten_for_features(item))
        return " ".join(parts)
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten_for_features(item) for item in value)
    return str(value)


def _interesting_terms(text: str) -> tuple[str, ...]:
    keep: set[str] = set()
    for token in _WORD_RE.findall(text):
        token = _clean_token(token)
        if len(token) < 4:
            continue
        if token.startswith(("cve-", "apt", "unc")):
            keep.add(token)
        elif token in {
            "russia",
            "ukraine",
            "china",
            "taiwan",
            "iran",
            "dprk",
            "sanctions",
            "election",
            "summit",
            "wiper",
            "ransomware",
            "phishing",
            "supply-chain",
            "critical",
            "infrastructure",
            "edge",
            "vpn",
            "ics",
            "scada",
            "swift",
            "crypto",
        }:
            keep.add(token)
    return _sorted(keep)


def _clean_token(value: str) -> str:
    return _normalize_text(value).strip(" .,:;()[]{}*_`\"'")


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("–", "-").replace("—", "-").replace("→", " -> ")
    return re.sub(r"\s+", " ", text)


def _sorted(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))
