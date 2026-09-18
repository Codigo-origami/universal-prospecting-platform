
"""
=============================================================================
Universal Prospecting Platform (V8.12 "The Enterprise Core - Ultimate")
=============================================================================
Description: Advanced B2B Lead Generation Tool.
             Features: True Atomic Transactions, Universal Schema Migrations, 
             Strict Domain Extraction, Safe SMTP State Handling, Hard Timeouts,
             Rich Conflict Logging, Accurate Discovery Analytics, Global 
             Recipient Suppression, and Administrative Safeguards.
             
Author:      Código Origami - Alejandro Moreno (YouTube)
Repository:  https://github.com/Codigo-origami
License:     MIT License
=============================================================================
"""

__author__ = "Codigo Origami"
__version__ = "8.12.0"

import os
import time
import random
import re
import datetime
import requests
import uuid
import sqlite3
import pandas as pd
import traceback
import hashlib
import json
import unicodedata
import math
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode, urljoin, unquote, quote_plus
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

st.set_page_config(page_title="Universal Prospector | Codigo Origami", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "origami_leads.db")
TEMPLATE_PATH = os.path.join(BASE_DIR, "template_en.html")

# ============================================================================
# 1. CORE UTILITIES & NORMALIZATION (Must precede DB init)
# ============================================================================

def normalize_address(address):
    if not address or address == "Not available": return ""
    norm = unicodedata.normalize("NFKC", str(address)).casefold()
    return "".join(ch for ch in norm if ch.isalnum() or ch.isspace()).strip()

def normalize_location(loc_string):
    if not loc_string: return "unknown"
    return "|".join([unicodedata.normalize("NFKC", p.strip()).casefold() for p in loc_string.split(',') if p.strip()])

def parse_weighted_keywords(kw_text):
    kws = []
    for line in re.split(r'[\n,]+', kw_text):
        line = line.strip()
        if not line: continue
        weight = 10
        if ':' in line:
            parts = line.rsplit(':', 1)
            try: weight = max(1, min(int(parts[1].strip()), 30)); word_part = parts[0].strip().lower()
            except Exception: word_part = line.lower()
        else: word_part = line.lower()
        aliases = [alias.strip() for alias in word_part.split('|') if alias.strip()]
        if aliases: kws.append({"aliases": aliases, "weight": weight})
    return kws

def parse_flat_keywords(kw_text):
    kws = []
    for line in re.split(r'[\n,]+', kw_text):
        line = line.strip().lower()
        if not line: continue
        aliases = [alias.strip() for alias in line.split('|') if alias.strip()]
        if aliases: kws.append(aliases)
    return kws

def get_icp_hash(req_kws, strong_kws, bonus_kws, excl_kws):
    icp_state = {"req": req_kws, "strong": strong_kws, "bonus": bonus_kws, "excl": excl_kws}
    icp_str = json.dumps(icp_state, sort_keys=True)
    return hashlib.sha256(icp_str.encode()).hexdigest()[:12]

def is_social_domain(hostname, domain):
    hostname = (hostname or "").lower().rstrip(".")
    return hostname == domain or hostname.endswith("." + domain)

def email_matches_domain(email, domain):
    if not email or not domain: return False
    try:
        email_domain = email.rsplit("@", 1)[1].lower().rstrip(".")
        return email_domain == domain.lower().rstrip(".")
    except Exception: return False

def clean_url(url):
    if not url or url == "Not available": return "Not available"
    try:
        parts = urlsplit(url)
        params = dict(parse_qsl(parts.query, keep_blank_values=True))
        if 'google.' in parts.netloc or 'duckduckgo.' in parts.netloc or 'bing.' in parts.netloc:
            if "uddg" in params: return unquote(params["uddg"])
            if "q" in params: 
                candidate = unquote(params["q"])
                if candidate.startswith(("http://", "https://")): return candidate
        return url
    except Exception: return url

def normalize_company_name(name):
    if not name or name == "Unknown": return ""
    s = name.casefold().strip()
    s = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in s)
    s = re.sub(r"\b(ltd|limited|llc|inc|corp|corporation|co|company|gmbh|sa|sas|sl)\b", " ", s, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s).strip()

def normalize_domain(url):
    if not url or url == "Not available": return ""
    if not url.startswith("http"): url = "http://" + url
    try:
        domain = urlsplit(url).hostname
        if domain:
            domain = domain.lower()
            if domain.startswith("www."): domain = domain[4:]
            SOCIAL_DOMAINS = {"facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com"}
            if any(is_social_domain(domain, social) for social in SOCIAL_DOMAINS):
                return ""
            return domain
    except Exception: pass
    return ""

def normalize_phone(phone):
    if not phone or phone == "Not available": return "Not available"
    cleaned = re.sub(r"[^\d\+]", "", phone)
    return cleaned if cleaned else "Not available"

def extract_place_id(url):
    match = re.search(r'!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)', url)
    return match.group(1) if match else "Unknown"

def add_hl_param(url, hl="en"):
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["hl"] = hl
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

def is_valid_email(email):
    if not email or '@' not in email or '.' not in email.split('@')[-1]: return False
    email = email.lower()
    false_positives = ['duckduckgo', 'sentry', 'wixpress', 'godaddy', 'schema', 'example', 'polyfill', 'github', '.png', '.jpg', '.jpeg', '.gif', 'mysite.com', 'domain.com']
    if any(fp in email for fp in false_positives): return False
    if re.search(r'\.[0-9]+$', email): return False
    if re.search(r'@[0-9-]+\.[a-z0-9-.]+$', email): return False
    return True

def decode_cfemail(encoded):
    try:
        r = int(encoded[:2], 16)
        return ''.join(chr(int(encoded[i:i+2], 16) ^ r) for i in range(2, len(encoded), 2))
    except Exception: return ""

def get_best_email(emails):
    if not emails: return "Not available"
    best_email = emails[0]
    best_score = -100
    for e in emails:
        score = 0
        e_lower = e.lower()
        if e_lower.startswith('purchasing@') or e_lower.startswith('procurement@'): score += 40
        elif e_lower.startswith('sales@') or e_lower.startswith('marketing@'): score += 25
        elif e_lower.startswith('info@') or e_lower.startswith('contact@'): score += 15
        if 'privacy' in e_lower: score -= 30
        if 'support' in e_lower: score -= 10
        if score > best_score:
            best_score = score
            best_email = e
    return best_email

# --- STRICT IDENTITY ALIASING ---
def generate_identity_aliases(maps_id, domain, phone, norm_name, norm_address):
    aliases = []
    if maps_id and maps_id != "Unknown": aliases.append(f"maps:{maps_id}")
    if domain and norm_address: aliases.append(f"dom_addr:{domain}|{norm_address}")
    if phone and phone != "Not available" and norm_address: aliases.append(f"ph_addr:{phone}|{norm_address}")
    if norm_name and norm_address: aliases.append(f"name_addr:{norm_name}|{norm_address}")
    return list(set(aliases))

def resolve_lead_identity(db_conn, aliases):
    if not aliases: return None, "NO_IDENTITY", []
    
    cur = db_conn.cursor()
    placeholders = ', '.join(['?'] * len(aliases))
    cur.execute(f"SELECT DISTINCT lead_id FROM lead_identity_aliases WHERE alias_key IN ({placeholders})", tuple(aliases))
    results = [row[0] for row in cur.fetchall()]
    
    if len(results) == 1:
        return results[0], "EXISTING", []
    elif len(results) > 1:
        return None, "IDENTITY_CONFLICT", results
    
    return f"ORI-{str(uuid.uuid4())[:8].upper()}", "NEW", []

def log_identity_conflict(db_conn, run_id, aliases, conflict_ids, company_name, maps_id, domain, phone, address):
    conflict_id = f"CONF-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    id_1 = conflict_ids[0] if len(conflict_ids) > 0 else "UNKNOWN"
    id_2 = conflict_ids[1] if len(conflict_ids) > 1 else "UNKNOWN"
    
    db_conn.execute("""
        INSERT INTO identity_conflicts 
        (conflict_id, run_id, alias_key, lead_id_1, lead_id_2, company_name, maps_id, domain, phone, address, detected_at, resolution_status) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (conflict_id, run_id, json.dumps(aliases), id_1, id_2, company_name, maps_id, domain, phone, address, now, "PENDING"))

# ============================================================================
# 2. DATABASE LAYER
# ============================================================================

def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=15)
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def add_column_if_missing(conn, table, column, column_type):
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

def ensure_db_schema():
    with get_db() as conn:
        conn.execute("PRAGMA journal_mode=WAL") 
        
        # Base Tables Creation
        conn.execute('''CREATE TABLE IF NOT EXISTS leads (lead_id TEXT PRIMARY KEY)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS lead_identity_aliases (alias_key TEXT PRIMARY KEY, lead_id TEXT NOT NULL, FOREIGN KEY(lead_id) REFERENCES leads(lead_id) ON DELETE CASCADE)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS identity_conflicts (conflict_id TEXT PRIMARY KEY)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS global_recipient_locks (recipient TEXT PRIMARY KEY)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS recipient_history (recipient TEXT PRIMARY KEY)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS lead_discoveries (run_id TEXT, lead_id TEXT, query TEXT, location TEXT, PRIMARY KEY (run_id, lead_id, query, location), FOREIGN KEY(lead_id) REFERENCES leads(lead_id) ON DELETE CASCADE)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS activities (activity_id TEXT PRIMARY KEY, lead_id TEXT, FOREIGN KEY(lead_id) REFERENCES leads(lead_id) ON DELETE CASCADE)''')
        
        # Universal Schema Migration
        lead_cols = [
            ("created_at", "TEXT"), ("last_seen_at", "TEXT"), ("enriched_at", "TEXT"), ("last_attempted_at", "TEXT"), 
            ("last_contacted_at", "TEXT"), ("status_updated_at", "TEXT"), ("lock_token", "TEXT"),
            ("maps_id", "TEXT"), ("maps_url", "TEXT"), ("domain", "TEXT"), ("norm_name", "TEXT"), 
            ("norm_address", "TEXT"), ("location", "TEXT"), ("query", "TEXT"), ("company", "TEXT"), 
            ("category", "TEXT"), ("address", "TEXT"), ("website", "TEXT"), ("phone", "TEXT"), 
            ("whatsapp", "TEXT"), ("email", "TEXT"), ("email_source", "TEXT"), ("email_source_url", "TEXT"),
            ("wa_link", "TEXT"), ("facebook", "TEXT"), ("instagram", "TEXT"), ("linkedin", "TEXT"), 
            ("contactability_score", "INTEGER"), ("icp_fit_score", "INTEGER"), ("priority_score", "INTEGER"), 
            ("matched_keywords", "TEXT"), ("qual_status", "TEXT"), ("priority_badge", "TEXT"), 
            ("status", "TEXT"), ("enrichment_level", "TEXT"), ("enrich_time", "TEXT"), ("icp_hash", "TEXT"),
            ("sources_searched", "TEXT"), ("sources_found", "TEXT"), ("debug_logs", "TEXT")
        ]
        for c, t in lead_cols: add_column_if_missing(conn, "leads", c, t)
            
        act_cols = [
            ("campaign_id", "TEXT"), ("lock_token", "TEXT"), ("type", "TEXT"), ("status", "TEXT"), 
            ("recipient", "TEXT"), ("sender", "TEXT"), ("subject", "TEXT"), ("attempted_at", "TEXT"), 
            ("sent_at", "TEXT"), ("error", "TEXT")
        ]
        for c, t in act_cols: add_column_if_missing(conn, "activities", c, t)
            
        conf_cols = [
            ("run_id", "TEXT"), ("alias_key", "TEXT"), ("lead_id_1", "TEXT"), ("lead_id_2", "TEXT"), 
            ("company_name", "TEXT"), ("maps_id", "TEXT"), ("domain", "TEXT"), ("phone", "TEXT"), 
            ("address", "TEXT"), ("detected_at", "TEXT"), ("resolution_status", "TEXT")
        ]
        for c, t in conf_cols: add_column_if_missing(conn, "identity_conflicts", c, t)
            
        lock_cols = [("locked_at", "TEXT"), ("campaign_id", "TEXT"), ("lock_token", "TEXT")]
        for c, t in lock_cols: add_column_if_missing(conn, "global_recipient_locks", c, t)
            
        hist_cols = [("first_contacted_at", "TEXT"), ("last_contacted_at", "TEXT"), ("last_campaign_id", "TEXT"), ("total_attempts", "INTEGER DEFAULT 0")]
        for c, t in hist_cols: add_column_if_missing(conn, "recipient_history", c, t)
            
        disc_cols = [("discovered_at", "TEXT")]
        for c, t in disc_cols: add_column_if_missing(conn, "lead_discoveries", c, t)

        # Indexes
        conn.execute('CREATE INDEX IF NOT EXISTS idx_maps_id ON leads(maps_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_priority_score ON leads(priority_score DESC)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_alias_lead_id ON lead_identity_aliases(lead_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_leads_qual ON leads(qual_status, priority_badge)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_activities_lead ON activities(lead_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_activities_camp ON activities(campaign_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_activities_status ON activities(status)')

def init_db():
    ensure_db_schema()

def clear_db():
    """Atomic drop with concurrent active-sends check inside a BEGIN IMMEDIATE lock."""
    with get_db() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM global_recipient_locks")
            if cur.fetchone()[0] > 0: 
                conn.rollback()
                return False
                
            cur.execute("SELECT COUNT(*) FROM leads WHERE status='Sending...'")
            if cur.fetchone()[0] > 0: 
                conn.rollback()
                return False
                
            tables = [
                "activities", "lead_discoveries", "lead_identity_aliases", 
                "global_recipient_locks", "identity_conflicts", "recipient_history", "leads"
            ]
            for table in tables:
                conn.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
            
    ensure_db_schema()
    return True

init_db()

def load_leads():
    with get_db() as conn:
        return pd.read_sql("SELECT * FROM leads ORDER BY priority_score DESC", conn)

def get_campaign_candidates(target_qualities, limit, skipped_ids=None):
    if not target_qualities: return pd.DataFrame()
    skipped_ids = skipped_ids or []
    
    with get_db() as conn:
        placeholders = ','.join(['?']*len(target_qualities))
        query = f"""
            SELECT lead_id, email, company, qual_status, priority_badge, status 
            FROM leads 
            WHERE qual_status='QUALIFIED' 
            AND priority_badge IN ({placeholders}) 
            AND email IS NOT NULL AND email != 'Not available' 
            AND status NOT IN ('Contacted', 'Do Not Contact', 'Replied', 'Not Interested', 'Recipient rejected', 'Sender rejected', 'Excluded', 'Not ICP', 'Sending...', 'Send outcome unknown', 'Invalid Email')
        """
        params = list(target_qualities)
        if skipped_ids:
            skip_placeholders = ','.join(['?']*len(skipped_ids))
            query += f" AND lead_id NOT IN ({skip_placeholders})"
            params.extend(skipped_ids)
            
        query += " ORDER BY priority_score DESC LIMIT ?"
        params.append(limit)
        
        return pd.read_sql(query, conn, params=tuple(params))

def upsert_lead_transaction(db_conn, lead_dict, aliases, discovery_dict):
    try:
        db_conn.execute("BEGIN IMMEDIATE")
        lead_id, id_status, conflict_ids = resolve_lead_identity(db_conn, aliases)
        
        if not lead_id: 
            if id_status == "IDENTITY_CONFLICT":
                log_identity_conflict(db_conn, discovery_dict['run_id'], aliases, conflict_ids, lead_dict['company'], lead_dict.get('maps_id'), lead_dict.get('domain'), lead_dict.get('phone'), lead_dict.get('address'))
            db_conn.commit()
            return f"Skipped: {id_status}"
            
        lead_dict['lead_id'] = lead_id
        cur = db_conn.cursor()
        
        cols = list(lead_dict.keys())
        placeholders = ', '.join(['?'] * len(cols))
        col_names = ', '.join(cols)
        
        update_clauses = []
        for col in cols:
            # created_at is ignored on update, preserving the original discovery time
            if col in ['lead_id', 'created_at']: continue
            elif col == 'status':
                # Protect hard terminal states & active locks
                update_clauses.append(f"{col} = CASE WHEN leads.status IN ('Contacted', 'Replied', 'Not Interested', 'Do Not Contact', 'Excluded', 'Sending...', 'Send outcome unknown') THEN leads.status ELSE excluded.{col} END")
            elif col in ['enriched_at', 'last_seen_at', 'last_contacted_at', 'last_attempted_at', 'status_updated_at']:
                 update_clauses.append(f"{col} = COALESCE(excluded.{col}, leads.{col})")
            else:
                update_clauses.append(f"{col} = excluded.{col}")
                
        update_clause_str = ',\n        '.join(update_clauses)
        
        query = f"""
        INSERT INTO leads ({col_names})
        VALUES ({placeholders})
        ON CONFLICT(lead_id) DO UPDATE SET
        {update_clause_str}
        """
        cur.execute(query, tuple(lead_dict[col] for col in cols))
        
        # Insert aliases AFTER the lead is safely upserted to respect FK
        for alias in aliases:
            cur.execute("SELECT lead_id FROM lead_identity_aliases WHERE alias_key=?", (alias,))
            existing = cur.fetchone()
            if existing and existing[0] != lead_id:
                raise ValueError(f"Identity collision: Alias {alias} belongs to {existing[0]}, attempted on {lead_id}")
            cur.execute("INSERT OR IGNORE INTO lead_identity_aliases (alias_key, lead_id) VALUES (?, ?)", (alias, lead_id))
            
        discovery_dict['lead_id'] = lead_id
        cur.execute('''INSERT OR IGNORE INTO lead_discoveries 
                       (run_id, lead_id, query, location, discovered_at) 
                       VALUES (?, ?, ?, ?, ?)''', 
                    (discovery_dict['run_id'], discovery_dict['lead_id'], discovery_dict['query'], 
                     discovery_dict['location'], discovery_dict['discovered_at']))
                     
        db_conn.commit()
        return "Processed"
    except Exception as e:
        db_conn.rollback()
        raise e

def lock_lead_and_create_activity(lead_id, campaign_id, recipient, sender, subject):
    with get_db() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.cursor()
            
            cur.execute("SELECT 1 FROM global_recipient_locks WHERE recipient=?", (recipient,))
            if cur.fetchone(): 
                conn.commit()
                return None 
                
            cur.execute("SELECT first_contacted_at FROM recipient_history WHERE recipient=?", (recipient,))
            row = cur.fetchone()
            if row and row[0]:
                conn.commit()
                return None
                
            lock_token = uuid.uuid4().hex
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Record last_attempted_at at the start of the lock to accurately track attempt timestamps
            cur.execute("""
                UPDATE leads 
                SET status='Sending...', status_updated_at=?, last_attempted_at=?, lock_token=? 
                WHERE lead_id=? AND status NOT IN ('Contacted', 'Do Not Contact', 'Replied', 'Not Interested', 'Recipient rejected', 'Sender rejected', 'Excluded', 'Not ICP', 'Sending...', 'Send outcome unknown', 'Invalid Email')
            """, (now, now, lock_token, lead_id))
            
            if cur.rowcount == 0: 
                conn.commit()
                return None
                
            cur.execute("INSERT INTO global_recipient_locks (recipient, locked_at, campaign_id, lock_token) VALUES (?, ?, ?, ?)", (recipient, now, campaign_id, lock_token))
            
            # total_attempts = number of times the system initiated contact (concurrency & preflight intents)
            cur.execute("INSERT OR IGNORE INTO recipient_history (recipient, total_attempts) VALUES (?, 0)", (recipient,))
            cur.execute("UPDATE recipient_history SET total_attempts = total_attempts + 1, last_campaign_id=? WHERE recipient=?", (campaign_id, recipient))
            
            activity_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
            cur.execute('''INSERT INTO activities 
                (activity_id, lead_id, campaign_id, lock_token, type, status, recipient, sender, subject, attempted_at, error) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (activity_id, lead_id, campaign_id, lock_token, "Email", "Attempting", recipient, sender, subject, now, ""))
            
            cur.execute("SELECT email, qual_status, priority_badge, status, company FROM leads WHERE lead_id=? AND lock_token=?", (lead_id, lock_token))
            row = cur.fetchone()
            conn.commit()
            
            if not row: return None
            return {
                "email": row[0], "qual_status": row[1], "priority_badge": row[2], 
                "status": row[3], "company": row[4], "lock_token": lock_token,
                "activity_id": activity_id
            }
        except Exception:
            conn.rollback()
            raise

def update_activity_and_lead(activity_id, lead_id, act_status, lead_status, lock_token, error_msg="", recipient=None):
    with get_db() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.cursor()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            time_updates = "status_updated_at=?, lock_token=NULL"
            lead_params = [lead_status, now]
            if act_status == "Contacted":
                time_updates += ", last_contacted_at=?"
                lead_params.append(now)
                
            lead_params.extend([lead_id, lock_token])
            cur.execute(f"UPDATE leads SET status=?, {time_updates} WHERE lead_id=? AND lock_token=? AND status='Sending...'", tuple(lead_params))
            
            if cur.rowcount != 1:
                raise RuntimeError(f"Lost send lock for lead {lead_id} (Token: {lock_token}). Update aborted to protect DB integrity.")
            
            sent_update = ", sent_at=?" if act_status == "Contacted" else ""
            act_params = [act_status, error_msg]
            if act_status == "Contacted": act_params.append(now)
            act_params.append(activity_id)
            cur.execute(f"UPDATE activities SET status=?, error=?{sent_update} WHERE activity_id=?", tuple(act_params))
            
            if recipient:
                if act_status == "Contacted":
                    cur.execute("UPDATE recipient_history SET first_contacted_at = COALESCE(first_contacted_at, ?), last_contacted_at = ? WHERE recipient = ?", (now, now, recipient))
                cur.execute("DELETE FROM global_recipient_locks WHERE recipient=? AND lock_token=?", (recipient, lock_token))
            
            conn.commit()
        except Exception:
            conn.rollback()
            raise

def release_send_lock(lead_id, lock_token, recipient, activity_id=None, status="Ready to Contact"):
    with get_db() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("""
                UPDATE leads 
                SET status=?, status_updated_at=?, lock_token=NULL 
                WHERE lead_id=? AND lock_token=? AND status='Sending...'
            """, (status, now, lead_id, lock_token))
            conn.execute("DELETE FROM global_recipient_locks WHERE recipient=? AND lock_token=?", (recipient, lock_token))
            
            if activity_id:
                conn.execute("UPDATE activities SET status='Aborted', error='Pre-flight validation failed' WHERE activity_id=? AND lock_token=?", (activity_id, lock_token))
            conn.commit()
        except Exception:
            conn.rollback()
            raise

def reset_stuck_sends():
    with get_db() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            time_limit = (datetime.datetime.now() - datetime.timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
            cur = conn.cursor()
            
            cur.execute("SELECT lead_id, lock_token FROM leads WHERE status='Sending...' AND status_updated_at < ? AND lock_token IS NOT NULL", (time_limit,))
            stuck = cur.fetchall()
            
            if not stuck: 
                conn.commit()
                return 0, 0
            
            tokens = [t[1] for t in stuck]
            placeholders = ','.join(['?'] * len(tokens))
            
            cur.execute(f"UPDATE activities SET status='Unknown', error='Recovered after stale send timeout' WHERE status='Attempting' AND lock_token IN ({placeholders}) AND attempted_at < ?", tuple(tokens) + (time_limit,))
            act_count = cur.rowcount
            
            cur.execute(f"DELETE FROM global_recipient_locks WHERE lock_token IN ({placeholders})", tuple(tokens))
            
            cur.execute(f"UPDATE leads SET status='Send outcome unknown', status_updated_at=datetime('now','localtime'), lock_token=NULL WHERE status='Sending...' AND lock_token IN ({placeholders}) AND status_updated_at < ?", tuple(tokens) + (time_limit,))
            lead_count = cur.rowcount
                
            conn.commit()
            return lead_count, act_count
        except Exception:
            conn.rollback()
            raise

# ============================================================================
# 3. HIGH-SIGNAL EXTRACTION & ENRICHMENT
# ============================================================================

def fetch_with_retry(url, timeout=8, max_retries=3):
    headers = {'User-Agent': 'Mozilla/5.0'}
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers=headers, timeout=timeout)
            if res.status_code in [429, 500, 502, 503, 504]:
                time.sleep(1.5 * (attempt + 1))
                continue
            return res
        except requests.RequestException:
            if attempt == max_retries - 1: raise
            time.sleep(1.5 * (attempt + 1))
    return None

def get_high_signal_text(soup):
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
        tag.decompose()
    garbage_pattern = re.compile(r"cookie|privacy|terms|login|menu", re.I)
    for tag in soup.find_all(attrs={"class": garbage_pattern}): tag.decompose()
    for tag in soup.find_all(attrs={"id": garbage_pattern}): tag.decompose()

    parts = []
    if soup.title and soup.title.string: parts.append(soup.title.string)
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'): parts.append(meta_desc['content'])
    for tag in ['h1', 'h2', 'h3']:
        for el in soup.find_all(tag):
            parts.append(el.get_text(separator=' ', strip=True))
            
    body_text = soup.get_text(separator=' ', strip=True)
    signal_body = body_text[:1000] + " " + body_text[-500:] if len(body_text) > 1500 else body_text
    parts.append(signal_body)
    return " ".join(parts).lower()

def extract_social_links(soup):
    fb, ig, li = "Not available", "Not available", "Not available"
    BAD_PATHS = {'/sharer', '/share', '/dialog', '/oauth', '/login'}
    for a in soup.find_all('a', href=True):
        try:
            href = a['href']
            parsed = urlsplit(href.lower())
            hostname = parsed.hostname
            path = parsed.path.rstrip("/")
            
            if any(path == bad or path.startswith(bad + "/") for bad in BAD_PATHS): continue
            
            if is_social_domain(hostname, "facebook.com") and fb == "Not available": fb = href
            if is_social_domain(hostname, "instagram.com") and ig == "Not available": ig = href
            if is_social_domain(hostname, "linkedin.com") and li == "Not available": li = href
        except Exception: pass
    return clean_url(fb), clean_url(ig), clean_url(li)

def extract_contacts_from_html(html_text, source_url):
    email, wa, wa_link = "Not available", "Not available", "Not available"
    link_soup = BeautifulSoup(html_text, 'html.parser')
    fb, ig, li = extract_social_links(link_soup)
    
    found_emails = []
    for tag in link_soup.select('[data-cfemail]'):
        e = decode_cfemail(tag['data-cfemail'])
        if is_valid_email(e): found_emails.append(e)
    for a in link_soup.select('a[href^="mailto:"]'):
        e = a['href'].replace('mailto:', '').split('?')[0].strip()
        if is_valid_email(e): found_emails.append(e)
        
    raw_emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', html_text)
    found_emails.extend([e for e in raw_emails if is_valid_email(e)])
    if found_emails: email = get_best_email(list(set(found_emails)))
        
    for a in link_soup.find_all('a', href=True):
        href = a['href'].lower()
        if 'wa.me/' in href or 'api.whatsapp.com/send' in href or 'whatsapp://send' in href:
            parsed_url = urlsplit(href)
            query_params = dict(parse_qsl(parsed_url.query))
            phone_param = query_params.get('phone', '')
            if phone_param: wa_cand = normalize_phone(phone_param)
            else:
                m = re.search(r'(?:wa\.me/)(\+?\d+)', href)
                wa_cand = normalize_phone(m.group(1)) if m else "Not available"
            if wa_cand != "Not available": 
                wa, wa_link = wa_cand, a['href']
                break
            
    if wa == "Not available":
        m = re.search(r'(?:whatsapp|📱)\s*[\:\-]?\s*(\+?[\d\s\-\(\)]{8,20})', link_soup.get_text(separator=' '), re.IGNORECASE)
        if m:
            clean_num = normalize_phone(m.group(1))
            if clean_num != "Not available": wa = clean_num
            
    signal_soup = BeautifulSoup(html_text, 'html.parser')
    high_signal_site_text = get_high_signal_text(signal_soup)
            
    return email, wa, wa_link, fb, ig, li, high_signal_site_text

def extract_contacts_from_url(url, timeout_sec=8):
    url = clean_url(url)
    if url == "Not available" or not url.startswith("http"): 
        return "Not available", "Not available", "Not available", "Not available", "Not available", "Not available", "", "Invalid URL"
    try:
        res = fetch_with_retry(url, timeout=timeout_sec)
        if not res or not res.ok or "text/html" not in res.headers.get("Content-Type", "").lower(): 
            return "Not available", "Not available", "Not available", "Not available", "Not available", "Not available", "", f"HTTP Error"
        email, wa, wa_link, fb, ig, li, hst = extract_contacts_from_html(res.text.replace('[at]', '@').replace('(at)', '@'), url)
        return email, wa, wa_link, fb, ig, li, hst, "Success"
    except requests.Timeout: 
        return "Not available", "Not available", "Not available", "Not available", "Not available", "Not available", "", "Timeout"
    except Exception as e: 
        return "Not available", "Not available", "Not available", "Not available", "Not available", "Not available", "", f"Error: {type(e).__name__}"

def search_contact_pages(base_url):
    routes = ['/contact', '/contact-us', '/contacto', '/kontakt', '/about', '/services', '/products']
    found_emails = []
    e_source_url, wa_final, wa_link_final = "Not available", "Not available", "Not available"
    fb_final, ig_final, li_final = "Not available", "Not available", "Not available"
    compiled_text = ""
    log_errors = []
    
    for route in routes:
        try:
            full_url = urljoin(base_url, route)
            res = fetch_with_retry(full_url, timeout=5)
            if not res or not res.ok or "text/html" not in res.headers.get("Content-Type", "").lower(): continue
            email, wa, wa_link, fb, ig, li, page_text = extract_contacts_from_html(res.text.replace('[at]', '@').replace('(at)', '@'), full_url)
            compiled_text += " " + page_text
            
            if email != "Not available": 
                found_emails.append(email)
                if e_source_url == "Not available": e_source_url = full_url
            if wa != "Not available" and wa_final == "Not available": wa_final, wa_link_final = wa, wa_link
            if fb != "Not available" and fb_final == "Not available": fb_final = fb
            if ig != "Not available" and ig_final == "Not available": ig_final = ig
            if li != "Not available" and li_final == "Not available": li_final = li
        except Exception as e:
            log_errors.append(f"{route}: {type(e).__name__}")
            continue
            
    return get_best_email(list(set(found_emails))), e_source_url, wa_final, wa_link_final, fb_final, ig_final, li_final, compiled_text, "; ".join(log_errors)

def search_social_media_clean(company_name, country):
    time.sleep(random.uniform(1, 2))
    BAD_PATHS = {'/sharer', '/share', '/dialog', '/oauth', '/login'}
    try:
        url = "https://lite.duckduckgo.com/lite/"
        data = {'q': f'"{company_name}" {country} facebook OR instagram OR linkedin'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.post(url, data=data, headers=headers, timeout=8)
        if not res.ok: return {}
        soup = BeautifulSoup(res.text, 'html.parser')
        
        found_social = {"facebook": "Not available", "instagram": "Not available", "linkedin": "Not available"}
        for a in soup.find_all('a', href=True):
            href = clean_url(a['href'])
            parsed = urlsplit(href.lower())
            
            if 'duckduckgo' in parsed.netloc: continue
            
            path = parsed.path.rstrip("/")
            if any(path == bad or path.startswith(bad + "/") for bad in BAD_PATHS): continue
            
            if is_social_domain(parsed.hostname, "facebook.com") and found_social["facebook"] == "Not available": found_social["facebook"] = href
            elif is_social_domain(parsed.hostname, "instagram.com") and found_social["instagram"] == "Not available": found_social["instagram"] = href
            elif is_social_domain(parsed.hostname, "linkedin.com") and found_social["linkedin"] == "Not available": found_social["linkedin"] = href
        return found_social
    except Exception: return {}

def hunt_email_internet(company_name, country, domain=""):
    time.sleep(random.uniform(1, 2))
    try:
        url = "https://lite.duckduckgo.com/lite/"
        data = {'q': f'"{company_name}" {country} email "@"'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.post(url, data=data, headers=headers, timeout=8)
        if not res.ok: return "Not available", "Not available"
        emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', res.text)
        valid_emails = [e for e in emails if is_valid_email(e)]
        
        soup = BeautifulSoup(res.text, 'html.parser')
        source_url = "Search Result"
        for a in soup.find_all('a', href=True):
            href = clean_url(a['href'])
            if 'duckduckgo' not in href and domain and domain != "Not available":
                candidate_domain = normalize_domain(href)
                if candidate_domain == domain or candidate_domain.endswith("." + domain):
                    source_url = href
                    break
        
        if domain and domain != "Not available":
            domain_filtered = [e for e in valid_emails if email_matches_domain(e, domain)]
            if domain_filtered: return get_best_email(domain_filtered), source_url
            
        return "Not available", "Not available" 
    except Exception: return "Not available", "Not available"

# ============================================================================
# 4. EMAIL AUTOMATION FUNCTIONS (SMTP)
# ============================================================================

def connect_smtp(sender_email, sender_password):
    # Hard 60-second SMTP timeout keeps the send operation well below 
    # the stale-lock recovery window under normal execution.
    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=60)
    server.starttls()
    server.login(sender_email, sender_password)
    return server

def send_single_email(srv, sender_email, sender_password, receiver, email_subject, company_name, html_template):
    personalized_html = html_template.replace("[Company Name]", str(company_name))
    soup_plain = BeautifulSoup(personalized_html, "html.parser")
    for tag in soup_plain(["style", "script"]): tag.decompose()
    
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = receiver
    msg["Subject"] = email_subject
    msg.attach(MIMEText(soup_plain.get_text(separator="\n").strip(), "plain"))
    msg.attach(MIMEText(personalized_html, "html"))
    
    try:
        srv.send_message(msg)
        return True, "Contacted", srv
    except smtplib.SMTPRecipientsRefused: 
        return False, "Recipient rejected", srv
    except smtplib.SMTPSenderRefused: 
        return False, "Sender rejected", srv
    except Exception: 
        # If we cannot prove it was explicitly rejected before acceptance, treat as unknown
        return False, "Send outcome unknown", srv

# ============================================================================
# 5. ARCHITECTURE LOGIC: ICP GATING, SCORING & CONTEXTUAL NEGATION
# ============================================================================

def check_keyword_match(text, aliases):
    negated_found = None
    sentences = re.split(r'[.!?;]', text)
    negation_words = {"not", "no", "don't", "never", "without", "sin", "ningun", "ningún", "ninguna"}
    
    for sentence in sentences:
        for alias in aliases:
            for match in re.finditer(r'\b' + re.escape(alias) + r'\b', sentence):
                tokens_before = re.findall(r"\b[\w'-]+\b", sentence[:match.start()].lower())
                window_tokens = set(tokens_before[-5:])
                if not window_tokens.intersection(negation_words):
                    return True, alias, False
                else:
                    negated_found = alias
    if negated_found: return False, negated_found, True
    return False, None, False

def get_dual_score(biz_text, email, phone, whatsapp, wa_link_direct, website, req_kws, strong_kws, bonus_kws, exclude_kws):
    for kw_group in exclude_kws:
        matched, alias, negated = check_keyword_match(biz_text, kw_group)
        if matched: return 0, 0, 0, "❌ EXCLUDED", f"[EXC] {alias}", "EXCLUDED", True

    matched_words = []
    if req_kws:
        for req_group in req_kws:
            matched, alias, negated = check_keyword_match(biz_text, req_group)
            if matched: matched_words.append(f"[REQ] {alias}")
            else:
                if negated: matched_words.append(f"[NEGATED REQ] {alias}")
                return 0, 0, 0, "❌ NOT ICP", "Failed Required Gate", "NOT_ICP", False

    contactability_score = 0
    if email != "Not available": contactability_score += 20
    if phone != "Not available" or whatsapp != "Not available" or wa_link_direct != "Not available": contactability_score += 10
    if website != "Not available": contactability_score += 10

    icp_fit_raw = 0
    for kw_dict in strong_kws:
        matched, alias, negated = check_keyword_match(biz_text, kw_dict['aliases'])
        if matched:
            icp_fit_raw += kw_dict['weight']
            matched_words.append(f"[STR] {alias}")
        elif negated: matched_words.append(f"[NEGATED STR] {alias}")

    for kw_dict in bonus_kws:
        matched, alias, negated = check_keyword_match(biz_text, kw_dict['aliases'])
        if matched:
            icp_fit_raw += kw_dict['weight']
            matched_words.append(f"[BON] {alias}")
        elif negated: matched_words.append(f"[NEGATED BON] {alias}")

    icp_fit_score = min(60, icp_fit_raw)
    priority_score = contactability_score + icp_fit_score
    evidence_str = ", ".join(matched_words) if matched_words else "None"
    
    if priority_score >= 80: badge = "🔥 EXCELLENT"
    elif priority_score >= 50: badge = "🟢 GOOD"
    elif priority_score >= 30: badge = "🟡 NORMAL"
    else: badge = "🔴 LOW"
        
    return contactability_score, icp_fit_score, priority_score, badge, evidence_str, "QUALIFIED", False

# ============================================================================
# 6. USER INTERFACE
# ============================================================================

st.markdown("""
<style>
    .main { background-color: #FFFFFF; color: #31333F; }
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif !important; color: #0093A3; }
    .stButton>button { background-color: #00E5FF !important; color: #000 !important; font-weight: bold; width: 100%; border:none; }
    .stButton>button:hover { background-color: #00B8CC !important; }
    div[data-testid="metric-container"] { background-color: #F0F2F6; border-radius: 8px; padding: 10px; border-left: 4px solid #0093A3; box-shadow: 0 2px 4px rgba(0,0,0,0.1); color: #31333F;}
</style>
""", unsafe_allow_html=True)

# Replace the text below with your Base64 encoded image string
LOGO_B64 = "data:image/jpeg;base64,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"
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image(LOGO_B64, width=80)
with col_title:
    st.title("Universal Prospecting Platform")
    st.markdown("Developed by Codigo Origami | Pipeline Architecture V8.12")

tab_discover, tab_qualify, tab_prospect = st.tabs(["🔎 1. DISCOVER", "🧠 2. QUALIFY", "🎯 3. PROSPECT"])

# ---------------------------------------------------------
# TAB 1: DISCOVER (Ideal Customer Profile)
# ---------------------------------------------------------
with tab_discover:
    st.markdown("### 🎯 Define your Ideal Customer Profile (ICP)")

    col_icp1, col_icp2 = st.columns(2)
    with col_icp1:
        st.markdown("#### Discovery Parameters")
        target_locations = st.text_area("Locations (City, Country):", "Santiago, Chile\nBogota, Colombia", height=80)
        base_keywords = st.text_area("Target Queries (Maps Search):", "used car dealer\nauto parts importer", height=80)
        max_results = st.selectbox("Max prospects per query:", [20, 50, 100, 200, 500], index=1)
        enrichment_mode = st.radio("Enrichment Mode:", ["⚡ FAST (Maps + Homepage)", "🧠 SMART (Deepen based on Uncertainty/Promise)", "🔬 DEEP (Always Full Enrichment)"], index=1)
        headless_mode = st.checkbox("Run browser headless (Background mode)", value=True)
        debug_mode = st.checkbox("🐞 Debug Mode (Log enrichment errors)")
        
    with col_icp2:
        st.markdown("#### ICP Qualification (Gate & Weighted Signals)")
        req_kws_input = st.text_area("Required GATE (Must have to pass. 1 condition per line. OR = |):", "importer | wholesale\nvehicles | cars | auto", height=80)
        st.caption("Each line acts as an AND condition. Words divided by '|' act as OR.")
        strong_kws_input = st.text_area("Strong Signals (Format: kw | alias : weight [1-30]):", "japanese | japan: 25\nused | second hand: 20", height=60)
        bonus_kws_input = st.text_area("Bonus Signals (Format: kw : weight):", "b2b:10\ndealer:5", height=60)
        exclude_keywords = st.text_area("Absolute Exclusion (❌ EXCLUDED):", "rental, repair | mechanic, motorcycle", height=60)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 INITIATE PROSPECTING ENGINE"):
        locations = [l.strip() for l in target_locations.split("\n") if l.strip()]
        bases = [b.strip() for b in base_keywords.split("\n") if b.strip()]
        
        req_kws = parse_flat_keywords(req_kws_input)
        strong_kws = parse_weighted_keywords(strong_kws_input)
        bonus_kws = parse_weighted_keywords(bonus_kws_input)
        excludes = parse_flat_keywords(exclude_keywords)
        icp_hash = get_icp_hash(req_kws, strong_kws, bonus_kws, excludes)
        
        if not locations or not bases:
            st.error("❌ Please provide Location and Target Query.")
            st.stop()
            
        run_id = f"RUN-{uuid.uuid4().hex[:12].upper()}"
        
        est_scroll = (int(max_results / 5)) * 1.5
        est_enrich = max_results * (5 if "FAST" in enrichment_mode else (15 if "SMART" in enrichment_mode else 30))
        est_mins = int((est_scroll + est_enrich) * len(locations) * len(bases) / 60)
        st.info(f"⏳ Approximate runtime: ~{est_mins} minutes. Run ID: {run_id}")
        
        status_box = st.status("Initializing Prospecting Engine...", expanded=True)
        dropped_no_identity_count = 0
        
        with get_db() as db_conn:
            browser, context = None, None
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=headless_mode)
                    context = browser.new_context(locale="en-US")
                    page = context.new_page()
                    
                    for loc in locations:
                        norm_loc = normalize_location(loc)
                        for base in bases:
                            status_box.update(label=f"🔎 Searching '{base}' in '{loc}'...", state="running")
                            
                            query_enc = quote_plus(base)
                            loc_enc = quote_plus(loc)
                            search_url = add_hl_param(f"https://www.google.com/maps/search/{query_enc}+in+{loc_enc}")
                            
                            try:
                                page.goto(search_url, timeout=30000)
                                page.wait_for_selector('div[role="main"]', timeout=15000)
                                feed = page.locator('div[role="feed"]')
                                
                                if feed.count() > 0:
                                    prev_count, stalls = 0, 0
                                    max_scrolls = max(5, min(50, math.ceil(max_results / 5) + 5))
                                    for _ in range(max_scrolls): 
                                        feed.hover()
                                        page.mouse.wheel(0, 10000)
                                        page.wait_for_timeout(1000) 
                                        curr_count = page.locator('a[href*="/maps/place/"]').count()
                                        if curr_count >= max_results: break
                                        if curr_count == prev_count:
                                            stalls += 1
                                            if stalls >= 3: break
                                        else: stalls = 0
                                        prev_count = curr_count

                                cards = page.locator('a[href*="/maps/place/"]').element_handles()
                                raw_urls = [clean_url(t.get_attribute('href')) for t in cards]
                                company_urls = list(dict.fromkeys([u for u in raw_urls if u and u != "Not available" and '/reviews/' not in u and '/photos/' not in u]))[:max_results]
                                
                                status_box.write(f"✅ Found {len(company_urls)} raw prospects. Initiating enrichment...")
                                
                                for idx, url in enumerate(company_urls):
                                    start_time = time.time()
                                    sources_searched = ["Google Maps"]
                                    sources_found = []
                                    debug_logs = []
                                    
                                    maps_id = extract_place_id(url)
                                    maps_url = url
                                    
                                    company_name, category, address, phone, website = "Unknown", "Not available", "Not available", "Not available", "Not available"
                                    
                                    try:
                                        page.goto(add_hl_param(url), timeout=20000)
                                        page.wait_for_selector('h1', timeout=10000)
                                        company_name = page.locator('h1').first.inner_text()
                                    except Exception as e:
                                        debug_logs.append(f"Maps Load Error: {type(e).__name__}")
                                        continue
                                        
                                    try: category = page.locator('button[jsaction*="category"]').first.inner_text(timeout=1000)
                                    except Exception: pass
                                    
                                    try:
                                        loc_dir = page.locator('button[data-item-id^="address:"], button[aria-label*="Address"]').first
                                        address = loc_dir.get_attribute('aria-label').replace("Address: ", "").strip() if loc_dir.get_attribute('aria-label') else loc_dir.inner_text().replace("\n", ", ").strip() if loc_dir.count() > 0 else "Not available"
                                    except Exception: pass
                                    
                                    try: phone = normalize_phone(page.locator('[data-item-id^="phone:"]').first.inner_text(timeout=1000))
                                    except Exception: pass
                                    
                                    try: website = clean_url(page.locator('a[data-item-id^="authority:"], a[data-tooltip*="website"]').first.get_attribute('href', timeout=1000))
                                    except Exception: pass
                                    
                                    domain = normalize_domain(website)
                                    norm_name = normalize_company_name(company_name)
                                    norm_addr = normalize_address(address)
                                    
                                    identity_aliases = generate_identity_aliases(maps_id, domain, phone, norm_name, norm_addr)
                                    try:
                                        db_conn.execute("BEGIN IMMEDIATE")
                                        lead_id, id_status, conflict_ids = resolve_lead_identity(db_conn, identity_aliases)
                                        if not lead_id:
                                            if id_status == "IDENTITY_CONFLICT":
                                                log_identity_conflict(db_conn, run_id, identity_aliases, conflict_ids, company_name, maps_id, domain, phone, address)
                                                status_box.write(f"⚠️ {id_status} skipped: {company_name}")
                                            elif id_status == "NO_IDENTITY":
                                                dropped_no_identity_count += 1
                                            db_conn.commit()
                                            continue
                                            
                                        cur = db_conn.cursor()
                                        cur.execute("SELECT status, enriched_at, icp_hash FROM leads WHERE lead_id=?", (lead_id,))
                                        res = cur.fetchone()
                                        db_conn.commit() 
                                    except Exception as e:
                                        db_conn.rollback()
                                        status_box.write(f"⚠️ DB Error on Resolution: {type(e).__name__}")
                                        continue
                                    
                                    if res:
                                        status_val, enriched_at_val, saved_icp_hash = res[0], res[1], res[2]
                                        should_refresh = False
                                        
                                        hard_terminal = {"Contacted", "Replied", "Not Interested", "Do Not Contact", "Excluded", "Sending...", "Send outcome unknown"}
                                        is_terminal = status_val in hard_terminal
                                        
                                        if not enriched_at_val:
                                            should_refresh = True
                                        elif not is_terminal:
                                            try:
                                                last_enrich = datetime.datetime.strptime(enriched_at_val, "%Y-%m-%d %H:%M:%S")
                                                icp_changed = saved_icp_hash != icp_hash
                                                if (datetime.datetime.now() - last_enrich).days >= 30 or icp_changed:
                                                    should_refresh = True
                                            except Exception:
                                                should_refresh = True
                                                
                                        if not should_refresh:
                                            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            try:
                                                db_conn.execute("BEGIN IMMEDIATE")
                                                db_conn.execute("UPDATE leads SET last_seen_at = ?, location = ?, query = ? WHERE lead_id = ?", (now_str, norm_loc, base, lead_id))
                                                db_conn.execute("INSERT OR IGNORE INTO lead_discoveries (run_id, lead_id, query, location, discovered_at) VALUES (?, ?, ?, ?, ?)", (run_id, lead_id, base, loc, now_str))
                                                db_conn.commit()
                                            except Exception as e:
                                                db_conn.rollback()
                                                if debug_mode: status_box.write(f"⚠️ DB Error logging discovery for {company_name}: {type(e).__name__}")
                                            status_box.write(f"⏭️ Already known: {company_name} (recent data or terminal state)")
                                            continue
                                        else:
                                            status_box.write(f"🔄 Refreshing stale data/ICP for: {company_name} (Status: {status_val})")

                                    status_box.update(label=f"Enriching {idx+1}/{len(company_urls)}: {company_name}")
                                    
                                    email, whatsapp, wa_link_direct, fb, ig, li, email_source, email_source_url = "Not available", "Not available", "Not available", "Not available", "Not available", "Not available", "Not available", "Not available"
                                    website_context_text = ""
                                    
                                    # ⚡ FAST ENRICHMENT
                                    if website != "Not available":
                                        sources_searched.append("Website (Homepage)")
                                        email, whatsapp, wa_link_direct, fb, ig, li, website_context_text, err_msg = extract_contacts_from_url(website)
                                        if email != "Not available": email_source, email_source_url = "Website", website
                                        if err_msg != "Success": debug_logs.append(f"Homepage Error: {err_msg}")
                                    
                                    full_biz_text = f"{category} {company_name} {website_context_text}".lower()
                                    c_score, b_score, t_score, badge, evidence, qual_status, is_excl = get_dual_score(
                                        full_biz_text, email, phone, whatsapp, wa_link_direct, website, req_kws, strong_kws, bonus_kws, excludes
                                    )
                                    
                                    # 🧠 SMART ENRICHMENT LOGIC
                                    do_deep = False
                                    if "DEEP" in enrichment_mode: 
                                        do_deep = True
                                    elif "SMART" in enrichment_mode:
                                        if is_excl or qual_status == "NOT_ICP": 
                                            do_deep = False
                                        elif qual_status == "QUALIFIED" and (b_score >= 30 or (email == "Not available" and c_score < 20)): 
                                            do_deep = True
                                    
                                    applied_enrichment_level = "FAST"
                                    
                                    # 🔬 DEEP ENRICHMENT
                                    if do_deep:
                                        applied_enrichment_level = "DEEP"
                                        if website != "Not available" and email == "Not available":
                                            sources_searched.append("Website (Sub-pages)")
                                            e_ext, e_s_url, wa_ext, wa_link_ext, fb_ext, ig_ext, li_ext, deep_site_text, err_log = search_contact_pages(website)
                                            website_context_text += " " + deep_site_text
                                            if err_log: debug_logs.append(f"Sub-pages Error: {err_log}")
                                            if e_ext != "Not available": email, email_source, email_source_url = e_ext, "Website (Contact)", e_s_url
                                            if whatsapp == "Not available" and wa_ext != "Not available": whatsapp = wa_ext
                                            if wa_link_direct == "Not available" and wa_link_ext != "Not available": wa_link_direct = wa_link_ext
                                            if fb == "Not available" and fb_ext != "Not available": fb = fb_ext
                                            if ig == "Not available" and ig_ext != "Not available": ig = ig_ext
                                            if li == "Not available" and li_ext != "Not available": li = li_ext
                                        
                                        sources_searched.append("Social Search")    
                                        social_links = search_social_media_clean(company_name, loc)
                                        if social_links:
                                            target_social = next((social_links.get(k) for k in ["facebook", "linkedin", "instagram"] if social_links.get(k) != "Not available"), "Not available")
                                            
                                            if fb == "Not available" and social_links.get("facebook") != "Not available": fb = social_links["facebook"]
                                            if ig == "Not available" and social_links.get("instagram") != "Not available": ig = social_links["instagram"]
                                            if li == "Not available" and social_links.get("linkedin") != "Not available": li = social_links["linkedin"]
                                            
                                            if email == "Not available" and target_social != "Not available":
                                                e_ext, wa_ext, wa_link_ext, _, _, _, _, err_msg = extract_contacts_from_url(target_social)
                                                if err_msg != "Success": debug_logs.append(f"Social Extr Error: {err_msg}")
                                                if e_ext != "Not available": email, email_source, email_source_url = e_ext, "Social Media", target_social
                                                if whatsapp == "Not available" and wa_ext != "Not available": whatsapp = wa_ext
                                                if wa_link_direct == "Not available" and wa_link_ext != "Not available": wa_link_direct = wa_link_ext
                                        
                                        sources_searched.append("Search Engine")
                                        if email == "Not available":
                                            email_fallback, e_s_url = hunt_email_internet(company_name, loc, domain)
                                            if email_fallback != "Not available": email, email_source, email_source_url = email_fallback, "Search Engine", e_s_url

                                        full_biz_text = f"{category} {company_name} {website_context_text}".lower()
                                        c_score, b_score, t_score, badge, evidence, qual_status, is_excl = get_dual_score(
                                            full_biz_text, email, phone, whatsapp, wa_link_direct, website, req_kws, strong_kws, bonus_kws, excludes
                                        )
                                        
                                    if email != "Not available": sources_found.append("Email")
                                    if whatsapp != "Not available" or wa_link_direct != "Not available": sources_found.append("WhatsApp")
                                    if fb != "Not available" or ig != "Not available" or li != "Not available": sources_found.append("Social")
                                    
                                    enrich_time = round(time.time() - start_time, 1)
                                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    
                                    status_val = "Excluded" if qual_status == "EXCLUDED" else "Not ICP" if qual_status == "NOT_ICP" else "Ready to Contact"
                                    
                                    lead_dict = {
                                        "lead_id": lead_id,
                                        "created_at": now,
                                        "last_seen_at": now,
                                        "enriched_at": now,
                                        "maps_id": maps_id,
                                        "maps_url": maps_url,
                                        "domain": domain,
                                        "norm_name": norm_name,
                                        "norm_address": norm_addr,
                                        "location": norm_loc,
                                        "query": base,
                                        "company": company_name,
                                        "category": category,
                                        "address": address,
                                        "website": website,
                                        "phone": phone,
                                        "whatsapp": whatsapp,
                                        "email": email,
                                        "email_source": email_source,
                                        "email_source_url": email_source_url,
                                        "wa_link": wa_link_direct,
                                        "facebook": fb,
                                        "instagram": ig,
                                        "linkedin": li,
                                        "contactability_score": c_score,
                                        "icp_fit_score": b_score,
                                        "priority_score": t_score,
                                        "matched_keywords": evidence,
                                        "qual_status": qual_status,
                                        "priority_badge": badge,
                                        "status": status_val,
                                        "enrichment_level": applied_enrichment_level,
                                        "enrich_time": f"{enrich_time}s",
                                        "icp_hash": icp_hash,
                                        "sources_searched": ", ".join(sources_searched),
                                        "sources_found": ", ".join(sources_found) if sources_found else "None",
                                        "debug_logs": "; ".join(debug_logs) if debug_logs else "None"
                                    }
                                    
                                    discovery_dict = {
                                        "run_id": run_id,
                                        "query": base,
                                        "location": loc,
                                        "discovered_at": now
                                    }
                                    
                                    action_taken = upsert_lead_transaction(db_conn, lead_dict, identity_aliases, discovery_dict)
                                    
                                    msg = f"✓ {action_taken}: {company_name} | {badge} | ⏱ {enrich_time}s"
                                    if debug_mode and debug_logs: msg += f" | 🐞 Errors: {len(debug_logs)}"
                                    status_box.write(msg)
                                        
                            except Exception as e: 
                                status_box.write(f"Error on {base}: {type(e).__name__}")
            finally:
                if context:
                    try: context.close()
                    except: pass
                if browser:
                    try: browser.close()
                    except: pass
                    
        st.success(f"🎉 BATCH COMPLETE!")
        if dropped_no_identity_count > 0:
            st.warning(f"⚠️ {dropped_no_identity_count} prospects were dropped directly due to a lack of identifiable data (No Maps ID or Address found).")
        
        time.sleep(3)
        st.rerun() 

# ---------------------------------------------------------
# TAB 2: QUALIFY (Funnel Dashboard & Sorting)
# ---------------------------------------------------------

with tab_qualify:
    st.markdown("### 🧠 Prospect Qualification & Funnel Dashboard")

    db_df = load_leads()

    if not db_df.empty:
        total_prospects = len(db_df)
        qualified = len(db_df[db_df['qual_status'] == 'QUALIFIED'])
        not_icp = len(db_df[db_df['qual_status'] == 'NOT_ICP'])
        excluded = len(db_df[db_df['qual_status'] == 'EXCLUDED'])
        
        email_ready = len(db_df[(db_df['qual_status'] == 'QUALIFIED') & (db_df['email'] != 'Not available')])
        has_wa = len(db_df[(db_df['whatsapp'] != 'Not available') | (db_df['wa_link'] != 'Not available')])
        contacted = len(db_df[db_df['status'] == 'Contacted'])
        replied = len(db_df[db_df['status'] == 'Replied'])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("TOTAL PROSPECTS", total_prospects)
        c2.metric("ICP QUALIFIED", qualified)
        c3.metric("NOT ICP", not_icp)
        c4.metric("EXCLUDED", excluded)
        
        st.markdown("---")
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("EMAIL READY", email_ready)
        c6.metric("WHATSAPP AVAILABLE", has_wa)
        c7.metric("CONTACTED", contacted)
        c8.metric("REPLIED", replied)
        st.markdown("---")
        
        st.markdown("#### Database Filters")
        col_req1, col_req2, col_req3, col_req4 = st.columns(4)
        with col_req1: 
            icp_filter = st.multiselect("ICP Status:", ["QUALIFIED", "NOT_ICP", "EXCLUDED"], default=["QUALIFIED"])
        with col_req2: 
            quality_filter = st.multiselect("Priority Badge:", ["🔥 EXCELLENT", "🟢 GOOD", "🟡 NORMAL", "🔴 LOW"], default=["🔥 EXCELLENT", "🟢 GOOD", "🟡 NORMAL"])
        with col_req3: 
            req_email = st.checkbox("☑ Must have Email")
            req_phone = st.checkbox("☑ Must have Phone or WhatsApp")
        with col_req4: 
            min_score = st.number_input("Minimum Priority Score (/100)", min_value=0, max_value=100, value=0)
        
        filtered_df = db_df.copy()
        
        if icp_filter: filtered_df = filtered_df[filtered_df['qual_status'].isin(icp_filter)]
        if quality_filter: filtered_df = filtered_df[filtered_df['priority_badge'].isin(quality_filter)]
            
        if req_email: filtered_df = filtered_df[filtered_df['email'] != "Not available"]
        if req_phone: filtered_df = filtered_df[(filtered_df['phone'] != "Not available") | (filtered_df['whatsapp'] != "Not available") | (filtered_df['wa_link'] != "Not available")]
        
        filtered_df = filtered_df[filtered_df['priority_score'] >= min_score]
        
        display_cols = ['company', 'category', 'website', 'email', 'email_source_url', 'phone', 'whatsapp', 'linkedin', 'contactability_score', 'icp_fit_score', 'priority_score', 'matched_keywords', 'priority_badge', 'status', 'sources_searched', 'enrichment_level']
        if 'debug_logs' in filtered_df.columns: display_cols.append('debug_logs')
            
        display_df = filtered_df[display_cols] if not filtered_df.empty else pd.DataFrame()
        st.dataframe(display_df, use_container_width=True)
        
        st.markdown(f"**Showing {len(filtered_df)} prospects matching current filters.**")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1,1,1])
        with col_btn1:
            if not filtered_df.empty:
                csv_data = filtered_df.to_csv(index=False, sep=";").encode('utf-8-sig')
                st.download_button("💾 Export Filtered Prospects to CSV", data=csv_data, file_name="origami_prospects.csv", mime="text/csv")
        with col_btn2:
            if st.button("🚨 Recover stuck sends"):
                l_res, a_res = reset_stuck_sends()
                st.success(f"Recovered {l_res} leads and {a_res} activities. Manual review required.")
                time.sleep(2)
                st.rerun()
        with col_btn3:
            if st.button("🗑️ Clear Local Database"):
                if clear_db():
                    st.rerun()
                else:
                    st.error("Cannot clear database while active sends exist. Please wait for campaigns to finish or reset stuck sends.")
    else:
        st.info("Your local SQLite database is empty. Please run the Discovery engine in Step 1.")

# ---------------------------------------------------------
# TAB 3: PROSPECT (Native Email Outreach)
# ---------------------------------------------------------

with tab_prospect:
    st.markdown("### ✉️ Controlled Outreach Campaign")
    st.markdown("Send targeted cold emails safely with global recipient-level concurrency locks.")

    col_em1, col_em2 = st.columns(2)
    with col_em1:
        sender_email = st.text_input("Sender Email Address", placeholder="youremail@gmail.com")
        sender_password = st.text_input("App Password", type="password", placeholder="16-digit code")
        email_subject = st.text_input("Email Subject", placeholder="Partnership Inquiry")
    with col_em2:
        target_quality = st.multiselect("Send ONLY to leads with Priority Badge:", ["🔥 EXCELLENT", "🟢 GOOD", "🟡 NORMAL"], default=["🔥 EXCELLENT", "🟢 GOOD"])
        max_emails_this_run = st.number_input("Max successful emails per campaign (Limit: 200):", min_value=1, max_value=200, value=20)
        delay_range = st.slider("Humanized Delay between emails (seconds):", 5, 60, (10, 20))

    if st.button("🚀 START OUTREACH CAMPAIGN"):
        if not sender_email or not sender_password or not email_subject:
            st.error("Please provide your SMTP credentials and Email Subject.")
            st.stop()
            
        if not os.path.exists(TEMPLATE_PATH):
            st.error(f"Template '{TEMPLATE_PATH}' not found in the application folder.")
            st.stop()
            
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            html_template_content = f.read()
            
        try:
            active_server = connect_smtp(sender_email, sender_password)
        except Exception as e:
            st.error(f"SMTP Login Failed: {type(e).__name__}")
            st.stop()
            
        st.markdown("#### Campaign Log:")
        log_box = st.empty()
        
        campaign_run_id = f"CAMP-{uuid.uuid4().hex[:8].upper()}"
        sent_count = 0
        stop_campaign = False
        no_more_leads = False
        skipped_ids = set()
        
        # Resilient Queue Fetching
        while sent_count < max_emails_this_run:
            campaign_targets = get_campaign_candidates(target_quality, (max_emails_this_run - sent_count) * 2, list(skipped_ids)) 
            if campaign_targets.empty: 
                no_more_leads = True
                break
            
            locked_in_batch = 0
            for _, lead in campaign_targets.iterrows():
                if sent_count >= max_emails_this_run: break
                    
                email_lower = lead['email'].strip().lower() if lead['email'] else ""
                if not email_lower or email_lower == "not available": continue
                
                # ATOMIC DATABASE LOCK & ACTIVITY CREATION
                fresh_lead = lock_lead_and_create_activity(lead['lead_id'], campaign_run_id, email_lower, sender_email, email_subject)
                if not fresh_lead: continue 
                locked_in_batch += 1
                
                # Verify Lead is still eligible post-lock
                if fresh_lead['qual_status'] != "QUALIFIED" or fresh_lead['priority_badge'] not in target_quality:
                    release_send_lock(lead['lead_id'], fresh_lead['lock_token'], email_lower, fresh_lead.get('activity_id'))
                    skipped_ids.add(lead['lead_id'])
                    continue
                
                success, new_status, active_server = send_single_email(
                    active_server, sender_email, sender_password, fresh_lead['email'], email_subject, fresh_lead['company'], html_template_content
                )
                
                err_msg = "" if success else new_status
                try:
                    update_activity_and_lead(fresh_lead['activity_id'], lead['lead_id'], new_status, new_status, fresh_lead['lock_token'], err_msg, email_lower)
                except RuntimeError as re_err:
                    log_box.error(str(re_err))
                    skipped_ids.add(lead['lead_id'])
                    if new_status in ["Send outcome unknown", "Sender rejected"]:
                        log_box.warning(f"⚠️ {new_status.upper()}. Campaign infrastructure issue. Campaign stopped. DO NOT RETRY AUTOMATICALLY.")
                        stop_campaign = True
                        break
                    continue 
                except Exception as gen_err:
                    log_box.error(f"Unexpected DB Error updating lead {lead['lead_id']}: {type(gen_err).__name__}")
                    stop_campaign = True
                    break
                
                if success:
                    sent_count += 1
                    sleep_time = random.uniform(delay_range[0], delay_range[1])
                    log_box.success(f"[{sent_count}/{max_emails_this_run}] Sent to {fresh_lead['company']} ({fresh_lead['email']}) | ID: {lead['lead_id']} | Waiting {round(sleep_time, 1)}s")
                    time.sleep(sleep_time)
                else:
                    skipped_ids.add(lead['lead_id'])
                    log_box.error(f"Failed to send to {fresh_lead['company']} - {new_status}")
                    if new_status in ["Send outcome unknown", "Sender rejected"]:
                        log_box.warning(f"⚠️ {new_status.upper()}. Campaign infrastructure issue. Campaign stopped. DO NOT RETRY AUTOMATICALLY.")
                        stop_campaign = True
                        break
            
            if stop_campaign: 
                break 
            if locked_in_batch == 0:
                log_box.info("No additional eligible leads could be locked in this batch.")
                no_more_leads = True
                break
                        
        try: active_server.quit()
        except: pass
        
        # Semantic UI Feedback
        if stop_campaign:
            st.warning(f"⚠️ Campaign stopped due to infrastructure or configuration issues. Successfully sent {sent_count} emails. Database updated.")
        elif no_more_leads and sent_count < max_emails_this_run:
            st.info(f"ℹ️ Campaign ended early. No additional eligible/unlocked leads available. Successfully sent {sent_count} emails. Database updated.")
        else:
            st.success(f"✅ Campaign completed! Successfully sent {sent_count} emails. Database updated.")
            
        time.sleep(3)
        st.rerun()