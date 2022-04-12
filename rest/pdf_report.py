import os
import textwrap
import uuid
from fpdf import FPDF

from rest.profile_dao import Profile


def text_to_pdf(text, image):
    a4_width_mm = 210
    pt_to_mm = 0.35
    fontsize_pt = 26
    fontsize_mm = fontsize_pt * pt_to_mm
    margin_bottom_mm = 10
    character_width_mm = 7 * pt_to_mm
    width_text = int(a4_width_mm // character_width_mm)

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(True, margin=margin_bottom_mm)
    pdf.add_page()

    name = uuid.uuid4().__str__()
    open(f'{name}.png', 'wb+').write(image)
    pdf.image(f'{name}.png', w=100, h=100)
    os.remove(f'{name}.png')
    pdf.set_font(family='Courier', size=fontsize_pt)
    splitted = text.split('\n')

    for line in splitted:
        lines = textwrap.wrap(line, width_text)

        if len(lines) == 0:
            pdf.ln()

        for wrap in lines:
            pdf.cell(0, fontsize_mm, wrap, ln=1)

    return pdf.output('', 'S').encode('latin-1')


def generate_pdf_by_profile(profile: Profile):
    text = f'''
=======================================
Login: {profile.login}
Name: {profile.name}
Gender: {profile.gender}
Mail: {profile.mail}
=======================================
Total time: {profile.total_time}
Sessions played: {profile.session_count}
Games won: {profile.win_count}
Games lost: {profile.lose_count}
'''
    return text_to_pdf(text, profile.image)
