from pathlib import Path
import re, shutil, sys

ROOT = Path.cwd()
marker = "WHATSAPP BRAND FIX 2026-10-03"
icon_include = '{% include "partials/whatsapp_icon.html" %}'

required = [ROOT/'manage.py', ROOT/'templates']
if not all(p.exists() for p in required):
    print('ERROR: Run this from the Social project root (for example E:\\social).')
    sys.exit(1)

changed = []

def write_if_changed(path: Path, text: str):
    old = path.read_text(encoding='utf-8') if path.exists() else None
    if old == text:
        return False
    if path.exists():
        bak = path.with_suffix(path.suffix + '.bak_whatsapp_20261003')
        if not bak.exists():
            shutil.copy2(path, bak)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='')
    changed.append(str(path.relative_to(ROOT)))
    return True

# 1) Shared official WhatsApp SVG icon.
icon_path = ROOT/'templates'/'partials'/'whatsapp_icon.html'
icon_svg = '''<svg class="whatsapp-brand-icon" viewBox="0 0 448 512" aria-hidden="true" focusable="false"><path fill="currentColor" d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222 0 39.1 10.2 77.3 29.6 111L.1 480l117.7-30.9c32.4 17.7 68.9 27 106 27h.1c122.3 0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157zm-157 341.6c-33.2 0-65.7-8.9-94-25.8l-6.7-4-69.8 18.3 18.6-68-4.4-7c-18.5-29.4-28.2-63.4-28.2-98.2 0-101.7 82.8-184.5 184.6-184.5 49.3 0 95.6 19.2 130.4 54.1 34.8 34.9 56.2 81.2 56.1 130.5 0 101.8-84.9 184.6-186.6 184.6zm101.2-138.2c-5.5-2.8-32.8-16.1-37.9-18-5.1-1.9-8.8-2.8-12.5 2.8s-14.3 18-17.6 21.8c-3.2 3.7-6.5 4.2-12 1.4-32.6-16.3-54-29.1-75.6-66-5.7-9.8 5.7-9.1 16.3-30.3 1.8-3.7.9-6.9-.5-9.7-1.4-2.8-12.5-30.1-17.1-41.2-4.5-10.8-9.1-9.3-12.5-9.5-3.2-.2-6.9-.2-10.6-.2-3.7 0-9.7 1.4-14.8 6.9-5.1 5.6-19.4 19-19.4 46.3s19.9 53.7 22.6 57.4c2.8 3.7 39.1 59.7 94.8 83.8 35.2 15.2 49 16.5 66.6 13.9 10.7-1.6 32.8-13.4 37.4-26.3 4.6-13 4.6-24.1 3.2-26.4-1.3-2.5-5-3.9-10.5-6.7z"/></svg>\n'''
write_if_changed(icon_path, icon_svg)

# Helpers for template text.
def add_class(attrs, cls):
    m = re.search(r'class=("|\')([^"\']*)(\1)', attrs)
    if m:
        classes = m.group(2).split()
        if cls not in classes:
            classes.append(cls)
        return attrs[:m.start()] + f'class={m.group(1)}{" ".join(classes)}{m.group(1)}' + attrs[m.end():]
    return attrs + f' class="{cls}"'

def add_attr(attrs, attr):
    name = attr.split('=')[0].strip()
    if re.search(r'\b'+re.escape(name)+r'=', attrs):
        return attrs
    return attrs + ' ' + attr

def clean_phone_href(href):
    # Add removal of dashes/spaces to Django template phone expressions when possible.
    if 'wa.me/' in href and "|cut:'+'" in href:
        if "|cut:'-'" not in href:
            href = href.replace("|cut:'+'", "|cut:'+'|cut:'-'")
        if "|cut:' '" not in href:
            href = href.replace("|cut:'-'", "|cut:'-'|cut:' '")
    return href

def transform_anchor(match):
    attrs, body = match.group(1), match.group(2)
    lower = attrs.lower()
    is_wa = ('wa.me/' in lower or 'redirect=whatsapp' in lower or 'create_person_share' in lower or
             'create_profile_share' in lower or 'whatsapp_url' in lower or 'whatsapp' in lower)
    if not is_wa:
        return match.group(0)

    # Only transform likely WhatsApp actions/links, not arbitrary text mentions.
    if not any(x in lower for x in ('wa.me/', 'redirect=whatsapp', 'create_person_share', 'create_profile_share', 'whatsapp_url')):
        if 'whatsapp' not in lower:
            return match.group(0)

    attrs = re.sub(r'href=("|\')([^"\']*)(\1)', lambda m: f'href={m.group(1)}{clean_phone_href(m.group(2))}{m.group(1)}', attrs)
    attrs = add_attr(attrs, 'rel="noopener"') if 'target="_blank"' in attrs or "target='_blank'" in attrs else attrs

    # Action-column share buttons are icon-only.
    icon_only = ('class="wa"' in attrs or "class='wa'" in attrs or 'whatsapp-icon-only' in attrs)
    if icon_only:
        attrs = add_class(attrs, 'wa') if 'whatsapp-icon-only' not in attrs else attrs
        body = icon_include
    else:
        # Give visible/direct WhatsApp links a recognizable class.
        if 'phone-whatsapp' in attrs:
            attrs = add_class(attrs, 'whatsapp-inline-button')
        elif 'mobile-card-actions' not in lower and ('action-button' in attrs or 'btn ' in attrs or 'btn"' in attrs):
            attrs = add_class(attrs, 'whatsapp')
        # Strip common speech/SMS glyphs and insert brand icon if missing.
        if 'whatsapp_icon.html' not in body:
            body = re.sub(r'^\s*(?:&#128172;|&#128488;|💬|🗨️|🗨|◉|WA\b|SMS\b)\s*', '', body, flags=re.I)
            if re.search(r'WhatsApp|Send via|Open WhatsApp|\{\{', body, re.I):
                body = icon_include + (' ' if body.strip() else '') + body.strip()
            else:
                body = icon_include
    return '<a' + attrs + '>' + body + '</a>'

# 2) Update all templates that contain actual WhatsApp actions.
for path in (ROOT/'templates').rglob('*.html'):
    text = path.read_text(encoding='utf-8')
    original = text
    # Anchors, including multiline/minified templates.
    text = re.sub(r'<a\b([^>]*)>(.*?)</a>', transform_anchor, text, flags=re.I|re.S)

    # WhatsApp action buttons (e.g. public registration toolbar).
    def transform_button(m):
        attrs, body = m.group(1), m.group(2)
        if 'whatsapp' not in attrs.lower():
            return m.group(0)
        attrs2 = attrs
        if 'data-public-form-action="whatsapp"' in attrs2 or "data-public-form-action='whatsapp'" in attrs2:
            attrs2 = add_class(attrs2, 'whatsapp-public')
        if 'whatsapp_icon.html' not in body:
            body = re.sub(r'^\s*(?:&#128172;|&#128488;|💬|🗨️|🗨|WA\b|SMS\b)\s*', '', body, flags=re.I)
            body = icon_include + ((' ' + body.strip()) if body.strip() and 'WhatsApp' in body else '')
        return '<button' + attrs2 + '>' + body + '</button>'
    text = re.sub(r'<button\b([^>]*)>(.*?)</button>', transform_button, text, flags=re.I|re.S)

    # Mobile secure-share anchors may only say WhatsApp and have no identifying class.
    text = re.sub(r'(<a\b[^>]*(?:create_person_share|create_profile_share)[^>]*)(>)(\s*WhatsApp\s*</a>)',
                  lambda m: add_class(m.group(1), 'whatsapp-action') + m.group(2) + icon_include + ' WhatsApp</a>', text, flags=re.I)

    if text != original:
        write_if_changed(path, text)

# 3) CSS treatment; append idempotently.
css = ROOT/'static'/'app.css'
if css.exists():
    text = css.read_text(encoding='utf-8')
    if marker not in text:
        text += f'''\n\n/* {marker} */\n.whatsapp-brand-icon{{width:1em;height:1em;display:inline-block;vertical-align:-.12em;flex:0 0 auto}}\n.people-row-actions a.wa,.row-actions a.whatsapp-icon-only{{background:#25D366!important;color:#fff!important;border-color:#25D366!important}}\n.people-row-actions a.wa .whatsapp-brand-icon,.row-actions a.whatsapp-icon-only .whatsapp-brand-icon{{width:15px;height:15px}}\n.action-button.whatsapp,.btn.whatsapp,.mobile-card-actions a.whatsapp-action{{display:inline-flex;align-items:center;gap:6px;background:#25D366!important;color:#fff!important;border-color:#25D366!important}}\n.harmony-primary-phone.whatsapp-phone,.phone-whatsapp.whatsapp-inline-button{{display:inline-flex;align-items:center;gap:7px}}\n.harmony-primary-phone.whatsapp-phone .whatsapp-brand-icon,.phone-whatsapp.whatsapp-inline-button .whatsapp-brand-icon{{width:17px;height:17px}}\n.public-marriage-icon.whatsapp-public{{color:#fff;background:#25D366!important}}\n.public-marriage-icon.whatsapp-public .whatsapp-brand-icon{{width:17px;height:17px}}\n.whatsapp-inline-button{{display:inline-flex;align-items:center;gap:7px}}\n.whatsapp-inline-button .whatsapp-brand-icon{{width:16px;height:16px}}\n'''
        write_if_changed(css, text)

# 4) Reliable local server launcher. This is intentionally conservative: it only kills an existing Django runserver.
ps1 = ROOT/'run_social_local.ps1'
ps_text = r'''# Reliable local launcher for Social. Prevents stale Django runserver processes on port 8080.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$port = 8080

$listeners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
foreach ($listener in $listeners) {
    $pidOnPort = $listener.OwningProcess
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$pidOnPort" -ErrorAction SilentlyContinue
    $cmd = if ($proc) { [string]$proc.CommandLine } else { "" }
    $name = if ($proc) { [string]$proc.Name } else { "unknown" }

    if ($cmd -match "manage\.py\s+runserver") {
        Write-Host "Stopping stale Django runserver on port $port (PID $pidOnPort)..." -ForegroundColor Yellow
        Stop-Process -Id $pidOnPort -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }
    else {
        Write-Host "Port $port is already used by PID $pidOnPort ($name)." -ForegroundColor Red
        if ($cmd) { Write-Host "Command: $cmd" }
        Write-Host "Not killing it because it is not a Django runserver." -ForegroundColor Red
        exit 1
    }
}

$env:DJANGO_ALLOWED_HOSTS = "127.0.0.1,localhost,192.168.100.28"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Virtual environment python not found: $python" }

Write-Host "Starting Social on http://127.0.0.1:$port/" -ForegroundColor Green
Write-Host "Using --noreload so VS Code/Django does not leave a second autoreloader process." -ForegroundColor DarkGray
& $python manage.py runserver "0.0.0.0:$port" --noreload
'''
write_if_changed(ps1, ps_text)

print('\nApplied resilient WhatsApp/server fix.')
if changed:
    print('Changed files:')
    for item in changed:
        print('  -', item)
else:
    print('No file changes were needed; the fix already appears to be present.')
print('\nNext:')
print('  py manage.py check')
print('  .\\run_social_local.ps1')
