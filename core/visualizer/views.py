from urllib import response
from django.contrib.auth.models import User
from django.shortcuts import render
from django.http import JsonResponse
from .models import ImageSlice
from .sorting import *
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer, PageBreak, Image as RLImage
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from datetime import datetime
from django.shortcuts import redirect
from .models import ImageUpload
from django.contrib.auth import authenticate, login, logout
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO


# ─────────────────────────────────────────────────────────────
#  FONT REGISTRATION  (done once at module load)
# ─────────────────────────────────────────────────────────────
def _register_fonts():
    try:
        # LiberationSerif ≡ Times New Roman (metric-compatible)
        pdfmetrics.registerFont(TTFont(
            'TNR',
            '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'))
        pdfmetrics.registerFont(TTFont(
            'TNR-Bold',
            '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'))
        pdfmetrics.registerFont(TTFont(
            'TNR-Italic',
            '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'))
        pdfmetrics.registerFont(TTFont(
            'TNR-BoldItalic',
            '/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf'))
        pdfmetrics.registerFontFamily(
            'TNR',
            normal='TNR', bold='TNR-Bold',
            italic='TNR-Italic', boldItalic='TNR-BoldItalic')

        # Lora – elegant serif for page title / subheadings
        pdfmetrics.registerFont(TTFont(
            'Lora',
            '/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf'))
        pdfmetrics.registerFont(TTFont(
            'Lora-Italic',
            '/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf'))

        # Poppins – clean geometric sans for section headings
        pdfmetrics.registerFont(TTFont(
            'Poppins',
            '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
        pdfmetrics.registerFont(TTFont(
            'Poppins-Bold',
            '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
        pdfmetrics.registerFont(TTFont(
            'Poppins-Medium',
            '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
        return True
    except Exception as e:
        print(f'[PDF] Font registration failed: {e}')
        return False

_FONTS_OK = _register_fonts()


# ─────────────────────────────────────────────────────────────
#  PAGE BORDER CANVAS CALLBACK
# ─────────────────────────────────────────────────────────────
class BorderedCanvas(pdfcanvas.Canvas):
    """Draws a double-rule page border + page number on every page."""

    # Sky-blue accent colour
    SKY   = colors.HexColor('#0ea5e9')
    DARK  = colors.HexColor('#0f172a')
    MID   = colors.HexColor('#64748b')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_border(total)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def _draw_border(self, page_count):
        W, H = self._pagesize
        m = 0.45 * inch          # margin from edge

        # ── Outer rule (sky blue)
        self.setStrokeColor(self.SKY)
        self.setLineWidth(2.2)
        self.rect(m, m, W - 2*m, H - 2*m)

        # ── Inner rule (thin, dark)
        inner = m + 5
        self.setStrokeColor(self.DARK)
        self.setLineWidth(0.5)
        self.rect(inner, inner, W - 2*inner, H - 2*inner)

        # ── Corner ornaments (small filled squares at each corner)
        self.setFillColor(self.SKY)
        sq = 4
        for cx, cy in [(m - sq/2, m - sq/2),
                       (W - m - sq/2, m - sq/2),
                       (m - sq/2, H - m - sq/2),
                       (W - m - sq/2, H - m - sq/2)]:
            self.rect(cx, cy, sq, sq, stroke=0, fill=1)

        # ── Page number footer
        page_num = self._pageNumber
        self.setFillColor(self.MID)
        font = 'Poppins' if _FONTS_OK else 'Helvetica'
        self.setFont(font, 7.5)
        self.drawCentredString(W / 2, m - 16, f'Page {page_num} of {page_count}')

        # ── Footer brand text (right-aligned)
        self.setFont(font, 7)
        self.setFillColor(self.SKY)
        self.drawRightString(W - m, m - 16,
                             'Sorting Visualizer  ·  Interactive Algorithm Learning Platform')


# ─────────────────────────────────────────────────────────────
#  STYLE FACTORY
# ─────────────────────────────────────────────────────────────
def _make_styles():
    """Return a dict of ParagraphStyles using the registered fonts."""
    TNR_body  = 'TNR'       if _FONTS_OK else 'Times-Roman'
    TNR_bold  = 'TNR-Bold'  if _FONTS_OK else 'Times-Bold'
    TNR_ital  = 'TNR-Italic'if _FONTS_OK else 'Times-Italic'
    Lora      = 'Lora'      if _FONTS_OK else 'Times-Bold'
    Poppins   = 'Poppins-Bold' if _FONTS_OK else 'Helvetica-Bold'
    Poppins_r = 'Poppins'   if _FONTS_OK else 'Helvetica'

    SKY  = colors.HexColor('#0ea5e9')
    DARK = colors.HexColor('#0f172a')
    BODY = colors.HexColor('#1e293b')
    MID  = colors.HexColor('#475569')
    TEAL = colors.HexColor('#0d9488')

    return {
        # ── Main report title (fancy Lora)
        'main_title': ParagraphStyle(
            'MainTitle',
            fontName=Lora,
            fontSize=28,
            textColor=DARK,
            alignment=TA_CENTER,
            spaceAfter=4,
            leading=34,
            tracking=2,
        ),
        # ── Report subtitle
        'subtitle': ParagraphStyle(
            'Subtitle',
            fontName=TNR_ital,
            fontSize=13,
            textColor=MID,
            alignment=TA_CENTER,
            spaceAfter=3,
            leading=18,
        ),
        # ── Thin sky-blue rule label above title
        'eyebrow': ParagraphStyle(
            'Eyebrow',
            fontName=Poppins,
            fontSize=7,
            textColor=SKY,
            alignment=TA_CENTER,
            spaceAfter=6,
            tracking=4,
        ),
        # ── Section headings (Poppins Bold)
        'section': ParagraphStyle(
            'Section',
            fontName=Poppins,
            fontSize=11,
            textColor=DARK,
            spaceBefore=16,
            spaceAfter=8,
            leading=16,
            borderPadding=(0, 0, 4, 0),
        ),
        # ── Sub-section headings (Poppins medium)
        'subsection': ParagraphStyle(
            'Subsection',
            fontName=Poppins_r,
            fontSize=10,
            textColor=SKY,
            spaceBefore=10,
            spaceAfter=6,
            leading=14,
        ),
        # ── Body text (Times New Roman / LiberationSerif)
        'body': ParagraphStyle(
            'Body',
            fontName=TNR_body,
            fontSize=11,
            textColor=BODY,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=17,
        ),
        # ── Caption / footnote
        'caption': ParagraphStyle(
            'Caption',
            fontName=TNR_ital,
            fontSize=9,
            textColor=MID,
            alignment=TA_CENTER,
            spaceAfter=6,
            leading=13,
        ),
        # ── Info row label
        'info_key': ParagraphStyle(
            'InfoKey',
            fontName=TNR_bold,
            fontSize=10,
            textColor=DARK,
            leading=14,
        ),
        # ── Info row value
        'info_val': ParagraphStyle(
            'InfoVal',
            fontName=TNR_body,
            fontSize=10,
            textColor=BODY,
            leading=14,
        ),
        # ── Table header cell
        'th': ParagraphStyle(
            'TH',
            fontName=Poppins,
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER,
            leading=13,
        ),
        # ── Table body cell
        'td': ParagraphStyle(
            'TD',
            fontName=TNR_body,
            fontSize=10,
            textColor=BODY,
            alignment=TA_CENTER,
            leading=14,
        ),
        # ── Table bold cell (algo names)
        'td_bold': ParagraphStyle(
            'TDBold',
            fontName=TNR_bold,
            fontSize=10,
            textColor=DARK,
            alignment=TA_LEFT,
            leading=14,
        ),
        # ── Resource link text
        'resource_link': ParagraphStyle(
            'ResLink',
            fontName=TNR_body,
            fontSize=9,
            textColor=SKY,
            leading=13,
        ),
        # ── Resource description text
        'resource_desc': ParagraphStyle(
            'ResDesc',
            fontName=TNR_body,
            fontSize=9,
            textColor=MID,
            leading=13,
        ),
        # ── Footer
        'footer': ParagraphStyle(
            'Footer',
            fontName=Poppins_r,
            fontSize=7.5,
            textColor=MID,
            alignment=TA_CENTER,
            leading=11,
        ),
    }


# ─────────────────────────────────────────────────────────────
#  HELPER: thin horizontal rule
# ─────────────────────────────────────────────────────────────
def _sky_rule(width='100%', thickness=0.8):
    return HRFlowable(
        width=width,
        thickness=thickness,
        color=colors.HexColor('#0ea5e9'),
        spaceAfter=6,
        spaceBefore=6,
    )

def _grey_rule(width='100%', thickness=0.4):
    return HRFlowable(
        width=width,
        thickness=thickness,
        color=colors.HexColor('#cbd5e1'),
        spaceAfter=4,
        spaceBefore=4,
    )


# ─────────────────────────────────────────────────────────────
#  CHART HELPERS  (matplotlib)
# ─────────────────────────────────────────────────────────────
def _bar_chart(algo_labels_map, frames_by_algo):
    algos = ['bubble', 'insertion', 'quick', 'merge']
    names = [algo_labels_map[a] for a in algos]
    vals  = [frames_by_algo.get(a, 0) for a in algos]
    bar_colors = ['#38bdf8', '#818cf8', '#34d399', '#fb923c']

    fig, ax = plt.subplots(figsize=(6.2, 2.9), dpi=120, facecolor='white')
    bars = ax.bar(names, vals, color=bar_colors, edgecolor='white',
                  linewidth=1.2, width=0.55, zorder=3)

    ax.set_facecolor('#f8fafc')
    ax.grid(axis='y', color='#e2e8f0', linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[['top','right','left']].set_visible(False)
    ax.spines['bottom'].set_color('#cbd5e1')
    ax.tick_params(axis='x', labelsize=9, colors='#334155')
    ax.tick_params(axis='y', labelsize=8, colors='#94a3b8')
    ax.set_ylabel('Number of Frames', fontsize=9, color='#475569',
                  fontfamily='DejaVu Sans', labelpad=6)

    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
                str(val), ha='center', va='bottom',
                fontsize=10, fontweight='bold', color='#1e293b')

    plt.tight_layout(pad=0.6)
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight',
                facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return buf


def _line_chart(algo_labels_map, frames_by_algo):
    algos = ['bubble', 'insertion', 'quick', 'merge']
    sorted_algos = sorted(algos, key=lambda a: frames_by_algo.get(a, 0))
    names  = [algo_labels_map[a] for a in sorted_algos]
    scores = [len(sorted_algos) - i for i in range(len(sorted_algos))]
    frames_sorted = [frames_by_algo.get(a, 0) for a in sorted_algos]

    fig, ax = plt.subplots(figsize=(6.2, 2.9), dpi=120, facecolor='white')
    ax.set_facecolor('#f8fafc')

    ax.plot(range(len(names)), scores,
            color='#0ea5e9', linewidth=2.5,
            marker='o', markersize=9,
            markerfacecolor='#fbbf24', markeredgecolor='#0ea5e9',
            markeredgewidth=1.5, zorder=4)

    ax.grid(True, color='#e2e8f0', linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[['top','right','left']].set_visible(False)
    ax.spines['bottom'].set_color('#cbd5e1')
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=9, color='#334155')
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(['Slowest', 'Slow', 'Fast', 'Fastest'], fontsize=8, color='#94a3b8')
    ax.set_ylim(0.4, 4.6)
    ax.set_xlabel('Algorithm  (ranked by efficiency)', fontsize=9,
                  color='#475569', labelpad=6)
    ax.set_ylabel('Performance', fontsize=9, color='#475569', labelpad=6)

    for i, (name, sc, fr) in enumerate(zip(names, scores, frames_sorted)):
        ax.annotate(f'{fr} frames',
                    xy=(i, sc), xytext=(0, 14),
                    textcoords='offset points',
                    ha='center', fontsize=8, color='#334155',
                    arrowprops=dict(arrowstyle='-', color='#cbd5e1',
                                   lw=0.8))

    plt.tight_layout(pad=0.6)
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight',
                facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return buf


# ─────────────────────────────────────────────────────────────
#  DJANGO VIEWS
# ─────────────────────────────────────────────────────────────
def home(request):
    if request.method == "POST":
        image = request.FILES.get("image")
        num_slices = int(request.POST.get("num_slices", 20))
        if num_slices < 5:
            num_slices = 5
        elif num_slices > 1000:
            num_slices = 1000
        obj = ImageUpload.objects.create(
            name=image.name, image=image, num_slices=num_slices)
        return redirect(f'/processing/{obj.id}/')
    return render(request, 'index.html')


def processing(request, image_id):
    return render(request, 'processing.html', {
        "redirect_url": f"/visualize/{image_id}/"
    })


def visualizer_page(request, image_id):
    return render(request, 'visualizer.html', {"image_id": image_id})


def comparison_page(request, image_id):
    return render(request, 'comparison.html', {"image_id": image_id})


def report_page(request, image_id):
    return render(request, 'report.html', {"image_id": image_id})


def sort_visual(request, image_id):
    slices = list(
        ImageSlice.objects.filter(image_id=image_id).order_by('slice_index'))
    shuffled        = get_shuffled_slices(slices)
    bubble_frames   = bubble_sort_frames(shuffled.copy())
    insertion_frames= insertion_sort_frames(shuffled.copy())
    quick_frames    = quick_sort_frames(shuffled.copy())
    merge_frames    = merge_sort_frames(shuffled.copy())
    paths = {s.id: s.image_part.url for s in slices}
    return JsonResponse({
        "initial":   [s.id for s in shuffled],
        "paths":     paths,
        "bubble":    bubble_frames,
        "insertion": insertion_frames,
        "quick":     quick_frames,
        "merge":     merge_frames,
        "stats": {
            "bubble":    {"frames": len(bubble_frames)},
            "insertion": {"frames": len(insertion_frames)},
            "quick":     {"frames": len(quick_frames)},
            "merge":     {"frames": len(merge_frames)},
        },
    })


# ─────────────────────────────────────────────────────────────
#  PDF REPORT  (fully redesigned)
# ─────────────────────────────────────────────────────────────
def generate_report_pdf(request, image_id):
    import json

    # ── 1. Fetch sort data
    data   = sort_visual(request, image_id).content
    parsed = json.loads(data)
    stats  = parsed.get("stats", {})

    algo_labels = {
        'bubble':    'Bubble Sort',
        'insertion': 'Insertion Sort',
        'quick':     'Quick Sort',
        'merge':     'Merge Sort',
    }
    complexity = {
        'bubble':    ('O(n²)',      'O(1)'),
        'insertion': ('O(n²)',      'O(1)'),
        'quick':     ('O(n log n)', 'O(log n)'),
        'merge':     ('O(n log n)', 'O(n)'),
    }

    # Frame counts
    frames_by_algo = {}
    for a in ['bubble', 'insertion', 'quick', 'merge']:
        raw = stats.get(a, 0)
        frames_by_algo[a] = raw.get('frames', 0) if isinstance(raw, dict) else raw

    # ── 2. User info
    user     = request.user
    username = user.username if user.is_authenticated else 'Anonymous'
    email    = user.email    if user.is_authenticated else 'Not provided'
    org      = 'Personal Account'
    if email and '@' in email:
        domain = email.split('@')[1].upper()
        if domain not in ('GMAIL.COM', 'YAHOO.COM', 'OUTLOOK.COM', 'HOTMAIL.COM'):
            org = domain
        else:
            org = email

    # ── 3. Styles
    S = _make_styles()
    SKY  = colors.HexColor('#0ea5e9')
    DARK = colors.HexColor('#0f172a')
    TEAL = colors.HexColor('#0d9488')
    MINT = colors.HexColor('#f0fdf4')
    SLATE= colors.HexColor('#f8fafc')

    # ── 4. Document
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=(8.5 * inch, 11 * inch),
        leftMargin   = 0.85 * inch,
        rightMargin  = 0.85 * inch,
        topMargin    = 0.75 * inch,
        bottomMargin = 0.75 * inch,
    )

    el = []   # elements list

    # ═══════════════════════════════════════════════════════
    #  PAGE 1  ·  COVER / HEADER
    # ═══════════════════════════════════════════════════════

    el.append(Spacer(1, 0.1 * inch))

    # Eyebrow
    el.append(Paragraph(
        'EXPERIMENT REPORT &amp; ANALYSIS', S['eyebrow']))

    # Thick sky-blue rule
    el.append(_sky_rule(thickness=2.5))
    el.append(Spacer(1, 0.08 * inch))

    # Main title (Lora — fancy serif)
    el.append(Paragraph('Sorting Visualizer', S['main_title']))

    el.append(Spacer(1, 0.04 * inch))

    # Subtitle (Times New Roman italic)
    el.append(Paragraph(
        'Interactive Algorithm Visualization Suite', S['subtitle']))

    el.append(Spacer(1, 0.08 * inch))
    el.append(_sky_rule(thickness=2.5))
    el.append(Spacer(1, 0.22 * inch))

    # ── Meta / info block
    info_rows = [
        [Paragraph('Platform', S['info_key']),
         Paragraph('Sorting Visualizer – Interactive Algorithm Visualization Suite', S['info_val'])],
        [Paragraph('Username', S['info_key']),
         Paragraph(username, S['info_val'])],
        [Paragraph('Email / Org', S['info_key']),
         Paragraph(org, S['info_val'])],
        [Paragraph('Report Date', S['info_key']),
         Paragraph(datetime.now().strftime('%B %d, %Y'), S['info_val'])],
        [Paragraph('Image ID', S['info_key']),
         Paragraph(str(image_id), S['info_val'])],
    ]
    info_table = Table(info_rows, colWidths=[1.3*inch, 4.9*inch])
    info_table.setStyle([
        ('BACKGROUND',    (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('BACKGROUND',    (1, 0), (1, -1), colors.white),
        ('LINEBELOW',     (0, 0), (-1, -2), 0.4, colors.HexColor('#e2e8f0')),
        ('LINEAFTER',     (0, 0), (0, -1), 0.8, SKY),
        ('BOX',           (0, 0), (-1, -1), 0.8, colors.HexColor('#cbd5e1')),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ])
    el.append(info_table)
    el.append(Spacer(1, 0.3 * inch))

    # ═══════════════════════════════════════════════════════
    #  SECTION 1  ·  INTRODUCTION
    # ═══════════════════════════════════════════════════════
    el.append(_grey_rule())
    el.append(Paragraph('1.  Introduction', S['section']))
    el.append(_grey_rule())

    el.append(Paragraph(
        'Data structures are fundamental components of computer science that organize '
        'and store data efficiently. Sorting is one of the most critical operations in '
        'data structures, enabling quick search, optimal storage, and improved algorithm '
        'performance. Understanding how different sorting algorithms work and comparing '
        'their efficiency is essential for developing optimized software solutions.',
        S['body']))

    el.append(Paragraph(
        'Sorting techniques are extensively used in software development for tasks ranging '
        'from database indexing to search-result ranking. In this visualization software '
        'we implement four fundamental sorting algorithms — Bubble Sort, Insertion Sort, '
        'Quick Sort, and Merge Sort — each with distinct time and space complexity '
        'characteristics. Quick Sort and Merge Sort demonstrate <i>O(n log n)</i> '
        'performance, while Bubble and Insertion Sort exhibit <i>O(n²)</i> behaviour, '
        'making them suitable for educational comparison. The frame-by-frame visualization '
        'allows learners to observe the actual movement of elements, bridging the gap '
        'between theoretical understanding and practical implementation.',
        S['body']))

    el.append(Spacer(1, 0.15 * inch))

    # ═══════════════════════════════════════════════════════
    #  SECTION 2  ·  RESOURCES
    # ═══════════════════════════════════════════════════════
    el.append(_grey_rule())
    el.append(Paragraph('2.  Exploration &amp; Resources', S['section']))
    el.append(_grey_rule())

    el.append(Paragraph(
        'For deeper understanding of sorting algorithms and data structures, '
        'refer to these curated external resources:',
        S['body']))
    el.append(Spacer(1, 0.06 * inch))

    # Resources table
    TNR_body = 'TNR'       if _FONTS_OK else 'Times-Roman'
    TNR_bold = 'TNR-Bold'  if _FONTS_OK else 'Times-Bold'
    Poppins  = 'Poppins-Bold' if _FONTS_OK else 'Helvetica-Bold'
    Poppins_r= 'Poppins'   if _FONTS_OK else 'Helvetica'

    res_th = ParagraphStyle('RHdr', fontName=Poppins, fontSize=9,
                            textColor=colors.white, alignment=TA_CENTER, leading=13)
    res_type = ParagraphStyle('RType', fontName=TNR_bold, fontSize=9.5,
                              textColor=DARK, leading=13)
    res_link = ParagraphStyle('RLink', fontName=TNR_body, fontSize=8.5,
                              textColor=SKY, leading=12)
    res_desc = ParagraphStyle('RDesc', fontName=TNR_body, fontSize=8.5,
                              textColor=colors.HexColor('#475569'), leading=12)

    res_rows = [
        [Paragraph('Resource Type', res_th), Paragraph('Link &amp; Description', res_th)],
        [
            Paragraph('Wikipedia', res_type),
            Paragraph(
                '<font color="#0ea5e9">https://en.wikipedia.org/wiki/Sorting_algorithm</font><br/>'
                '<font color="#475569">Comprehensive overview of sorting algorithms, '
                'their classifications, comparison methods, and detailed performance analysis.</font>',
                res_desc)
        ],
        [
            Paragraph('YouTube Tutorials', res_type),
            Paragraph(
                '<font color="#0ea5e9">https://www.youtube.com/results?search_query=sorting+algorithms+visualization</font><br/>'
                '<font color="#475569">Interactive video tutorials with step-by-step visual '
                'animations and real-world explanations.</font>',
                res_desc)
        ],
        [
            Paragraph('Research Papers', res_type),
            Paragraph(
                '<font color="#0ea5e9">https://scholar.google.com/scholar?q=sorting+algorithms+analysis</font><br/>'
                '<font color="#475569">Academic papers on algorithm analysis, complexity theory, '
                'and sorting technique research.</font>',
                res_desc)
        ],
    ]
    res_table = Table(res_rows, colWidths=[1.4*inch, 4.8*inch])
    res_table.setStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), SKY),
        ('BACKGROUND',    (0, 1), (-1, 1), colors.white),
        ('BACKGROUND',    (0, 2), (-1, 2), SLATE),
        ('BACKGROUND',    (0, 3), (-1, 3), colors.white),
        ('LINEBELOW',     (0, 0), (-1, -2), 0.4, colors.HexColor('#e2e8f0')),
        ('BOX',           (0, 0), (-1, -1), 0.8, colors.HexColor('#cbd5e1')),
        ('LINEAFTER',     (0, 0), (0, -1), 0.8, colors.HexColor('#e2e8f0')),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ])
    el.append(res_table)

    el.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    #  SECTION 3  ·  RESULTS  (page 2)
    # ═══════════════════════════════════════════════════════
    el.append(_grey_rule())
    el.append(Paragraph('3.  Results &amp; Analysis', S['section']))
    el.append(_grey_rule())

    el.append(Paragraph(
        'The following table presents the frame counts for each sorting algorithm executed '
        'on the current input set. Frame count represents the number of comparison and swap '
        'operations performed by each algorithm, directly correlating to execution efficiency.',
        S['body']))
    el.append(Spacer(1, 0.1 * inch))

    # ── Performance ranking
    sorted_algos = sorted(frames_by_algo.items(), key=lambda x: x[1])
    perf_labels  = ['⭐ Fastest', '🟠 Moderately Fast', '🟡 Moderately Slow', '🔴 Slowest']
    perf_map     = {a: perf_labels[i] for i, (a, _) in enumerate(sorted_algos)}

    # ── Results table
    td_ctr = ParagraphStyle('TDctr', fontName=TNR_body, fontSize=10,
                            textColor=colors.HexColor('#1e293b'),
                            alignment=TA_CENTER, leading=14)
    td_lft = ParagraphStyle('TDlft', fontName=TNR_bold, fontSize=10,
                            textColor=DARK, alignment=TA_LEFT, leading=14)
    th_p   = ParagraphStyle('THp',   fontName=Poppins, fontSize=9,
                            textColor=colors.white, alignment=TA_CENTER, leading=13)
    perf_p = ParagraphStyle('Perf',  fontName=TNR_body, fontSize=9,
                            textColor=TEAL, alignment=TA_CENTER, leading=13)

    res_data = [[
        Paragraph('Algorithm',        th_p),
        Paragraph('Time\nComplexity', th_p),
        Paragraph('Space\nComplexity',th_p),
        Paragraph('Frames',           th_p),
        Paragraph('Performance',      th_p),
    ]]
    for a in ['bubble', 'insertion', 'quick', 'merge']:
        tc, sc = complexity[a]
        fr     = frames_by_algo.get(a, 0)
        pf     = perf_map.get(a, '—')
        bg_row = MINT if a == sorted_algos[0][0] else None
        res_data.append([
            Paragraph(algo_labels[a], td_lft),
            Paragraph(tc,  td_ctr),
            Paragraph(sc,  td_ctr),
            Paragraph(str(fr), td_ctr),
            Paragraph(pf,  perf_p),
        ])

    # Row-level background: highlight winner
    winner_algo = sorted_algos[0][0]
    winner_row  = ['bubble','insertion','quick','merge'].index(winner_algo) + 1

    res_tbl = Table(res_data, colWidths=[1.5*inch, 1.0*inch, 1.1*inch, 0.8*inch, 1.8*inch])
    res_style = [
        ('BACKGROUND',    (0, 0), (-1, 0), SKY),
        ('LINEBELOW',     (0, 0), (-1, -2), 0.4, colors.HexColor('#e2e8f0')),
        ('BOX',           (0, 0), (-1, -1), 0.8, colors.HexColor('#94a3b8')),
        ('LINEAFTER',     (0, 0), (-1, -1), 0.4, colors.HexColor('#e2e8f0')),
        ('TOPPADDING',    (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('LEFTPADDING',   (0, 0), (-1, -1), 9),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 9),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        # Alternating rows
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, SLATE]),
        # Winner row highlight
        ('BACKGROUND',    (0, winner_row), (-1, winner_row), MINT),
        ('LINEABOVE',     (0, winner_row), (-1, winner_row), 1.2, TEAL),
        ('LINEBELOW',     (0, winner_row), (-1, winner_row), 1.2, TEAL),
    ]
    res_tbl.setStyle(res_style)
    el.append(res_tbl)
    el.append(Paragraph(
        f'★  Highlighted row indicates the fastest algorithm '
        f'({algo_labels[winner_algo]}, {frames_by_algo[winner_algo]} frames).',
        S['caption']))

    el.append(Spacer(1, 0.18 * inch))

    # ── Bar chart
    el.append(Paragraph('Frame Count Comparison', S['subsection']))
    bar_buf = _bar_chart(algo_labels, frames_by_algo)
    el.append(RLImage(bar_buf, width=5.6*inch, height=2.6*inch))
    el.append(Paragraph(
        'Bar chart showing the number of frames (comparison + swap operations) '
        'required by each algorithm on the current input.',
        S['caption']))

    el.append(Spacer(1, 0.18 * inch))

    # ── Line chart
    el.append(Paragraph('Algorithm Performance Ranking', S['subsection']))
    line_buf = _line_chart(algo_labels, frames_by_algo)
    el.append(RLImage(line_buf, width=5.6*inch, height=2.6*inch))
    el.append(Paragraph(
        'Algorithms ordered by efficiency (fewest frames = highest performance score). '
        'Lower frame count correlates directly with faster sorting.',
        S['caption']))

    el.append(Spacer(1, 0.1 * inch))
    el.append(Paragraph(
        'The visualizations above demonstrate the significant performance differences between '
        'algorithms. The <i>O(n log n)</i> algorithms (Quick Sort and Merge Sort) generally '
        'outperform their <i>O(n²)</i> counterparts, validating complexity theory predictions '
        'in real-world execution metrics.',
        S['body']))

    # ═══════════════════════════════════════════════════════
    #  SECTION 4  ·  CONCLUSION
    # ═══════════════════════════════════════════════════════
    el.append(_grey_rule())
    el.append(Paragraph('4.  Conclusion', S['section']))
    el.append(_grey_rule())

    el.append(Paragraph(
        'This visualization project successfully demonstrates the importance of selecting '
        'appropriate sorting algorithms based on problem requirements. Through interactive '
        'frame-by-frame animation, we observed how different algorithms achieve the same '
        'result with vastly different efficiency levels. The Sorting Visualizer platform has '
        'provided valuable insights into algorithmic thinking, making abstract concepts concrete '
        'and enhancing our understanding of computational complexity. By visualizing each step '
        'of the sorting process, learners can appreciate how seemingly simple operations compound '
        'into significant performance differences, emphasizing the critical role of algorithm '
        'selection in software development and system design.',
        S['body']))

    el.append(Spacer(1, 0.25 * inch))
    el.append(_sky_rule(thickness=1.5))
    el.append(Spacer(1, 0.1 * inch))
    el.append(Paragraph(
        'Generated by <b>Sorting Visualizer</b>  ·  Interactive Algorithm Learning Platform',
        S['footer']))

    # ── 5. Build PDF with bordered canvas
    doc.build(el, canvasmaker=BorderedCanvas)

    buf.seek(0)
    pdf_bytes = buf.getvalue()
    buf.close()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="sorting_report_{image_id}.pdf"')
    response['Content-Length'] = str(len(pdf_bytes))
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['Accept-Ranges']   = 'bytes'
    response['Cache-Control']   = 'no-store'
    return response


# ─────────────────────────────────────────────────────────────
#  AUTH VIEWS
# ─────────────────────────────────────────────────────────────
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('/')

def support_page(request):
    return render(request, 'support.html')

def faq_page(request):
    return render(request, 'faq.html')
