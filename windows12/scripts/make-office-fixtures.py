#!/usr/bin/env python3
"""Build a tiny public OOXML corpus; generation is not an Office compatibility test.

Standard library only. No applications, subprocesses, network, macros or external links.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import zipfile

PROJECT = Path(__file__).resolve().parent.parent
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
S = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
STAMP = (2000, 1, 1, 0, 0, 0)


def rels(items):
    return f'<Relationships xmlns="{PKG}">' + ''.join(
        f'<Relationship Id="{rid}" Type="{R}/{kind}" Target="{target}"/>'
        for rid, kind, target in items) + '</Relationships>'


def content_types(items):
    return ('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>' + ''.join(
                f'<Override PartName="/{name}" ContentType="{kind}"/>'
                for name, kind in items) + '</Types>')


def package(parts, main, types):
    parts = dict(parts)
    parts['_rels/.rels'] = rels([('rId1', 'officeDocument', main)])
    parts['[Content_Types].xml'] = content_types(types)
    buf = io.BytesIO()
    # ZIP_STORED avoids zlib/version-dependent compression output.
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, xml in sorted(parts.items()):
            ET.fromstring(xml)  # Well-formed XML only; not schema/app validation.
            info = zipfile.ZipInfo(name, STAMP)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (XML + xml).encode('utf-8'))
    return buf.getvalue()


def paragraph(text, style=None):
    props = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
    return f'<w:p>{props}<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def word():
    body = paragraph('Community garden report', 'Title')
    body += paragraph('Windows12 public Office QA fixture. No personal data.')
    body += paragraph('Season overview', 'Heading1')
    body += paragraph('Café • naïve • résumé • München • Ελληνικά • 日本語')
    body += paragraph('Three plots produced 12, 18 and 24 baskets: total 54.')
    rows = [('Plot', 'Baskets'), ('North', '12'), ('East', '18'), ('South', '24'), ('Total', '54')]
    body += ('<w:tbl><w:tblPr><w:tblW w:w="8640" w:type="dxa"/>'
             '<w:tblBorders>' + ''.join(f'<w:{side} w:val="single" w:sz="4" w:color="4472C4"/>'
                                       for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV')) +
             '</w:tblBorders></w:tblPr><w:tblGrid><w:gridCol w:w="4320"/><w:gridCol w:w="4320"/></w:tblGrid>')
    for row in rows:
        body += '<w:tr>' + ''.join('<w:tc><w:tcPr><w:tcW w:w="4320" w:type="dxa"/></w:tcPr>' +
                                     paragraph(cell) + '</w:tc>' for cell in row) + '</w:tr>'
    body += '</w:tbl>' + paragraph('Review note', 'Heading1')
    body += paragraph('Edit this sentence to: Reviewed in the test desktop.')
    body += '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
    styles = f'''<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Liberation Sans" w:hAnsi="Liberation Sans"/><w:sz w:val="22"/></w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="36"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style></w:styles>'''
    return package({'word/document.xml': f'<w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>',
                    'word/styles.xml': styles,
                    'word/_rels/document.xml.rels': rels([('rId1', 'styles', 'styles.xml')])},
                   'word/document.xml', [('word/document.xml', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'),
                                         ('word/styles.xml', 'application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml')])


def cell(ref, value, formula=None):
    if isinstance(value, str):
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
    return f'<c r="{ref}">' + (f'<f>{escape(formula)}</f>' if formula else '') + f'<v>{value}</v></c>'


def spreadsheet():
    rows = [cell('A1', 'Plot') + cell('B1', 'Baskets') + cell('C1', 'Price') + cell('D1', 'Value')]
    for n, name, count in ((2, 'North', 12), (3, 'East', 18), (4, 'South', 24)):
        rows.append(cell(f'A{n}', name) + cell(f'B{n}', count) + cell(f'C{n}', 2.5) + cell(f'D{n}', count * 2.5, f'B{n}*C{n}'))
    rows += [cell('A5', 'Total') + cell('B5', 54, 'SUM(B2:B4)') + cell('D5', 135, 'SUM(D2:D4)'),
             cell('A6', 'Average baskets') + cell('B6', 18, 'AVERAGE(B2:B4)'),
             cell('A7', 'Label') + cell('B7', 'Café / 日本語')]
    sheet = f'<worksheet xmlns="{S}"><dimension ref="A1:D7"/><sheetViews><sheetView workbookViewId="0"/></sheetViews><sheetFormatPr defaultRowHeight="15"/><cols><col min="1" max="1" width="24" customWidth="1"/><col min="2" max="4" width="18" customWidth="1"/></cols><sheetData>'
    sheet += ''.join(f'<row r="{n}">{row}</row>' for n, row in enumerate(rows, 1))
    sheet += '</sheetData><pageMargins left="0.5" right="0.5" top="0.5" bottom="0.5" header="0.3" footer="0.3"/></worksheet>'
    return package({'xl/workbook.xml': f'<workbook xmlns="{S}" xmlns:r="{R}"><bookViews><workbookView/></bookViews><sheets><sheet name="Harvest" sheetId="1" r:id="rId1"/></sheets><calcPr calcId="191029" calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"/></workbook>',
                    'xl/_rels/workbook.xml.rels': rels([('rId1', 'worksheet', 'worksheets/sheet1.xml')]),
                    'xl/worksheets/sheet1.xml': sheet}, 'xl/workbook.xml',
                   [('xl/workbook.xml', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'),
                    ('xl/worksheets/sheet1.xml', 'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml')])


def group():
    return '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'


def shape(sid, name, x, y, width, height, text, size=2400, fill=None, geom='rect'):
    paint = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else '<a:noFill/>'
    paragraphs = ''.join(f'<a:p><a:pPr/><a:r><a:rPr lang="en-US" sz="{size}"><a:solidFill><a:srgbClr val="17365D"/></a:solidFill><a:latin typeface="Liberation Sans"/></a:rPr><a:t>{escape(line)}</a:t></a:r><a:endParaRPr lang="en-US" sz="{size}"/></a:p>' for line in text.split('\n'))
    return f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{width}" cy="{height}"/></a:xfrm><a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>{paint}<a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{paragraphs}</p:txBody></p:sp>'


def presentation():
    ns = f'xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"'
    colors = [('dk1', '000000'), ('lt1', 'FFFFFF'), ('dk2', '17365D'), ('lt2', 'F2F2F2'), ('accent1', '4472C4'), ('accent2', '70AD47'), ('accent3', 'FFC000'), ('accent4', 'ED7D31'), ('accent5', '5B9BD5'), ('accent6', 'A5A5A5'), ('hlink', '0563C1'), ('folHlink', '954F72')]
    color_xml = ''.join(f'<a:{name}><a:srgbClr val="{value}"/></a:{name}>' for name, value in colors)
    # Complete theme style lists have three entries each, per DrawingML schema.
    fill = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    line = '<a:ln w="12700" cap="flat" cmpd="sng" algn="ctr">' + fill + '<a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>'
    theme = f'<a:theme xmlns:a="{A}" name="Public QA"><a:themeElements><a:clrScheme name="Public QA">{color_xml}</a:clrScheme><a:fontScheme name="Public QA">'
    for kind in ('majorFont', 'minorFont'):
        theme += f'<a:{kind}><a:latin typeface="Liberation Sans"/><a:ea typeface=""/><a:cs typeface=""/></a:{kind}>'
    theme += f'</a:fontScheme><a:fmtScheme name="Public QA"><a:fillStyleLst>{fill * 3}</a:fillStyleLst><a:lnStyleLst>{line * 3}</a:lnStyleLst><a:effectStyleLst>{"<a:effectStyle><a:effectLst/></a:effectStyle>" * 3}</a:effectStyleLst><a:bgFillStyleLst>{fill * 3}</a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>'
    cmap = '<p:clrMap accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" bg1="lt1" bg2="lt2" folHlink="folHlink" hlink="hlink" tx1="dk1" tx2="dk2"/>'
    parts = {
        'ppt/presentation.xml': f'<p:presentation {ns}><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst><p:sldId id="256" r:id="rId2"/><p:sldId id="257" r:id="rId3"/></p:sldIdLst><p:sldSz cx="12192000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>',
        'ppt/_rels/presentation.xml.rels': rels([('rId1', 'slideMaster', 'slideMasters/slideMaster1.xml'), ('rId2', 'slide', 'slides/slide1.xml'), ('rId3', 'slide', 'slides/slide2.xml'), ('rId4', 'presProps', 'presProps.xml')]),
        'ppt/presProps.xml': f'<p:presentationPr {ns}/>',
        'ppt/slideMasters/slideMaster1.xml': f'<p:sldMaster {ns}><p:cSld><p:spTree>{group()}</p:spTree></p:cSld>{cmap}<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>',
        'ppt/slideMasters/_rels/slideMaster1.xml.rels': rels([('rId1', 'slideLayout', '../slideLayouts/slideLayout1.xml'), ('rId2', 'theme', '../theme/theme1.xml')]),
        'ppt/slideLayouts/slideLayout1.xml': f'<p:sldLayout {ns} type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>{group()}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>',
        'ppt/slideLayouts/_rels/slideLayout1.xml.rels': rels([('rId1', 'slideMaster', '../slideMasters/slideMaster1.xml')]),
        'ppt/theme/theme1.xml': theme,
    }
    slides = [
        shape(2, 'Title', 600000, 400000, 10900000, 900000, 'Community garden', 3600) +
        shape(3, 'Summary', 600000, 1600000, 10900000, 1500000, 'Public Office QA fixture\nCafé • München • 日本語', 2400) +
        shape(4, 'Blue rectangle', 600000, 3500000, 4800000, 1500000, '54 baskets', 3200, 'D9E2F3') +
        shape(5, 'Green ellipse', 6600000, 3500000, 4800000, 1500000, '3 plots', 3200, 'E2F0D9', 'ellipse'),
        shape(2, 'Title', 600000, 400000, 10900000, 900000, 'Harvest review', 3600) +
        shape(3, 'Details', 600000, 1700000, 10900000, 2100000, 'North: 12 baskets\nEast: 18 baskets\nSouth: 24 baskets', 2800) +
        shape(4, 'Review box', 600000, 4400000, 10900000, 1100000, 'Edit this to: Reviewed in the test desktop.', 2400, 'FFF2CC')]
    for n, shapes in enumerate(slides, 1):
        parts[f'ppt/slides/slide{n}.xml'] = f'<p:sld {ns}><p:cSld><p:spTree>{group()}{shapes}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
        parts[f'ppt/slides/_rels/slide{n}.xml.rels'] = rels([('rId1', 'slideLayout', '../slideLayouts/slideLayout1.xml')])
    suffixes = [('ppt/presentation.xml', 'presentation.main'), ('ppt/presProps.xml', 'presProps'), ('ppt/slideMasters/slideMaster1.xml', 'slideMaster'), ('ppt/slideLayouts/slideLayout1.xml', 'slideLayout'), ('ppt/slides/slide1.xml', 'slide'), ('ppt/slides/slide2.xml', 'slide')]
    types = [(name, f'application/vnd.openxmlformats-officedocument.presentationml.{kind}+xml') for name, kind in suffixes]
    types.append(('ppt/theme/theme1.xml', 'application/vnd.openxmlformats-officedocument.theme+xml'))
    return package(parts, 'ppt/presentation.xml', types)


def safe_output(raw):
    requested = Path(raw)
    path = Path(os.path.abspath(requested if requested.is_absolute() else PROJECT / requested))
    if path == PROJECT or not path.is_relative_to(PROJECT):
        raise ValueError('output must be a directory strictly inside the project')
    # Check components before mkdir or writes; do not follow existing symlinks.
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError(f'symlink path refused: {component}')
        if component == PROJECT:
            break
    if path.exists() and not path.is_dir():
        raise ValueError('output exists and is not a directory')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='artifacts/office-fixtures', help='project-relative or absolute directory inside windows12')
    args = parser.parse_args()
    try:
        output = safe_output(args.output)
        files = {'garden-report.docx': word(), 'garden-budget.xlsx': spreadsheet(), 'garden-review.pptx': presentation()}
        expected = {
            'fixture_version': 1,
            'status': 'Generated fixture expectations only; no application or render validation performed.',
            'word': {'file': 'garden-report.docx', 'target_pages': 1, 'table_rows': 5, 'table_columns': 2,
                     'headings': ['Community garden report', 'Season overview', 'Review note'],
                     'unicode': 'Café • naïve • résumé • München • Ελληνικά • 日本語',
                     'edit': 'Reviewed in the test desktop.'},
            'spreadsheet': {'file': 'garden-budget.xlsx', 'sheet': 'Harvest',
                            'formula_cached_values': {'D2': 30, 'D3': 45, 'D4': 60, 'B5': 54, 'D5': 135, 'B6': 18},
                            'edit': 'Change B2 from 12 to 14; recalculate; save/reopen.',
                            'after_edit': {'D2': 35, 'B5': 56, 'D5': 140, 'B6': '56/3 (approximately 18.66666667)'}},
            'presentation': {'file': 'garden-review.pptx', 'slides': 2, 'aspect_ratio': '16:9',
                             'slide1_shapes': ['Blue rectangle: 54 baskets', 'Green ellipse: 3 plots'],
                             'slide2_values': [12, 18, 24], 'edit': 'Reviewed in the test desktop.'},
            'acceptance': 'See docs/OFFICE_WORKFLOW_QA.md; inspect render, edit, save/reopen and PDF export separately.'}
        files['expected.json'] = (json.dumps(expected, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')
        files['SHA256SUMS'] = ''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name, data in sorted(files.items())).encode('ascii')
        output.mkdir(parents=True, exist_ok=True)
        for name in files:
            target = output / name
            if target.is_symlink() or (target.exists() and not target.is_file()):
                raise ValueError(f'non-regular output refused: {target}')
        # Prepare every byte locally, then replace regular outputs; never truncate a
        # preexisting hardlink. No temp/cache files outside the selected directory.
        with tempfile.TemporaryDirectory(prefix='.fixture-', dir=output) as staging:
            for name, data in files.items():
                (Path(staging) / name).write_bytes(data)
            for name in files:
                safe_output(str(output))
                if (output / name).is_symlink():
                    raise ValueError(f'symlink output refused: {name}')
                os.replace(Path(staging) / name, output / name)
        print(f'Wrote {len(files)} files in {output}')
        print('OOXML generated; actual open/edit/save/reopen/export checks remain unperformed.')
    except (ValueError, OSError) as error:
        parser.exit(1, f'error: {error}\n')


if __name__ == '__main__':
    main()
