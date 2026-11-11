"""Daily summary email - goes ONLY to the owner's address (REPORT_EMAIL secret / .env).

Sent through the Gmail API with the same sign-in as YouTube (gmail.send scope), so no
password is stored anywhere. Inline styles + bgcolor attributes so Gmail renders it as designed.
"""
import base64
import datetime as dt
import html
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

from .core import config, log


def _when(iso):
    if not iso:
        return ""
    t = dt.datetime.fromisoformat(iso)
    ist = t.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%a %d %b, %I:%M %p IST")
    et = t.astimezone(ZoneInfo("America/New_York")).strftime("%I:%M %p ET")
    return f"{ist} ({et})"


def build(results, stats=None):
    e = html.escape
    bank = next((r["bank"] for r in results if "bank" in r), None)
    results = [r for r in results if "bank" not in r]
    pub = [r for r in results if r.get("video_id")]
    held = [r for r in results if not r.get("video_id")]
    rows = "".join(
        f'<tr><td style="padding:10px 0;border-bottom:1px solid #e3e7ee">'
        f'<a href="https://youtube.com/shorts/{e(r["video_id"])}" style="color:#0b1630;font-weight:700;text-decoration:none">{e(r["title"])}</a>'
        f'<br><span style="color:#5a6577;font-size:13px">Goes public {e(_when(r.get("publish_at")))}</span>'
        f'<br><span style="color:#5a6577;font-size:13px">Closing question: {e(r.get("question", ""))}</span></td></tr>'
        for r in pub) or '<tr><td style="padding:10px 0;color:#5a6577">Nothing published today.</td></tr>'
    held_rows = "".join(
        f'<tr><td style="padding:8px 0;border-bottom:1px solid #f0e3e3"><b>{e(r.get("title") or r.get("topic", ""))}</b>'
        f'<br><span style="color:#8a3b3b;font-size:13px">{e(r.get("reason", ""))}</span></td></tr>'
        for r in held)
    st = stats or {}
    stat_line = (f'{st.get("subscribers", "–")} subscribers · {st.get("views", "–")} total views · '
                 f'{st.get("videos", "–")} public videos') if st else ""
    today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y")
    body = f"""<table width="100%" cellpadding="0" cellspacing="0" bgcolor="#f3f5f9" style="background-color:#f3f5f9;padding:24px 0">
<tr><td align="center"><table width="560" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="background-color:#ffffff;border-radius:12px;font-family:Arial,sans-serif">
<tr><td bgcolor="#0b1630" style="background-color:#0b1630;padding:20px 24px;border-radius:12px 12px 0 0">
<span style="color:#ffd60a;font-size:22px;font-weight:800">Ever Thought Why?</span>
<span style="color:#aab8d6;font-size:14px"> &nbsp;daily report · {today}</span></td></tr>
<tr><td style="padding:20px 24px">
<p style="margin:0 0 6px;font-size:15px;color:#0b1630"><b>{len(pub)} published</b> · {len(held)} held back</p>
<p style="margin:0 0 16px;font-size:13px;color:#5a6577">{e(stat_line)}</p>
{f'<p style="margin:0 0 16px;font-size:13px;color:#0b1630">Video bank: <b>{bank}</b> videos ready and scheduled ahead (3 go public each day).</p>' if bank is not None else ''}
<p style="margin:16px 0 4px;font-size:13px;letter-spacing:.06em;color:#00a896"><b>PUBLISHED / SCHEDULED</b></p>
<table width="100%" cellpadding="0" cellspacing="0">{rows}</table>
{f'<p style="margin:20px 0 4px;font-size:13px;letter-spacing:.06em;color:#b00020"><b>HELD BACK (not uploaded)</b></p><table width="100%" cellpadding="0" cellspacing="0">{held_rows}</table>' if held else ''}
<p style="margin:22px 0 0;font-size:12px;color:#8a94a6">Every video passed the fact-check and the quality check before upload.
Open YouTube Studio from the desktop icon to see everything.</p>
</td></tr></table></td></tr></table>"""
    subject = f"Ever Thought Why? · {len(pub)} published, {len(held)} held · {today}"
    return subject, body


def send(subject, body_html):
    from googleapiclient.discovery import build as gbuild
    from .youtube import _creds
    import os
    to = os.environ.get("REPORT_EMAIL") or config().get("report", {}).get("email")
    if not to:
        log("report: no REPORT_EMAIL set, skipping")
        return
    msg = MIMEText(body_html, "html", "utf-8")
    msg["to"] = to
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gbuild("gmail", "v1", credentials=_creds(), cache_discovery=False).users().messages().send(
        userId="me", body={"raw": raw}).execute()
    log("report: sent to the owner")  # never print the address: the run logs are public
