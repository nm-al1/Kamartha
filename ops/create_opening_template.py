"""Create the offline opening-data workbook using only the Python standard library."""

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs' / 'templates' / 'KAMARTHA-template-data-lama-v2.xlsx'
NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
ET.register_namespace('', NS)
ROWS = 200


def tag(name):
    return f'{{{NS}}}{name}'


def cell(row, column, value, style=0, formula=False):
    node = ET.SubElement(row, tag('c'), r=f'{column}{row.attrib["r"]}', s=str(style))
    if formula:
        ET.SubElement(node, tag('f')).text = value
    elif isinstance(value, (int, float)):
        ET.SubElement(node, tag('v')).text = str(value)
    elif value is not None:
        node.set('t', 'inlineStr')
        ET.SubElement(ET.SubElement(node, tag('is')), tag('t')).text = str(value)


def sheet(headers, widths, records=(), formulas=None, validations=(), text_columns=(), money_columns=(), table=True):
    root = ET.Element(tag('worksheet'))
    views = ET.SubElement(root, tag('sheetViews'))
    view = ET.SubElement(views, tag('sheetView'), workbookViewId='0')
    ET.SubElement(view, tag('pane'), ySplit='1', topLeftCell='A2', activePane='bottomLeft', state='frozen')
    cols = ET.SubElement(root, tag('cols'))
    for index, width in enumerate(widths, 1):
        ET.SubElement(cols, tag('col'), min=str(index), max=str(index), width=str(width), customWidth='1')
    data = ET.SubElement(root, tag('sheetData'))
    header = ET.SubElement(data, tag('row'), r='1', ht='34', customHeight='1')
    for index, title in enumerate(headers):
        cell(header, chr(65 + index), title, 1)
    count = ROWS if table else len(records)
    for index in range(count):
        number = index + 2
        row = ET.SubElement(data, tag('row'), r=str(number))
        if not table:
            row.set('ht', '60')
            row.set('customHeight', '1')
        values = records[index] if index < len(records) else []
        for col in range(len(headers)):
            column = chr(65 + col)
            formula = (formulas or {}).get(column)
            value = formula(number) if formula else values[col] if col < len(values) else None
            style = 3 if column in text_columns else 2 if column in money_columns else 0
            cell(row, column, value, style, formula is not None)
    if table:
        ET.SubElement(root, tag('autoFilter'), ref=f'A1:{chr(64 + len(headers))}{ROWS + 1}')
    if validations:
        rules = ET.SubElement(root, tag('dataValidations'), count=str(len(validations)))
        for columns, kind, first, second in validations:
            rule = ET.SubElement(rules, tag('dataValidation'), type=kind, allowBlank='1',
                                 showErrorMessage='1', errorTitle='Periksa isian',
                                 error='Gunakan nilai sesuai petunjuk.', errorStyle='stop',
                                 sqref=' '.join(f'{c}2:{c}{ROWS + 1}' for c in columns))
            if kind != 'list':
                rule.set('operator', 'between')
            ET.SubElement(rule, tag('formula1')).text = first
            if second is not None:
                ET.SubElement(rule, tag('formula2')).text = second
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def build(output=OUTPUT):
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite an existing workbook: {output}')
    prices = [
        ('1-1', 1, 1, 700000), ('1-6', 1, 6, 3500000), ('1-12', 1, 12, 7000000),
        ('2-1', 2, 1, 1000000), ('2-6', 2, 6, 5500000), ('2-12', 2, 12, 10000000),
    ]
    instructions = [
        ('Status', 'Template pengumpulan data. Unggah melalui Data awal > Impor Excel, tinjau hasil, lalu konfirmasi menjadi draft. Finalisasi terpisah.'),
        ('Mulai', 'Isi Kamar, Penghuni, Kontrak, Penempatan, lalu Sisa tagihan awal. Baris kosong boleh dibiarkan.'),
        ('Tanggal mulai pencatatan', 'Tentukan satu tanggal cutover bersama pengelola sebelum mengisi sisa tagihan.'),
        ('Kamar', 'Isi nomor unik saja. Semua kamar bertipe Standar dan maksimal 2 orang.'),
        ('Penghuni', 'Kode unik seperti P001 menghubungkan sheet. Jangan cocokkan orang hanya berdasarkan nama.'),
        ('Identitas', 'Jenis dan nomor identitas wajib untuk data siap impor. Jika belum diketahui, kosongkan dan lengkapi sebelum impor; jangan mengarang.'),
        ('Teks', 'Nomor kamar, kode, identitas dan WhatsApp disimpan sebagai teks agar nol awal tidak hilang.'),
        ('Kontrak', 'Kode unik seperti K001. Pilih jumlah penghuni paket dan durasi. Harga total paket dihitung otomatis, bukan harga bulanan.'),
        ('Tanggal', 'Isi sebagai teks YYYY-MM-DD, misalnya 2026-11-01. Tanggal akhir adalah batas akhir eksklusif sesuai kontrak, bukan hari terakhir tinggal.'),
        ('Penempatan', 'Satu baris per penghuni per kontrak. Kode harus ada di sheet terkait. Satu penanggung jawab per kontrak.'),
        ('Penghuni keluar', 'Pilih Keluar. Isi tanggal keluar; jika benar-benar tidak diketahui, kosongkan dan pilih Ya pada Keluar tidak diketahui.'),
        ('Tagihan lama', 'Isi setiap periode yang masih bersisa pada cutover DAN periode berjalan meskipun sudah lunas (sisa 0). Jangan isi semua riwayat pembayaran.'),
        ('Nilai tagihan', 'Isi nominal asli tagihan periode itu dan sisa belum dibayar. Sudah dibayar dihitung otomatis sebagai selisih.'),
        ('Tanpa tunggakan', 'Kontrak yang masih berjalan pada cutover tetap perlu baris periode berjalan dengan sisa 0 bila lunas. Periode lama lain yang lunas boleh dilewati.'),
        ('Nominal', 'Ketik angka bulat tanpa Rp atau titik, misalnya 700000. Sisa harus 0 sampai nilai tagihan; angka tidak boleh negatif.'),
        ('Paket', 'Daftar harga adalah total tetap per paket 1/6/12 bulan untuk 1/2 penghuni. Jangan mengubah tabel harga atau kolom otomatis.'),
        ('Pemeriksaan', 'Dropdown membantu pengisian, bukan pengganti validasi. Duplikat, tanggal, bentrok kamar, saldo dan relasi harus diperiksa saat impor.'),
        ('Batas', 'Tersedia 200 baris per sheet isian. Jika lebih, gunakan salinan berkas terpisah dan koordinasikan kode agar tidak duplikat.'),
        ('Keamanan', 'Berkas berisi data pribadi. Simpan privat, jangan unggah ke repositori atau kirim identitas lengkap lewat chat.'),
        ('Finalisasi', 'Impor nantinya menjadi draft Data awal. Pratinjau, rekonsiliasi dan konfirmasi tetap diperlukan sebelum finalisasi.'),
    ]
    yes_no = ('list', '"Ya,Tidak"', None)
    money = ('whole', '0', '1000000000000')
    sheets = [
        ('Petunjuk', sheet(['Bagian', 'Petunjuk pengisian'], [30, 110], instructions, table=False)),
        ('Daftar harga', sheet(['Kode paket', 'Jumlah penghuni', 'Paket bulan', 'Harga total paket'], [18, 22, 18, 25], prices, money_columns=('D',), table=False)),
        ('Kamar', sheet(['Nomor kamar'], [24], text_columns=('A',))),
        ('Penghuni', sheet(['Kode penghuni', 'Nama', 'Jenis identitas', 'Nomor identitas', 'WhatsApp (opsional)', 'Catatan (opsional)'], [20, 32, 20, 28, 26, 40], text_columns=('A', 'B', 'C', 'D', 'E', 'F'))),
        ('Kontrak', sheet(['Kode kontrak', 'Nomor kamar', 'Jumlah penghuni paket', 'Paket bulan', 'Tanggal mulai', 'Tanggal akhir eksklusif', 'Harga paket (otomatis)'], [20, 20, 25, 18, 22, 28, 28],
            formulas={'G': lambda r: f'IF(OR(C{r}="",D{r}=""),"",IFERROR(VLOOKUP(C{r}&"-"&D{r},\'Daftar harga\'!$A$2:$D$7,4,FALSE),"PERIKSA PAKET"))'},
            validations=[('C', 'list', '"1,2"', None), ('D', 'list', '"1,6,12"', None)], text_columns=('A', 'B', 'E', 'F'), money_columns=('G',))),
        ('Penempatan', sheet(['Kode kontrak', 'Kode penghuni', 'Penanggung jawab', 'Tanggal masuk', 'Status tinggal', 'Tanggal keluar (jika ada)', 'Keluar tidak diketahui'], [20, 20, 24, 22, 22, 30, 28],
            validations=[('C', *yes_no), ('E', 'list', '"Tinggal,Keluar"', None), ('G', *yes_no)], text_columns=('A', 'B', 'D', 'F'))),
        ('Sisa tagihan awal', sheet(['Kode kontrak', 'Awal periode', 'Jatuh tempo', 'Nilai tagihan', 'Sisa belum dibayar', 'Sudah dibayar (otomatis)'], [20, 22, 22, 25, 25, 30],
            formulas={'F': lambda r: f'IF(OR(D{r}="",E{r}=""),"",IF(OR(E{r}<0,E{r}>D{r},D{r}<=0),"PERIKSA SALDO",D{r}-E{r}))'},
            validations=[('DE', *money)], text_columns=('A', 'B', 'C'), money_columns=('D', 'E', 'F'))),
    ]
    styles = f'''<styleSheet xmlns="{NS}"><numFmts count="1"><numFmt numFmtId="164" formatCode='"Rp"#,##0'/></numFmts><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF142039"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="4"><xf fontId="0" fillId="0" borderId="0" numFmtId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf><xf fontId="1" fillId="2" borderId="0" numFmtId="0" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf><xf fontId="0" fillId="0" borderId="0" numFmtId="164" xfId="0" applyNumberFormat="1"/><xf fontId="0" fillId="0" borderId="0" numFmtId="49" xfId="0" applyNumberFormat="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'''
    workbook = ET.Element(tag('workbook'))
    tabs = ET.SubElement(workbook, tag('sheets'))
    for index, (name, _) in enumerate(sheets, 1):
        ET.SubElement(tabs, tag('sheet'), name=name, sheetId=str(index),
                      attrib={'{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id': f'rId{index}'})
    ET.SubElement(workbook, tag('calcPr'), calcId='191029', fullCalcOnLoad='1', forceFullCalc='1')
    relationships = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    for index in range(1, len(sheets) + 1):
        relationships += f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
    relationships += '<Relationship Id="styles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'
    types = '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
    for index in range(1, len(sheets) + 1):
        types += f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', types + '</Types>')
        archive.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="root" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        archive.writestr('xl/workbook.xml', ET.tostring(workbook, encoding='utf-8', xml_declaration=True))
        archive.writestr('xl/_rels/workbook.xml.rels', relationships)
        archive.writestr('xl/styles.xml', styles)
        for index, (_, content) in enumerate(sheets, 1):
            archive.writestr(f'xl/worksheets/sheet{index}.xml', content)
    verify(output)
    return output


def verify(path):
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            ET.fromstring(archive.read(name))
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        assert len(book.find(tag('sheets'))) == 7
        contracts = ET.fromstring(archive.read('xl/worksheets/sheet5.xml'))
        assert len(contracts.findall(f'.//{tag("f")}')) == ROWS
        assert 'Daftar harga' in contracts.find(f'.//{tag("f")}').text
        balances = ET.fromstring(archive.read('xl/worksheets/sheet7.xml'))
        assert len(balances.findall(f'.//{tag("f")}')) == ROWS
        prices = ET.fromstring(archive.read('xl/worksheets/sheet2.xml'))
        assert [int(n.text) for n in prices.findall(f'.//{tag("c")}[@s="2"]/{tag("v")}')] == [700000, 3500000, 7000000, 1000000, 5500000, 10000000]


if __name__ == '__main__':
    print(build())
