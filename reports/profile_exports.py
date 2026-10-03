from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

NAVY = (23, 51, 74)
TEAL = (0, 132, 130)
PALE = (232, 240, 244)
INK = (31, 51, 64)
MUTED = (96, 117, 128)
WHITE = (255, 255, 255)
LINE = (208, 220, 226)


def _clean(value):
    if value in (None, '', []):
        return '—'
    if isinstance(value, (list, tuple)):
        return ', '.join(str(v) for v in value) or '—'
    return str(value)


def _font(size, bold=False):
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
        'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def _wrap_pillow(draw, text, font, max_width, max_lines=3):
    words = _clean(text).replace('\n', ' ').split()
    if not words:
        return ['—']
    lines, current = [], ''
    for word in words:
        candidate = f'{current} {word}'.strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and sum(len(line.split()) for line in lines) < len(words):
        lines[-1] = lines[-1].rstrip('.,;:') + '…'
    return lines or ['—']


def _photo_image(field, size):
    if not field:
        return None
    try:
        image = Image.open(field.path)
        image = ImageOps.exif_transpose(image).convert('RGB')
        return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.35))
    except (OSError, ValueError, AttributeError):
        return None


def profile_jpg_bytes(person, *, profile=None, family_harmony=False):
    """Render a fixed desktop-style profile card as a high resolution JPEG."""
    width = 1275
    margin = 58
    header_h = 310
    title_font = _font(42, True)
    subtitle_font = _font(20)
    section_font = _font(22, True)
    label_font = _font(15, True)
    value_font = _font(19)
    small_font = _font(15)

    if family_harmony and profile is not None:
        pref = getattr(profile, 'preferences', None)
        sections = [
            ('Personal Information', [
                ('Date of Birth', person.date_of_birth), ('Gender', person.gender),
                ('Nationality', person.nationality), ('Marital Status', profile.marital_status or person.marital_status),
                ('City / Country', f'{person.city or "—"} / {person.country or "—"}'), ('Jamatkhana', person.jamatkhana),
                ('Height / Weight', f'{profile.height_cm or "—"} cm / {profile.weight_kg or "—"} kg'), ('Physical Status', profile.physical_status),
            ]),
            ('Family', [
                ('Father', f'{profile.father_name or "—"} / {profile.father_occupation or "—"}'),
                ('Mother', f'{profile.mother_name or "—"} / {profile.mother_occupation or "—"}'),
                ('Brothers / Sisters', f'{profile.brothers_count if profile.brothers_count is not None else "—"} / {profile.sisters_count if profile.sisters_count is not None else "—"}'),
                ('Family Type', profile.family_type), ('Family Residence', profile.family_residence), ('Caste / Tribe', profile.caste_tribe),
            ]),
            ('Education & Career', [
                ('Education', profile.qualification or profile.education_level or person.education), ('Institution', profile.institution),
                ('Profession', profile.profession or person.occupation), ('Employer / Business', profile.employer_or_business or person.employer_or_business),
                ('Income Range', profile.income_range or person.income_range), ('House / Car', f'{"Yes" if profile.owns_house else "No"} / {"Yes" if profile.owns_car else "No"}'),
            ]),
            ('Lifestyle', [
                ('Languages', profile.languages or person.languages), ('Interests', profile.interests or person.interests),
                ('Smoking', profile.smoking), ('Willing to Relocate', 'Yes' if person.willing_to_relocate else 'No' if person.willing_to_relocate is False else '—'),
                ('Personal Statement', profile.personal_statement), ('Family Values', profile.family_values),
            ]),
                  ('Social Links', [
                ('Facebook', person.facebook_url), ('Instagram', person.instagram_url),
                ('LinkedIn', person.linkedin_url), ('Other', person.other_social_url),
            ]),
        ]
        if pref:
            sections.append(('Preferences for Prospective Match', [
                ('Age Range', f'{pref.minimum_age or "Any"} - {pref.maximum_age or "Any"}'), ('Education', pref.preferred_education_options),
                ('Profession', pref.preferred_professions), ('Location', pref.preferred_cities or pref.preferred_locations),
                ('Income', pref.preferred_income_options), ('Languages', pref.preferred_languages),
            ]))
        serial = profile.serial_number
        record_type = 'Family Harmony Profile'
    else:
        sections = [
            ('Personal Information', [
                ('Date of Birth', person.date_of_birth), ('Age', person.age), ('Gender', person.gender),
                ('Marital Status', person.marital_status), ('Nationality', person.nationality),
                ('Identity', f'{person.get_identity_type_display() if person.identity_type else "—"} · {person.masked_identity_number() or "—"}'),
            ]),
            ('Contact & Residence', [
                ('Mobile', person.mobile), ('WhatsApp', person.whatsapp_number), ('Email', person.email),
                ('City / Province', f'{person.city or "—"} / {person.province or "—"}'), ('Country', person.country),
                ('Current Address', person.current_address), ('Permanent Address', person.permanent_address),
            ]),
            ('Jamatkhana', [
                ('Regional Council', person.region), ('Local Council', person.local_council), ('Jamatkhana', person.jamatkhana),
            ]),
            ('Education & Career', [
                ('Education', person.education), ('Education Details', person.education_details), ('Occupation', person.occupation),
                ('Employer / Business', person.employer_or_business), ('Income Range', person.income_range),
                ('Languages', person.languages), ('Interests', person.interests),
            ]),
        ]
        serial = person.serial_number
        record_type = 'People Profile'

    # Estimate adaptive height from row counts and long fields.
    estimated_rows = sum((len(items) + 1) // 2 for _, items in sections)
    height = max(1650, header_h + 110 + len(sections) * 70 + estimated_rows * 96 + 140)
    image = Image.new('RGB', (width, height), WHITE)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, width, header_h), fill=NAVY)
    photo_box = (margin, 52, margin + 206, 272)
    photo = _photo_image(person.photo, (206, 220))
    if photo:
        image.paste(photo, (photo_box[0], photo_box[1]))
    else:
        draw.rounded_rectangle(photo_box, radius=12, fill=(240, 245, 247), outline=LINE, width=3)
        initials = ''.join(part[:1] for part in [person.first_name, person.last_name] if part)[:2].upper() or 'P'
        initials_font = _font(60, True)
        box = draw.textbbox((0, 0), initials, font=initials_font)
        draw.text((photo_box[0] + (206 - (box[2] - box[0])) / 2, photo_box[1] + 68), initials, font=initials_font, fill=TEAL)
    draw.rounded_rectangle(photo_box, radius=12, outline=(190, 212, 222), width=3)

    x = 302
    draw.text((x, 60), person.full_name[:48], font=title_font, fill=WHITE)
    draw.text((x, 122), f'{serial}  ·  {record_type}', font=subtitle_font, fill=(213, 229, 237))
    draw.text((x, 160), 'Aga Khan Social Welfare Board · Central Region', font=small_font, fill=(185, 215, 226))
    badges = [f'{person.age if person.age is not None else "—"} yrs', person.gender or '—', person.marital_status or '—']
    bx = x
    for badge in badges:
        tw = int(draw.textlength(str(badge), font=small_font)) + 30
        draw.rounded_rectangle((bx, 205, bx + tw, 247), radius=21, fill=WHITE)
        draw.text((bx + 15, 215), str(badge), font=small_font, fill=NAVY)
        bx += tw + 12

    y = header_h + 46
    content_w = width - margin * 2
    col_gap = 36
    col_w = (content_w - col_gap) // 2
    for heading, items in sections:
        draw.rounded_rectangle((margin, y, width - margin, y + 48), radius=9, fill=PALE)
        draw.text((margin + 18, y + 11), heading, font=section_font, fill=NAVY)
        y += 68
        for i in range(0, len(items), 2):
            pair = items[i:i + 2]
            rendered = []
            row_h = 70
            for label, value in pair:
                lines = _wrap_pillow(draw, value, value_font, col_w - 18, max_lines=3)
                row_h = max(row_h, 42 + len(lines) * 27)
                rendered.append((label, lines))
            for col, (label, lines) in enumerate(rendered):
                cell_x = margin + col * (col_w + col_gap)
                draw.text((cell_x, y), str(label).upper(), font=label_font, fill=MUTED)
                for line_index, line in enumerate(lines):
                    draw.text((cell_x, y + 25 + line_index * 27), line, font=value_font, fill=INK)
            y += row_h
        y += 24

    footer_y = height - 58
    draw.line((margin, footer_y - 18, width - margin, footer_y - 18), fill=LINE, width=2)
    draw.text((margin, footer_y), 'Confidential Social Welfare profile · Generated from the live record', font=small_font, fill=MUTED)
    draw.text((width - margin - 220, footer_y), 'Desktop export', font=small_font, fill=MUTED)

    output = BytesIO()
    image.save(output, format='JPEG', quality=92, optimize=True)
    return output.getvalue()


def _shared_profile_pdf_bytes(person, *, serial, record_type, sections, footer_text, document_title, badge_marital_status=None):
    """One PDF renderer shared by People and Family Harmony exports."""
    output = BytesIO()
    width, height = letter
    pdf = canvas.Canvas(output, pagesize=letter)
    pdf.setTitle(document_title)
    navy = (0.09, 0.20, 0.29)
    pale = (0.91, 0.94, 0.96)
    ink = (0.12, 0.20, 0.25)
    muted = (0.38, 0.46, 0.50)

    def wrap(text, font='Helvetica', size=6.8, max_width=175, max_lines=2):
        words = _clean(text).replace('\n', ' ').split()
        lines, line = [], ''
        for word in words:
            test = (line + ' ' + word).strip()
            if stringWidth(test, font, size) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
                if len(lines) >= max_lines:
                    break
        if line and len(lines) < max_lines:
            lines.append(line)
        if not lines:
            lines = ['—']
        if len(lines) == max_lines and len(words) > sum(len(x.split()) for x in lines):
            lines[-1] = lines[-1][:-1] + '…' if len(lines[-1]) > 2 else lines[-1]
        return lines

    # Header dimensions and typography are intentionally identical for both modules.
    pdf.setFillColorRGB(*navy)
    pdf.rect(0, height - 138, width, 138, fill=1, stroke=0)
    photo_x, photo_y, photo_w, photo_h = 28, height - 128, 88, 106
    if person.photo:
        try:
            pdf.drawImage(ImageReader(person.photo.path), photo_x, photo_y, photo_w, photo_h, preserveAspectRatio=True, anchor='c', mask='auto')
        except (OSError, ValueError):
            pass
    pdf.setStrokeColorRGB(0.75, 0.83, 0.87)
    pdf.rect(photo_x, photo_y, photo_w, photo_h, fill=0, stroke=1)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont('Helvetica-Bold', 20)
    pdf.drawString(134, height - 48, person.full_name[:38])
    pdf.setFont('Helvetica', 8)
    pdf.drawString(134, height - 68, f'{serial}   |   {record_type}')
    pdf.drawString(134, height - 84, 'Aga Khan Social Welfare Board - Central Region')
    badges = [f'{person.age or "—"} yrs', person.gender or '—', badge_marital_status or person.marital_status or '—']
    bx = 134
    for badge in badges:
        bw = stringWidth(str(badge), 'Helvetica-Bold', 7) + 14
        pdf.setFillColorRGB(1, 1, 1)
        pdf.roundRect(bx, height - 112, bw, 18, 9, fill=1, stroke=0)
        pdf.setFillColorRGB(*navy)
        pdf.setFont('Helvetica-Bold', 7)
        pdf.drawCentredString(bx + bw / 2, height - 106, str(badge))
        bx += bw + 6

    y = height - 156
    def section(title, items):
        nonlocal y
        pdf.setFillColorRGB(*pale)
        pdf.roundRect(26, y - 2, width - 52, 17, 3, fill=1, stroke=0)
        pdf.setFillColorRGB(*navy)
        pdf.setFont('Helvetica-Bold', 8.5)
        pdf.drawString(32, y + 3, title)
        y -= 16
        col_w = (width - 64) / 2
        for index in range(0, len(items), 2):
            pair = items[index:index + 2]
            max_lines = 1
            rendered = []
            for label, value in pair:
                lines = wrap(value, max_width=col_w - 82, max_lines=2)
                max_lines = max(max_lines, len(lines))
                rendered.append((label, lines))
            row_height = 10 + (max_lines * 7)
            for col, (label, lines) in enumerate(rendered):
                x = 32 + col * col_w
                pdf.setFillColorRGB(*muted)
                pdf.setFont('Helvetica-Bold', 6.3)
                pdf.drawString(x, y, label.upper())
                pdf.setFillColorRGB(*ink)
                pdf.setFont('Helvetica', 6.8)
                for line_no, line in enumerate(lines):
                    pdf.drawString(x + 76, y - (line_no * 7), line)
            y -= row_height
        y -= 4

    for title, items in sections:
        if y <= 58:
            break
        section(title, items)

    pdf.setStrokeColorRGB(0.78, 0.82, 0.84)
    pdf.line(26, 34, width - 26, 34)
    pdf.setFillColorRGB(*muted)
    pdf.setFont('Helvetica', 6.3)
    pdf.drawString(28, 22, footer_text)
    pdf.drawRightString(width - 28, 22, 'US Letter · Page 1 of 1')
    pdf.save()
    return output.getvalue()


def marriage_pdf_bytes(profile):
    person = profile.person
    pref = getattr(profile, 'preferences', None)
    height_text = '—'
    if profile.height_cm:
        total_inches = round(profile.height_cm / 2.54)
        height_text = f'{total_inches // 12} ft {total_inches % 12} in'
    sections = [
        ('Personal Information', [
            ('Age / DOB', f'{person.age or "—"} / {person.date_of_birth or "—"}'), ('Gender', person.gender),
            ('Marital Status', profile.marital_status or person.marital_status), ('Height / Weight', f'{height_text} / {profile.weight_kg or "—"} kg'),
            ('Physical Status', profile.physical_status), ('City / Country', f'{person.city or "—"}, {person.country or "—"}'),
            ('Jamatkhana', person.jamatkhana), ('Local Council', person.local_council),
        ]),
        ('Family', [
            ('Father', f'{profile.father_name or "—"} / {profile.father_occupation or "—"}'), ('Mother', f'{profile.mother_name or "—"} / {profile.mother_occupation or "—"}'),
            ('Brothers', profile.brothers_count), ('Sisters', profile.sisters_count), ('Family Residence', profile.family_residence), ('Family Type', profile.family_type), ('Caste / Tribe', profile.caste_tribe),
        ]),
        ('Education & Career', [
            ('Education', profile.qualification or profile.education_level or person.education), ('Institution', profile.institution), ('Profession', profile.profession or person.occupation),
            ('Employer / Business', profile.employer_or_business or person.employer_or_business), ('Income', profile.income_range or person.income_range), ('Experience', profile.years_experience),
            ('House', 'Yes' if profile.owns_house is True else 'No' if profile.owns_house is False else '—'), ('Car', 'Yes' if profile.owns_car is True else 'No' if profile.owns_car is False else '—'),
        ]),
        ('Health & Lifestyle', [
            ('Disability', profile.disability_status), ('Known Diseases', profile.known_diseases), ('Smoking', profile.smoking), ('Languages', profile.languages or person.languages),
            ('Interests', profile.interests or person.interests), ('Health Notes', profile.health_information),
        ]),
        ('Social Links', [
            ('Facebook', person.facebook_url), ('Instagram', person.instagram_url),
            ('LinkedIn', person.linkedin_url), ('Other', person.other_social_url),
        ]),
    ]
    if pref:
        sections.append(('Preferences for Prospective Match', [
            ('Age Range', f'{pref.minimum_age or "Any"} - {pref.maximum_age or "Any"}'), ('Education', pref.preferred_education_options), ('Profession', pref.preferred_professions),
            ('Location', pref.preferred_cities or pref.preferred_locations), ('Income', pref.preferred_income_options), ('Marital Status', pref.preferred_marital_status_options),
            ('Languages', pref.preferred_languages), ('Relocation', 'Yes' if pref.willingness_to_relocate else 'No'),
        ]))
        sections.append(('About', [('Personal Statement', profile.personal_statement), ('Other Expectations', pref.other_expectations or profile.expectations)]))
    return _shared_profile_pdf_bytes(person, serial=profile.serial_number, record_type='Marriage Profile', sections=sections, footer_text='Confidential Family Harmony profile. CNIC images and internal documents are not included.', document_title=f'Marriage Profile - {person.full_name}', badge_marital_status=profile.marital_status)


def person_pdf_bytes(person):
    sections = [
        ('Personal Information', [
            ('Age / DOB', f'{person.age or "—"} / {person.date_of_birth or "—"}'), ('Gender', person.gender),
            ('Marital Status', person.marital_status), ('Nationality', person.nationality),
            ('Identity', f'{person.get_identity_type_display() if person.identity_type else "—"} · {person.masked_identity_number() or "—"}'), ('City / Country', f'{person.city or "—"}, {person.country or "—"}'),
            ('Jamatkhana', person.jamatkhana), ('Local Council', person.local_council),
        ]),
        ('Contact & Residence', [
            ('Mobile', person.mobile), ('WhatsApp', person.whatsapp_number), ('Alternate Mobile', person.alternate_mobile), ('Email', person.email),
            ('Current Address', person.current_address), ('Permanent Address', person.permanent_address),
        ]),
        ('Jamatkhana', [('Regional Council', person.region), ('Local Council', person.local_council), ('Jamatkhana', person.jamatkhana)]),
        ('Education & Career', [
            ('Education', person.education), ('Education Details', person.education_details), ('Occupation', person.occupation), ('Employer / Business', person.employer_or_business),
            ('Income Range', person.income_range), ('Languages', person.languages), ('Interests', person.interests), ('Relocation', 'Yes' if person.willing_to_relocate else 'No' if person.willing_to_relocate is False else '—'),
        ]),
    ]
    social = [('Facebook', person.facebook_url), ('Instagram', person.instagram_url), ('LinkedIn', person.linkedin_url), ('Other', person.other_social_url)]
    if any(v for _, v in social):
        sections.append(('Social Links', social))
    return _shared_profile_pdf_bytes(person, serial=person.serial_number, record_type='People Profile', sections=sections, footer_text='Confidential People profile. CNIC images and internal documents are not included.', document_title=f'People Profile - {person.full_name}')
