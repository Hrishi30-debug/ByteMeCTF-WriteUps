import os
import re
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

NAVY_PRIMARY = RGBColor(30, 58, 138)      # #1E3A8A
SLATE_BLUE = RGBColor(29, 78, 216)        # #1D4ED8
CHARCOAL = RGBColor(31, 41, 55)           # #1F2937
MUTED_GRAY = RGBColor(100, 116, 139)      # #64748B
GREEN_ACCENT = RGBColor(5, 150, 105)      # #059669
WHITE = RGBColor(255, 255, 255)

CODE_BG = "F8FAFC"
CALLOUT_BG = "F1F5F9"
FLAG_BG = "ECFDF5"
BORDER_GRAY = "E2E8F0"
BORDER_GREEN = "10B981"
BORDER_NAVY = "1E3A8A"
TABLE_HDR_BG = "1E3A8A"
TABLE_ROW_ALT = "F8FAFC"

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_borders(cell, top="none", bottom="none", left="none", right="none", 
                     color="CBD5E1", sz="12"):
    tcPr = cell._tc.get_or_add_tcPr()
    def border_xml(name, val, c, s):
        if val == "none":
            return f'<w:{name} w:val="none"/>'
        return f'<w:{name} w:val="{val}" w:sz="{s}" w:space="0" w:color="{c}"/>'
    
    xml = f"""
    <w:tcBorders {nsdecls("w")}>
        {border_xml("top", top, color, sz)}
        {border_xml("left", left, color, sz)}
        {border_xml("bottom", bottom, color, sz)}
        {border_xml("right", right, color, sz)}
    </w:tcBorders>
    """
    tcPr.append(parse_xml(xml))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_callout(doc, text, title=None, border_color=BORDER_NAVY, bg_color=CALLOUT_BG, text_color=CHARCOAL):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, bg_color)
    set_cell_borders(cell, left="single", color=border_color, sz="36")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=160)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    
    if title:
        run_title = p.add_run(title + "\n")
        run_title.bold = True
        run_title.font.name = "Segoe UI"
        run_title.font.size = Pt(10)
        run_title.font.color.rgb = NAVY_PRIMARY
        
    run_text = p.add_run(text)
    run_text.font.name = "Segoe UI"
    run_text.font.size = Pt(9.5)
    run_text.font.italic = True
    run_text.font.color.rgb = text_color
    
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(4)

def add_flag_box(doc, flag_text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, FLAG_BG)
    set_cell_borders(cell, top="single", bottom="single", left="single", right="single", color=BORDER_GREEN, sz="24")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    
    r_hdr = p.add_run("FLAG RECOVERED\n")
    r_hdr.bold = True
    r_hdr.font.name = "Segoe UI"
    r_hdr.font.size = Pt(9)
    r_hdr.font.color.rgb = GREEN_ACCENT
    
    r_flag = p.add_run(flag_text.strip())
    r_flag.bold = True
    r_flag.font.name = "Consolas"
    r_flag.font.size = Pt(12)
    r_flag.font.color.rgb = GREEN_ACCENT
    
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(6)

def add_code_block(doc, code_str, lang=""):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, CODE_BG)
    set_cell_borders(cell, top="single", bottom="single", left="single", right="single", color=BORDER_GRAY, sz="12")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    
    cell.paragraphs[0].text = ""
    lines = code_str.split("\n")
    for i, line in enumerate(lines):
        if i == 0:
            p = cell.paragraphs[0]
        else:
            p = cell.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.05
        
        run = p.add_run(line if line else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(30, 41, 59)
        
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(4)

def add_image_with_caption(doc, img_path, caption_text, figure_num):
    if not os.path.exists(img_path):
        print(f"Warning: Image not found at {img_path}")
        return
        
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(3)
    
    run_img = p_img.add_run()
    run_img.add_picture(img_path, width=Inches(5.8))
    
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(10)
    
    run_cap = p_cap.add_run(f"Figure {figure_num}: {caption_text}")
    run_cap.font.name = "Segoe UI"
    run_cap.font.size = Pt(9)
    run_cap.font.italic = True
    run_cap.font.color.rgb = MUTED_GRAY

def add_metadata_table(doc, meta_dict):
    table = doc.add_table(rows=len(meta_dict) + 1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    col_widths = [Inches(1.8), Inches(4.7)]
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width
            
    # Header Row
    hdr_cells = table.rows[0].cells
    set_cell_background(hdr_cells[0], TABLE_HDR_BG)
    set_cell_background(hdr_cells[1], TABLE_HDR_BG)
    set_cell_borders(hdr_cells[0], top="single", bottom="single", left="single", right="single", color=BORDER_NAVY, sz="12")
    set_cell_borders(hdr_cells[1], top="single", bottom="single", left="single", right="single", color=BORDER_NAVY, sz="12")
    set_cell_margins(hdr_cells[0], top=80, bottom=80, left=120, right=120)
    set_cell_margins(hdr_cells[1], top=80, bottom=80, left=120, right=120)
    
    p0 = hdr_cells[0].paragraphs[0]
    p0.paragraph_format.space_after = Pt(0)
    r0 = p0.add_run("Property")
    r0.bold = True
    r0.font.name = "Segoe UI"
    r0.font.size = Pt(9.5)
    r0.font.color.rgb = WHITE
    
    p1 = hdr_cells[1].paragraphs[0]
    p1.paragraph_format.space_after = Pt(0)
    r1 = p1.add_run("Details")
    r1.bold = True
    r1.font.name = "Segoe UI"
    r1.font.size = Pt(9.5)
    r1.font.color.rgb = WHITE
    
    # Data Rows
    row_idx = 1
    for key, val in meta_dict.items():
        cells = table.rows[row_idx].cells
        bg_col = TABLE_ROW_ALT if row_idx % 2 == 1 else "FFFFFF"
        set_cell_background(cells[0], bg_col)
        set_cell_background(cells[1], bg_col)
        set_cell_borders(cells[0], top="single", bottom="single", left="single", right="single", color=BORDER_GRAY, sz="8")
        set_cell_borders(cells[1], top="single", bottom="single", left="single", right="single", color=BORDER_GRAY, sz="8")
        set_cell_margins(cells[0], top=70, bottom=70, left=120, right=120)
        set_cell_margins(cells[1], top=70, bottom=70, left=120, right=120)
        
        pk = cells[0].paragraphs[0]
        pk.paragraph_format.space_after = Pt(0)
        rk = pk.add_run(key)
        rk.bold = True
        rk.font.name = "Segoe UI"
        rk.font.size = Pt(9)
        rk.font.color.rgb = NAVY_PRIMARY
        
        pv = cells[1].paragraphs[0]
        pv.paragraph_format.space_after = Pt(0)
        rv = pv.add_run(val)
        rv.font.name = "Segoe UI"
        rv.font.size = Pt(9)
        rv.font.color.rgb = CHARCOAL
        
        row_idx += 1
        
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(6)

def parse_inline_formatting(paragraph, text, base_font="Segoe UI", base_size=10):
    tokens = re.split(r'(\*\*.*?\*\*|`.*?`)', text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**'):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
            run.font.name = base_font
            run.font.size = Pt(base_size)
            run.font.color.rgb = CHARCOAL
        elif token.startswith('`') and token.endswith('`'):
            run = paragraph.add_run(token[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(base_size - 0.5)
            run.font.color.rgb = RGBColor(190, 24, 93)
        else:
            run = paragraph.add_run(token)
            run.font.name = base_font
            run.font.size = Pt(base_size)
            run.font.color.rgb = CHARCOAL

def convert_markdown_to_docx(md_path, docx_path):
    print(f"\nProcessing {md_path} -> {docx_path}")
    base_dir = os.path.dirname(md_path)
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    doc = docx.Document()
    
    # Configure 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
        # Add Header
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("ByteMe CTF Writeups  |  Official Documentation")
        hrun.font.name = "Segoe UI"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = MUTED_GRAY

        # Add Footer with Page Number
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun1 = fp.add_run("ByteMe CTF  •  Author: Pratik Jadhav  •  Page ")
        frun1.font.name = "Segoe UI"
        frun1.font.size = Pt(8.5)
        frun1.font.color.rgb = MUTED_GRAY
        
        fldSimple = OxmlElement('w:fldSimple')
        fldSimple.set(qn('w:instr'), 'PAGE')
        fp._p.append(fldSimple)

    lines = content.split('\n')
    i = 0
    num_lines = len(lines)
    
    figure_count = 1
    metadata_parsed = False
    
    while i < num_lines:
        line = lines[i]
        stripped = line.strip()
        
        if not stripped:
            i += 1
            continue
            
        # Title (H1)
        if line.startswith('# '):
            title_text = line[2:].strip()
            
            p_top = doc.add_paragraph()
            p_top.paragraph_format.space_before = Pt(0)
            p_top.paragraph_format.space_after = Pt(2)
            r_top = p_top.add_run("BYTE ME CTF  •  OFFICIAL SOLUTION WRITEUP")
            r_top.bold = True
            r_top.font.name = "Segoe UI"
            r_top.font.size = Pt(9.5)
            r_top.font.color.rgb = SLATE_BLUE
            
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(10)
            run = p.add_run(title_text)
            run.bold = True
            run.font.name = "Segoe UI"
            run.font.size = Pt(22)
            run.font.color.rgb = NAVY_PRIMARY
            i += 1
            
            # Scan immediately following lines to extract metadata into a table
            meta_dict = {}
            while i < num_lines:
                curr = lines[i].strip()
                if not curr:
                    i += 1
                    continue
                if curr.startswith('## '):
                    break
                m_match = re.match(r'^\*\*(.*?):\*\*\s*(.*)', curr)
                if m_match:
                    k = m_match.group(1).strip()
                    v = m_match.group(2).strip()
                    meta_dict[k] = v
                    i += 1
                else:
                    break
            
            if meta_dict:
                add_metadata_table(doc, meta_dict)
            continue
            
        # Headings (H2)
        if line.startswith('## '):
            h2_text = line[3:].strip()
            
            # If this is Challenge Description, let's see if there are additional Given/Target items below it
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(h2_text)
            run.bold = True
            run.font.name = "Segoe UI"
            run.font.size = Pt(13.5)
            run.font.color.rgb = SLATE_BLUE
            i += 1
            continue

        # Headings (H3)
        if line.startswith('### '):
            h3_text = line[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(h3_text)
            run.bold = True
            run.font.name = "Segoe UI"
            run.font.size = Pt(11)
            run.font.color.rgb = CHARCOAL
            i += 1
            continue
            
        # Horizontal Rule
        if stripped == '---':
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run("―" * 50)
            r.font.name = "Segoe UI"
            r.font.color.rgb = RGBColor(226, 232, 240)
            i += 1
            continue
            
        # Code Block
        if stripped.startswith('```'):
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < num_lines and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1 # skip closing ```
            
            code_text = "\n".join(code_lines)
            
            # Check if this code block is simply a flag inside the Flag section
            if ("OWASP{" in code_text or "FLAG{" in code_text) and len(code_lines) <= 3:
                add_flag_box(doc, code_text)
            else:
                add_code_block(doc, code_text, lang)
            continue
            
        # Blockquote (Lore / Description)
        if stripped.startswith('> '):
            quote_lines = []
            while i < num_lines and lines[i].strip().startswith('>'):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            quote_text = " ".join(quote_lines)
            add_callout(doc, quote_text, title="CHALLENGE BRIEFING & LORE")
            continue
            
        # Image: ![alt](path)
        img_match = re.match(r'!\[(.*?)\]\((.*?)\)', stripped)
        if img_match:
            alt_text = img_match.group(1)
            img_rel = img_match.group(2)
            full_img_path = os.path.normpath(os.path.join(base_dir, img_rel))
            add_image_with_caption(doc, full_img_path, alt_text, figure_count)
            figure_count += 1
            i += 1
            continue
            
        # Bullet list item
        if stripped.startswith('- ') or stripped.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            parse_inline_formatting(p, stripped[2:].strip(), base_font="Segoe UI", base_size=10)
            i += 1
            continue
            
        # Numbered list item
        num_match = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if num_match:
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            parse_inline_formatting(p, num_match.group(2).strip(), base_font="Segoe UI", base_size=10)
            i += 1
            continue
            
        # Regular Paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        parse_inline_formatting(p, stripped, base_font="Segoe UI", base_size=10)
        i += 1
        
    doc.save(docx_path)
    print(f"Successfully generated: {docx_path} ({os.path.getsize(docx_path)} bytes)")

def main():
    root = r"c:\Users\Pratik\Engineering\3rd Year\Owasp\general\ByteMe\Writeups\pratik"
    
    # Target challenges
    targets = [
        # Web challenges
        (os.path.join(root, "Web", "signal_console.md"), "Signal_Console_Writeup.docx"),
        (os.path.join(root, "Web", "soul_fragment_race.md"), "Soul_Fragment_Race_Writeup.docx"),
        (os.path.join(root, "Web", "soul_split.md"), "Soul_Split_Writeup.docx"),
        (os.path.join(root, "Web", "soul_trial.md"), "Soul_Trial_Writeup.docx"),
        
        # Rev challenges
        (os.path.join(root, "Rev", "soulvault.md"), "SoulVault_Writeup.docx"),
        (os.path.join(root, "Rev", "soul_ascension.md"), "Soul_Ascension_Writeup.docx"),
    ]
    
    # Unified output directory
    unified_dir = os.path.join(root, "Word_Documents")
    os.makedirs(unified_dir, exist_ok=True)
    
    for md_path, docx_name in targets:
        # Save in the category folder alongside .md
        local_docx = os.path.join(os.path.dirname(md_path), docx_name)
        convert_markdown_to_docx(md_path, local_docx)
        
        # Also copy to unified directory
        unified_docx = os.path.join(unified_dir, docx_name)
        shutil.copy2(local_docx, unified_docx)
        print(f"Copied to centralized folder: {unified_docx}")

    # Also mirror Mobile folder
    mobile_dir = os.path.join(root, "Mobile")
    for docx_name in ["SoulVault_Writeup.docx", "Soul_Ascension_Writeup.docx"]:
        src = os.path.join(unified_dir, docx_name)
        dst = os.path.join(mobile_dir, docx_name)
        shutil.copy2(src, dst)
        print(f"Mirrored to Mobile directory: {dst}")

if __name__ == "__main__":
    main()
