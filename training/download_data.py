"""Download and merge phishing URL datasets from public sources."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from training.config import (
    BENIGN_URLS_URL,
    OPENPHISH_FEED_URL,
    PHIUSIIL_MIRROR_URL,
    RAW_DIR,
)

logger = logging.getLogger(__name__)


def _fetch_text(url: str, timeout: int = 60) -> Optional[str]:
    """Fetch text content from a URL."""
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "PhishLens/1.0"})
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return None


def _fetch_csv(url: str) -> Optional[pd.DataFrame]:
    """Fetch a CSV file from a URL."""
    try:
        return pd.read_csv(url)
    except Exception as exc:
        logger.warning("Failed to read CSV from %s: %s", url, exc)
        return None


def download_openphish(output_path: Path) -> int:
    """Download OpenPhish feed (phishing URLs only)."""
    text = _fetch_text(OPENPHISH_FEED_URL)
    if not text:
        return 0
    urls = [line.strip() for line in text.splitlines() if line.strip().startswith("http")]
    df = pd.DataFrame({"url": urls, "label": 1, "source": "OpenPhish"})
    df.to_csv(output_path, index=False)
    logger.info("Saved %d OpenPhish URLs to %s", len(df), output_path)
    return len(df)


def download_phiusiil(output_path: Path) -> int:
    """Download PhiUSIIL Phishing URL Dataset mirror."""
    df = _fetch_csv(PHIUSIIL_MIRROR_URL)
    if df is None or df.empty:
        return 0

    # Normalize column names across possible formats
    cols = {c.lower(): c for c in df.columns}
    url_col = None
    label_col = None
    for candidate in ("url", "urls", "uri"):
        if candidate in cols:
            url_col = cols[candidate]
            break
    for candidate in ("label", "class", "type", "phishing"):
        if candidate in cols:
            label_col = cols[candidate]
            break

    if url_col is None:
        url_col = df.columns[0]

    result = pd.DataFrame()
    result["url"] = df[url_col].astype(str).str.strip()

    if label_col is not None:
        labels = df[label_col]
        if labels.dtype == object:
            result["label"] = labels.str.lower().map(
                lambda x: 1 if str(x) in ("1", "phishing", "bad", "malicious", "phish") else 0
            )
        else:
            result["label"] = labels.astype(int)
    else:
        # Assume second column is label if numeric
        if len(df.columns) > 1 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
            result["label"] = df.iloc[:, 1].astype(int)
        else:
            result["label"] = 1

    result["source"] = "PhiUSIIL"
    result = result[result["url"].str.startswith("http", na=False)]
    result.to_csv(output_path, index=False)
    logger.info("Saved %d PhiUSIIL URLs to %s", len(result), output_path)
    return len(result)


def download_benign_urls(output_path: Path) -> int:
    """Download benign URL list from public mirror or curated fallback."""
    df = _fetch_csv(BENIGN_URLS_URL)
    urls: list[str] = []
    if df is not None and not df.empty:
        col = df.columns[0]
        urls = df[col].astype(str).tolist()

    # Expanded curated benign domains and realistic URL patterns
    curated = [
        "https://www.google.com", "https://www.github.com", "https://www.wikipedia.org",
        "https://github.com/openai/triton", "https://github.com/microsoft/vscode",
        "https://github.com/torvalds/linux", "https://github.com/python/cpython",
        "https://drive.google.com/file/d/1aZ", "https://docs.google.com/document/d/1",
        "https://stackoverflow.com/questions/12345/example",
        "https://www.reddit.com/r/programming", "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.python.org", "https://www.microsoft.com", "https://www.apple.com",
        "https://www.amazon.com", "https://www.stackoverflow.com", "https://www.reddit.com",
        "https://www.bbc.com", "https://www.nytimes.com", "https://www.linkedin.com",
        "https://docs.python.org", "https://www.cloudflare.com", "https://www.mozilla.org",
        "https://www.netflix.com", "https://www.spotify.com", "https://www.twitter.com",
        "https://www.instagram.com", "https://www.youtube.com", "https://www.adobe.com",
        "https://www.oracle.com", "https://www.ibm.com", "https://www.intel.com",
        "https://www.nvidia.com", "https://www.docker.com", "https://www.kubernetes.io",
        "https://www.debian.org", "https://www.ubuntu.com", "https://www.kernel.org",
        "https://www.npmjs.com", "https://www.pypi.org", "https://www.w3.org",
        "https://www.ietf.org", "https://www.un.org", "https://www.who.int",
        "https://www.nature.com", "https://www.science.org", "https://www.springer.com",
        "https://www.cambridge.org", "https://www.ox.ac.uk", "https://www.mit.edu",
        "https://www.stanford.edu", "https://www.harvard.edu", "https://www.caltech.edu",
        "https://www.berkeley.edu", "https://www.cmu.edu", "https://www.princeton.edu",
        "https://www.yale.edu", "https://www.columbia.edu", "https://www.cornell.edu",
        "https://www.imperial.ac.uk", "https://www.ucl.ac.uk", "https://www.ed.ac.uk",
        "https://www.utoronto.ca", "https://www.ubc.ca", "https://www.mcgill.ca",
        "https://www.sydney.edu.au", "https://www.melbourne.edu.au", "https://www.anu.edu.au",
        "https://www.ethz.ch", "https://www.epfl.ch", "https://www.tum.de",
        "https://www.kit.edu", "https://www.rwth-aachen.de", "https://www.lmu.de",
        "https://www.sorbonne-universite.fr", "https://www.polytechnique.edu",
        "https://www.sjtu.edu.cn", "https://www.tsinghua.edu.cn", "https://www.pku.edu.cn",
        "https://www.u-tokyo.ac.jp", "https://www.kyoto-u.ac.jp", "https://www.osaka-u.ac.jp",
        "https://www.nus.edu.sg", "https://www.ntu.edu.sg", "https://www.hku.hk",
        "https://www.cuhk.edu.hk", "https://www.kaist.ac.kr", "https://www.snu.ac.kr",
        "https://www.iitb.ac.in", "https://www.iisc.ac.in", "https://www.iitd.ac.in",
        "https://www.technion.ac.il", "https://www.tau.ac.il", "https://www.huji.ac.il",
        "https://www.uchicago.edu", "https://www.upenn.edu", "https://www.duke.edu",
        "https://www.northwestern.edu", "https://www.jhu.edu", "https://www.brown.edu",
        "https://www.dartmouth.edu", "https://www.vanderbilt.edu", "https://www.rice.edu",
        "https://www.wustl.edu", "https://www.georgetown.edu", "https://www.nd.edu",
        "https://www.emory.edu", "https://www.usc.edu", "https://www.ucla.edu",
        "https://www.ucsd.edu", "https://www.ucsb.edu", "https://www.ucdavis.edu",
        "https://www.uci.edu", "https://www.ucr.edu", "https://www.ucsc.edu",
        "https://www.umn.edu", "https://www.wisc.edu", "https://www.uiuc.edu",
        "https://www.umich.edu", "https://www.osu.edu", "https://www.psu.edu",
        "https://www.purdue.edu", "https://www.indiana.edu", "https://www.uiowa.edu",
        "https://www.washington.edu", "https://www.oregonstate.edu", "https://www.colorado.edu",
        "https://www.arizona.edu", "https://www.asu.edu", "https://www.utah.edu",
        "https://www.unm.edu", "https://www.tamu.edu", "https://www.utexas.edu",
        "https://www.uh.edu", "https://www.tulane.edu", "https://www.fsu.edu",
        "https://www.ufl.edu", "https://www.gatech.edu", "https://www.virginia.edu",
        "https://www.vt.edu", "https://www.wm.edu", "https://www.unc.edu",
        "https://www.ncsu.edu", "https://www.clemson.edu", "https://www.sc.edu",
        "https://www.uky.edu", "https://www.louisville.edu", "https://www.vanderbilt.edu",
        "https://www.tennessee.edu", "https://www.alabama.edu", "https://www.auburn.edu",
        "https://www.missouri.edu", "https://www.k-state.edu", "https://www.ku.edu",
        "https://www.nebraska.edu", "https://www.okstate.edu", "https://www.ou.edu",
        "https://www.baylor.edu", "https://www.tcu.edu", "https://www.smu.edu",
        "https://www.rice.edu", "https://www.ttu.edu", "https://www.unt.edu",
        "https://www.utdallas.edu", "https://www.uta.edu", "https://www.utsa.edu",
        "https://www.utep.edu", "https://www.utrgv.edu", "https://www.utmb.edu",
        "https://www.mdanderson.org", "https://www.mayoclinic.org", "https://www.clevelandclinic.org",
        "https://www.hopkinsmedicine.org", "https://www.massgeneral.org", "https://www.brighamandwomens.org",
        "https://www.nih.gov", "https://www.cdc.gov", "https://www.fda.gov",
        "https://www.nasa.gov", "https://www.noaa.gov", "https://www.usgs.gov",
        "https://www.energy.gov", "https://www.state.gov", "https://www.defense.gov",
        "https://www.justice.gov", "https://www.treasury.gov", "https://www.commerce.gov",
        "https://www.ed.gov", "https://www.hhs.gov", "https://www.va.gov",
        "https://www.ssa.gov", "https://www.irs.gov", "https://www.uscis.gov",
        "https://www.fbi.gov", "https://www.cia.gov", "https://www.nsa.gov",
        "https://www.dhs.gov", "https://www.fema.gov", "https://www.usda.gov",
        "https://www.epa.gov", "https://www.osha.gov", "https://www.sec.gov",
        "https://www.federalreserve.gov", "https://www.whitehouse.gov", "https://www.congress.gov",
        "https://www.supremecourt.gov", "https://www.uscourts.gov", "https://www.usa.gov",
        "https://www.archives.gov", "https://www.loc.gov", "https://www.smithsonian.edu",
        "https://www.metmuseum.org", "https://www.moma.org", "https://www.guggenheim.org",
        "https://www.britishmuseum.org", "https://www.louvre.fr", "https://www.hermitagemuseum.org",
        "https://www.nga.gov", "https://www.getty.edu", "https://www.nga.gov",
    ]
    urls = list(dict.fromkeys(urls + curated))  # dedupe preserving order

    result = pd.DataFrame({
        "url": [u if u.startswith("http") else f"https://{u}" for u in urls],
        "label": 0,
        "source": "BenignList",
    })
    result.to_csv(output_path, index=False)
    logger.info("Saved %d benign URLs to %s", len(result), output_path)
    return len(result)


def _seed_dataset() -> pd.DataFrame:
    """Minimal seed dataset for offline development when downloads fail."""
    phishing = [
        "http://secure-login-microsft.com/verify?id=983",
        "http://paypal-alert-confirm-id.net/account",
        "http://apple-id-locked-reset.support/login",
        "http://192.168.0.1/bank/login",
        "http://free-gift-bonus.xyz/claim",
        "http://account-verify-bank.com/signin",
        "http://microsoft-update-secure.tk/reset",
        "http://amazon-security-alert.click/verify",
    ]
    legit = [
        "https://github.com/openai/triton",
        "https://www.google.com",
        "https://www.python.org",
        "https://drive.google.com",
        "https://www.wikipedia.org",
        "https://stackoverflow.com/questions",
        "https://www.bbc.com/news",
        "https://docs.microsoft.com",
    ]
    rows = [{"url": u, "label": 1, "source": "Seed"} for u in phishing]
    rows += [{"url": u, "label": 0, "source": "Seed"} for u in legit]
    return pd.DataFrame(rows)


def download_all(raw_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Download all dataset sources and merge into a single raw DataFrame.

    Returns:
        Merged DataFrame with columns: url, label, source
    """
    raw_dir = raw_dir or RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    frames: list[pd.DataFrame] = []

    phiusiil_path = raw_dir / "phiusiil.csv"
    if download_phiusiil(phiusiil_path) > 0:
        frames.append(pd.read_csv(phiusiil_path))

    openphish_path = raw_dir / "openphish.csv"
    if download_openphish(openphish_path) > 0:
        frames.append(pd.read_csv(openphish_path))

    benign_path = raw_dir / "benign.csv"
    if download_benign_urls(benign_path) > 0:
        frames.append(pd.read_csv(benign_path))

    if not frames:
        logger.warning("All downloads failed; using seed dataset.")
        merged = _seed_dataset()
    else:
        merged = pd.concat(frames, ignore_index=True)

    merged_path = raw_dir / "merged_raw.csv"
    merged.to_csv(merged_path, index=False)
    logger.info("Merged dataset: %d URLs (%d phishing, %d legitimate)",
                len(merged), (merged["label"] == 1).sum(), (merged["label"] == 0).sum())
    return merged


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    download_all()
