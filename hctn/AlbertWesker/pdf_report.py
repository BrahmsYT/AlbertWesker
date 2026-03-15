import io
import re
from collections import defaultdict
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    PageBreak,
)

from models import ScanResult, FrameworkMapping
from mapping import (
    ISO_CONTROLS, NIST_CONTROLS, SOC2_CONTROLS,
    get_framework_mappings, extract_control_id,
)

SEVERITY_COLORS = {
    "critical": colors.HexColor("#d32f2f"),
    "high": colors.HexColor("#e65100"),
    "medium": colors.HexColor("#f9a825"),
    "low": colors.HexColor("#388e3c"),
    "info": colors.HexColor("#1565c0"),
}

RISK_COLORS = {
    "Critical": colors.HexColor("#d32f2f"),
    "High": colors.HexColor("#e65100"),
    "Medium": colors.HexColor("#f9a825"),
    "Low": colors.HexColor("#388e3c"),
}

_CLR_OBSERVATION = colors.HexColor("#e65100")
_CLR_NO_OBS = colors.HexColor("#388e3c")
_CLR_REVIEW = colors.HexColor("#1565c0")
_CLR_HEADER_BG = colors.HexColor("#1a1f2b")

STRENGTH_COLORS = {
    "strong": colors.HexColor("#388e3c"),
    "moderate": colors.HexColor("#f9a825"),
    "weak": colors.HexColor("#e65100"),
}

CONFIDENCE_COLORS = {
    "high": colors.HexColor("#388e3c"),
    "medium": colors.HexColor("#f9a825"),
    "low": colors.HexColor("#e65100"),
}


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Title2", parent=ss["Title"], fontSize=20, spaceAfter=4))
    ss.add(ParagraphStyle("Meta", parent=ss["Normal"], fontSize=9, textColor=colors.grey))
    ss.add(ParagraphStyle("SectionHead", parent=ss["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6))
    ss.add(ParagraphStyle("SubSection", parent=ss["Heading3"], fontSize=11, spaceBefore=10, spaceAfter=4,
                           textColor=colors.HexColor("#263238")))
    ss.add(ParagraphStyle("FindTitle", parent=ss["Heading3"], fontSize=11, spaceBefore=8, spaceAfter=2))
    ss.add(ParagraphStyle("Small", parent=ss["Normal"], fontSize=8.5, leading=11))
    ss.add(ParagraphStyle("SmallBold", parent=ss["Normal"], fontSize=8.5, leading=11, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("CellText", parent=ss["Normal"], fontSize=7.5, leading=9.5))
    ss.add(ParagraphStyle("Footer", parent=ss["Normal"], fontSize=7.5, textColor=colors.grey, alignment=1))
    ss.add(ParagraphStyle("BodyText2", parent=ss["Normal"], fontSize=9, leading=12, spaceBefore=4, spaceAfter=4))
    ss.add(ParagraphStyle("Caveat", parent=ss["Normal"], fontSize=8, leading=10,
                           textColor=colors.HexColor("#616161"), spaceBefore=2, spaceAfter=6))
    return ss


# ────────────────────────────────────────────
# Helpers for building rich control tables
# ────────────────────────────────────────────

def _build_control_findings_map(findings):
    """Return per-framework dicts: {control_id: list[FrameworkMapping]}"""
    iso_map: dict[str, list[FrameworkMapping]] = defaultdict(list)
    nist_map: dict[str, list[FrameworkMapping]] = defaultdict(list)
    soc2_map: dict[str, list[FrameworkMapping]] = defaultdict(list)

    for f in findings:
        for m in f.framework_mappings:
            if m.framework.startswith("ISO"):
                iso_map[m.control_id].append(m)
            elif m.framework.startswith("NIST"):
                nist_map[m.control_id].append(m)
            elif m.framework.startswith("SOC"):
                soc2_map[m.control_id].append(m)
    return iso_map, nist_map, soc2_map


def _best_mapping_attrs(mappings: list[FrameworkMapping]):
    """Given a list of mappings for one control, pick the strongest/highest-confidence."""
    str_order = {"strong": 0, "moderate": 1, "weak": 2}
    conf_order = {"high": 0, "medium": 1, "low": 2}
    best = min(mappings, key=lambda m: (str_order.get(m.mapping_strength, 3), conf_order.get(m.confidence, 3)))
    return best.mapping_strength, best.evidence_type, best.confidence, best.manual_review


def _status_cell(ss, mappings: list[FrameworkMapping] | None):
    """Return a Paragraph for the Status column — observation / no observation / needs review."""
    if not mappings:
        return Paragraph(f'<font color="{_CLR_NO_OBS.hexval()}">No Observation</font>', ss["CellText"])
    strength, etype, conf, needs_review = _best_mapping_attrs(mappings)
    if needs_review:
        return Paragraph(f'<font color="{_CLR_REVIEW.hexval()}">Needs Review</font>', ss["CellText"])
    return Paragraph(f'<font color="{_CLR_OBSERVATION.hexval()}">Observation</font>', ss["CellText"])


def _framework_table(ss, control_catalog, triggered_map, framework_name, all_findings):
    """Build a controls alignment table for one framework — NO PASS/FAIL language."""
    elements = []
    total = len(control_catalog)
    obs_count = len(triggered_map)
    clean_count = total - obs_count

    elements.append(Paragraph(
        f"Controls evaluated: {total} | "
        f'<font color="{_CLR_NO_OBS.hexval()}">No observations: {clean_count}</font> | '
        f'<font color="{_CLR_OBSERVATION.hexval()}">Observations: {obs_count}</font>',
        ss["Small"],
    ))
    elements.append(Spacer(1, 6))

    header = ["Control ID", "Control Description", "Status", "Strength", "Evidence", "Confidence"]
    rows = [header]

    # Build a mapping from control_id -> list of finding codes for the "Related Findings" context
    ctrl_finding_codes: dict[str, list[str]] = defaultdict(list)
    for f in all_findings:
        for m in f.framework_mappings:
            if m.control_id in control_catalog:
                ctrl_finding_codes[m.control_id].append(f.code)

    for ctrl_id, description in sorted(control_catalog.items()):
        mappings = triggered_map.get(ctrl_id)
        status = _status_cell(ss, mappings)
        if mappings:
            strength, etype, conf, _ = _best_mapping_attrs(mappings)
            str_clr = STRENGTH_COLORS.get(strength, colors.black).hexval()
            conf_clr = CONFIDENCE_COLORS.get(conf, colors.black).hexval()
            strength_p = Paragraph(f'<font color="{str_clr}">{strength.title()}</font>', ss["CellText"])
            etype_p = Paragraph(etype.title(), ss["CellText"])
            conf_p = Paragraph(f'<font color="{conf_clr}">{conf.title()}</font>', ss["CellText"])
        else:
            strength_p = Paragraph("\u2014", ss["CellText"])
            etype_p = Paragraph("\u2014", ss["CellText"])
            conf_p = Paragraph("\u2014", ss["CellText"])
        rows.append([ctrl_id, Paragraph(description, ss["CellText"]), status, strength_p, etype_p, conf_p])

    tbl = Table(rows, colWidths=[48, 170, 62, 52, 52, 52], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("BACKGROUND", (0, 0), (-1, 0), _CLR_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
    ]))
    elements.append(tbl)
    return elements


def generate_pdf(result: ScanResult, lang: str = "en") -> bytes:
    # Language translations for PDF
    translations = {
        "en": {
            "title": "External Security Posture &amp; Compliance Alignment Report",
            "generated": "Generated",
            "reference": "Reference frameworks",
            "caveat": "This report reflects <b>external technical indicators only</b>. It is not a compliance audit, certification, or attestation.",
            "executive_summary": "1. Executive Summary",
            "target_domain": "Target Domain",
            "risk_score": "External Risk Score",
            "risk_indicator": "Risk Indicator",
            "technical_observations": "Technical Observations",
            "critical": "Critical",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
            "tls_version": "TLS Version",
            "cert_expires": "Cert Expires In",
            "cert_issuer": "Cert Issuer",
            "server": "Server",
            "resolved_ips": "Resolved IPs",
            "status": "Status",
            "scope_methodology": "Scope &amp; Methodology",
        },
        "az": {
            "title": "Xarici Təhlükəsizlik Vəziyyəti &amp; Uyğunluq Sərtiləşdirmə Hesabatı",
            "generated": "Hazırlanıb",
            "reference": "İstinad çərçivələri",
            "caveat": "Bu hesabat <b>yalnız xarici texniki göstəriciləri əks etdirir</b>. Bu, uyğunluq audibi, sertifikatı və ya attestasiyası deyildir.",
            "executive_summary": "1. Xülasə",
            "target_domain": "Hədəf Domain",
            "risk_score": "Xarici Risk Sürəti",
            "risk_indicator": "Risk Göstəricisi",
            "technical_observations": "Texniki Müşahidələr",
            "critical": "Kritik",
            "high": "Yüksək",
            "medium": "Orta",
            "low": "Aşağı",
            "tls_version": "TLS Versiyası",
            "cert_expires": "Sertifikat Müddəti Bitir",
            "cert_issuer": "Sertifikat Vericisi",
            "server": "Server",
            "resolved_ips": "Həll Edilmiş IP-lər",
            "status": "Status",
            "scope_methodology": "Miqyas &amp; Metodologiya",
        },
        "ru": {
            "title": "Отчет о позиции безопасности и соответствии нормам",
            "generated": "Создано",
            "reference": "Справочные фреймворки",
            "caveat": "Этот отчет отражает <b>только внешние технические индикаторы</b>. Это не аудит соответствия, сертификат или аттестация.",
            "executive_summary": "1. Резюме",
            "target_domain": "Целевой домен",
            "risk_score": "Внешний показатель риска",
            "risk_indicator": "Индикатор риска",
            "technical_observations": "Технические наблюдения",
            "critical": "Критическое",
            "high": "Высокое",
            "medium": "Среднее",
            "low": "Низкое",
            "tls_version": "Версия TLS",
            "cert_expires": "Сертификат истекает",
            "cert_issuer": "Издатель сертификата",
            "server": "Сервер",
            "resolved_ips": "Разрешенные IP-адреса",
            "status": "Статус",
            "scope_methodology": "Масштаб и методология",
        }
    }
    
    t = translations.get(lang, translations["en"])
    
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )
    ss = _styles()
    story: list = []
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    # ═══════════════════════════════════════════════
    # 1. TITLE
    # ═══════════════════════════════════════════════
    story.append(Paragraph(t["title"], ss["Title2"]))
    story.append(Paragraph(
        f"{t['generated']}: {now_str} | "
        f"{t['reference']}: ISO 27001 \u00b7 NIST SP 800-53 \u00b7 SOC 2",
        ss["Meta"],
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(t["caveat"], ss["Caveat"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 10))

    # ═══════════════════════════════════════════════
    # 2. EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════
    story.append(Paragraph(t["executive_summary"], ss["SectionHead"]))
    risk_color = RISK_COLORS.get(result.risk_label, colors.black)

    summary_data = [
        [t["target_domain"], result.target],
        [t["risk_score"], f"{result.risk_score} / 100"],
        [t["risk_indicator"], result.risk_label],
        [t["technical_observations"], str(len(result.findings))],
    ]

    sev_counts: dict[str, int] = {}
    for f in result.findings:
        sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1
    for sev in ("critical", "high", "medium", "low"):
        if sev_counts.get(sev, 0) > 0:
            summary_data.append([f"  {t[sev].capitalize()}", str(sev_counts[sev])])

    meta = result.scan_meta
    tls = meta.get("tls", {})
    if tls.get("protocol"):
        summary_data.append([t["tls_version"], tls["protocol"]])
    if tls.get("days_until_expiry") is not None:
        summary_data.append([t["cert_expires"], f"{tls['days_until_expiry']} days"])
    issuer = tls.get("issuer", {})
    if issuer:
        summary_data.append([t["cert_issuer"], issuer.get("organizationName", issuer.get("commonName", "N/A"))])
    http_meta = meta.get("http", {})
    if http_meta.get("server"):
        summary_data.append([t["server"], http_meta["server"]])
    dns = meta.get("dns", {})
    if dns.get("resolved_ips"):
        summary_data.append([t["resolved_ips"], ", ".join(dns["resolved_ips"][:4])])

    if result.is_whitelisted:
        summary_data.append([t["status"], "TRUSTED (Whitelisted)"])

    tbl = Table(summary_data, colWidths=[120, 350])
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TEXTCOLOR", (0, 2), (1, 2), risk_color),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8))

    # Scope & Methodology
    story.append(Paragraph(t["scope_methodology"], ss["SubSection"]))
    
    scope_text_en = (
        f"This automated assessment evaluated the <b>external</b> security posture of <b>{result.target}</b> "
        "using non-intrusive techniques: TLS/certificate analysis, HTTP security header inspection, "
        "cookie attribute verification, HTTPS redirect validation, DNS resolution, and TCP port scanning with "
        "limited service banner detection."
    )
    scope_text_az = (
        f"Bu avtomatlaşdırılmış qiymətləndirmə <b>{result.target}</b> <b>xarici</b> təhlükəsizlik vəziyyətini "
        "qeyri-invaziv metodlarla qiymətləndirdi: TLS/sertifikat analizi, HTTP təhlükəsizlik başlığı inspeksiyası, "
        "cookie atribut yoxlanılması, HTTPS yönləndirmə validasiyası, DNS məlumatlandırması və TCP port skanı."
    )
    scope_text_ru = (
        f"Это автоматизированная оценка внешней позиции безопасности <b>{result.target}</b> "
        "с использованием неинвазивных методов: анализ TLS/сертификата, проверка заголовков безопасности HTTP, "
        "проверка атрибутов cookies, проверка редиректов HTTPS, разрешение DNS и сканирование портов TCP."
    )
    scope_texts = {"en": scope_text_en, "az": scope_text_az, "ru": scope_text_ru}
    story.append(Paragraph(scope_texts.get(lang, scope_text_en), ss["BodyText2"]))
    
    mapping_text_en = (
        "Findings are mapped to related controls from ISO/IEC 27001:2022, NIST SP 800-53 Rev. 5, "
        "and SOC 2 Trust Service Criteria. Each mapping includes a <b>mapping strength</b> "
        "(strong / moderate / weak), <b>evidence type</b> (direct / indirect / heuristic), "
        "and <b>confidence level</b> (high / medium / low) to indicate how reliably the external "
        "finding reflects the underlying control's status."
    )
    mapping_text_az = (
        "Tapıntılar ISO/IEC 27001:2022, NIST SP 800-53 Rev. 5 və SOC 2 Trust Service Criteria ilə əlaqəli "
        "kontrollara uyğunlaşdırılır. Hər bir uyğunlaşdırma <b>uyğunlaşdırma gücü</b> "
        "(güclü / orta / zəif), <b>sübut tipi</b> (birbaşa / dolayı / heuristic) və "
        "<b>etibar səviyyəsi</b> (yüksək / orta / aşağı) ehtiva edir."
    )
    mapping_text_ru = (
        "Выводы сопоставлены с соответствующими элементами управления из ISO/IEC 27001:2022, NIST SP 800-53 Rev. 5 "
        "и SOC 2 Trust Service Criteria. Каждое сопоставление включает <b>силу сопоставления</b> "
        "(сильная / средняя / слабая), <b>тип доказательства</b> (прямое / косвенное / эвристическое) и "
        "<b>уровень доверия</b> (высокий / средний / низкий)."
    )
    mapping_texts = {"en": mapping_text_en, "az": mapping_text_az, "ru": mapping_text_ru}
    story.append(Paragraph(mapping_texts.get(lang, mapping_text_en), ss["BodyText2"]))
    
    limitations_text_en = (
        "<b>Limitations:</b> This scan cannot evaluate internal policies, procedures, access controls, "
        "organizational governance, employee training, or any control that requires authenticated or "
        "insider access. Controls marked \"Needs Review\" require manual assessment by a qualified auditor."
    )
    limitations_text_az = (
        "<b>Məhdudiyyətlər:</b> Bu skan daxili siyasətləri, prosedurları, girişin nəzarətini, "
        "təşkilati rəhbərliyi, işçi təlimini və ya kimlik təsdiqləməsi tələb edən hər hansı nəzarəti "
        "qiymətləndirə bilməz. \"Nəzərdən Keçirilmə Lazımdır\" kimi qeyd edilən nəzarətlər."
    )
    limitations_text_ru = (
        "<b>Ограничения:</b> Это сканирование не может оценить внутренние политики, процедуры, контроль доступа, "
        "организационное управление, обучение сотрудников или любой контроль, требующий аутентификации или "
        "внутреннего доступа. Элементы управления, отмеченные как \"Требуется проверка\", нуждаются в."
    )
    limitations_texts = {"en": limitations_text_en, "az": limitations_text_az, "ru": limitations_text_ru}
    story.append(Paragraph(limitations_texts.get(lang, limitations_text_en), ss["Caveat"]))
    story.append(Spacer(1, 6))

    # ═══════════════════════════════════════════════
    # 3. COMPLIANCE ALIGNMENT OVERVIEW
    # ═══════════════════════════════════════════════
    iso_map, nist_map, soc2_map = _build_control_findings_map(result.findings)
    
    compliance_titles = {
        "en": "2. Compliance Alignment Overview",
        "az": "2. Uyğunluq Sərtiləşdirmə İcmalı",
        "ru": "2. Обзор соответствия нормам"
    }
    story.append(Paragraph(compliance_titles.get(lang, compliance_titles["en"]), ss["SectionHead"]))
    
    compliance_text_en = (
        "Summary of externally observable signals mapped to each framework. "
        "\"Observations\" indicate potential concerns detected from the external scan \u2014 "
        "they are <b>not</b> compliance failures. Full compliance can only be determined by a formal audit."
    )
    compliance_text_az = (
        "Hər bir çərçivəyə uyğunlaşdırılmış xarici müşahidə edilən siqnalların xülasəsi. "
        "\"Müşahidələr\" xarici scandan aşkar edilən potensial narahatlıqları göstərir \u2014 "
        "bunlar <b>deyil</b> uyğunluq uğursuzluğudur. Tam uyğunluq yalnız rəsmi auditlendirməsi ilə müəyyən edilə bilər."
    )
    compliance_text_ru = (
        "Резюме внешних наблюдаемых сигналов, сопоставленных с каждой структурой. "
        "\"Наблюдения\" указывают на потенциальные проблемы, обнаруженные при внешнем сканировании \u2014 "
        "они <b>не</b> являются отказом в соответствии. Полное соответствие может быть определено только формальным аудитом."
    )
    compliance_texts = {"en": compliance_text_en, "az": compliance_text_az, "ru": compliance_text_ru}
    story.append(Paragraph(compliance_texts.get(lang, compliance_text_en), ss["BodyText2"]))

    def _fw_stats(catalog, triggered):
        total = len(catalog)
        obs = len(triggered)
        return total, total - obs, obs

    iso_total, iso_clean, iso_obs = _fw_stats(ISO_CONTROLS, iso_map)
    nist_total, nist_clean, nist_obs = _fw_stats(NIST_CONTROLS, nist_map)
    soc2_total, soc2_clean, soc2_obs = _fw_stats(SOC2_CONTROLS, soc2_map)

    matrix_headers = {
        "en": ["Framework", "Controls Evaluated", "No Observations", "Observations", "External Alignment"],
        "az": ["Çərçivə", "Qiymətləndirilib", "Müşahidə Yoxdur", "Müşahidələr", "Xarici Sərtiləşdirmə"],
        "ru": ["Структура", "Оценено элементов", "Нет наблюдений", "Наблюдения", "Внешнее соответствие"]
    }
    
    matrix_data = [matrix_headers.get(lang, matrix_headers["en"])]

    def _alignment_label(clean, total):
        pct = round(clean / total * 100) if total else 100
        no_concerns = {
            "en": "no external concerns",
            "az": "xarici narahatlıq yoxdur",
            "ru": "нет внешних проблем"
        }
        prelim_estimate = {
            "en": "preliminary estimate",
            "az": "ilkin qiymətləndirmə",
            "ru": "предварительная оценка"
        }
        if pct == 100:
            return f"{pct}% ({no_concerns.get(lang, 'no external concerns')})"
        return f"~{pct}% ({prelim_estimate.get(lang, 'preliminary estimate')})"

    matrix_data.append([
        "ISO/IEC 27001:2022", str(iso_total),
        Paragraph(f'<font color="{_CLR_NO_OBS.hexval()}">{iso_clean}</font>', ss["CellText"]),
        Paragraph(f'<font color="{_CLR_OBSERVATION.hexval()}">{iso_obs}</font>', ss["CellText"]),
        _alignment_label(iso_clean, iso_total),
    ])
    matrix_data.append([
        "NIST SP 800-53 Rev. 5", str(nist_total),
        Paragraph(f'<font color="{_CLR_NO_OBS.hexval()}">{nist_clean}</font>', ss["CellText"]),
        Paragraph(f'<font color="{_CLR_OBSERVATION.hexval()}">{nist_obs}</font>', ss["CellText"]),
        _alignment_label(nist_clean, nist_total),
    ])
    matrix_data.append([
        "SOC 2 Type II", str(soc2_total),
        Paragraph(f'<font color="{_CLR_NO_OBS.hexval()}">{soc2_clean}</font>', ss["CellText"]),
        Paragraph(f'<font color="{_CLR_OBSERVATION.hexval()}">{soc2_obs}</font>', ss["CellText"]),
        _alignment_label(soc2_clean, soc2_total),
    ])

    mtbl = Table(matrix_data, colWidths=[120, 72, 72, 68, 130], repeatRows=1)
    mtbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 0), (-1, 0), _CLR_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (3, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
    ]))
    story.append(mtbl)
    story.append(Spacer(1, 4))
    
    caveat_text_en = (
        "\u26a0 \"External Alignment\" is a preliminary estimate based on observable signals only. "
        "It must not be cited as a compliance percentage."
    )
    caveat_text_az = (
        "\u26a0 \"Xarici Sərtiləşdirmə\" yalnız müşahidə olunan siqnallara əsaslanan ilkin qiymətləndirmədir. "
        "Bunu uyğunluq faiz nisbəti kimi göstərilə bilməz."
    )
    caveat_text_ru = (
        "\u26a0 \"Внешнее соответствие\" является предварительной оценкой, основанной только на наблюдаемых сигналах. "
        "Его нельзя цитировать как процент соответствия."
    )
    caveat_texts = {"en": caveat_text_en, "az": caveat_text_az, "ru": caveat_text_ru}
    story.append(Paragraph(caveat_texts.get(lang, caveat_text_en), ss["Caveat"]))
    story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════
    # 4. ISO 27001 CONTROLS ALIGNMENT
    # ═══════════════════════════════════════════════
    story.append(PageBreak())
    
    iso_titles = {
        "en": "3. ISO/IEC 27001:2022 \u2014 External Controls Alignment",
        "az": "3. ISO/IEC 27001:2022 \u2014 Xarici Nəzarət Sərtiləşdirməsi",
        "ru": "3. ISO/IEC 27001:2022 \u2014 Выравнивание внешних элементов управления"
    }
    story.append(Paragraph(iso_titles.get(lang, iso_titles["en"]), ss["SectionHead"]))
    
    iso_text_en = (
        "External signals mapped to applicable Annex A controls. \"Observation\" means an external "
        "indicator was detected \u2014 it does not confirm non-compliance without internal review."
    )
    iso_text_az = (
        "Tətbiq olunan Əlavə A nəzarətlərinə uyğunlaşdırılmış xarici siqnallar. \"Müşahidə\" xarici "
        "göstəricinin aşkar edilməsi deməkdir \u2014 bu, daxili nəzarədən sonra qeyri-uyğunluğu təsdiq etmir."
    )
    iso_text_ru = (
        "Внешние сигналы, сопоставленные с применимыми элементами управления Приложения A. \"Наблюдение\" означает, что был обнаружен внешний "
        "индикатор \u2014 это не подтверждает несоответствие без внутреннего анализа."
    )
    iso_texts = {"en": iso_text_en, "az": iso_text_az, "ru": iso_text_ru}
    story.append(Paragraph(iso_texts.get(lang, iso_text_en), ss["Caveat"]))
    story.extend(_framework_table(ss, ISO_CONTROLS, iso_map, "ISO 27001", result.findings))
    story.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════
    # 5. NIST SP 800-53 CONTROLS ALIGNMENT
    # ═══════════════════════════════════════════════
    nist_titles = {
        "en": "4. NIST SP 800-53 Rev. 5 \u2014 External Controls Alignment",
        "az": "4. NIST SP 800-53 Rev. 5 \u2014 Xarici Nəzarət Sərtiləşdirməsi",
        "ru": "4. NIST SP 800-53 Rev. 5 \u2014 Выравнивание внешних элементов управления"
    }
    story.append(Paragraph(nist_titles.get(lang, nist_titles["en"]), ss["SectionHead"]))
    
    nist_text_en = (
        "External signals mapped to applicable security controls. Observations indicate areas "
        "where external evidence suggests a potential gap in the technical implementation."
    )
    nist_text_az = (
        "Tətbiq olunan təhlükəsizlik nəzarətlərinə uyğunlaşdırılmış xarici siqnallar. Müşahidələr "
        "xarici sübütün texniki tətbiqdə potensial boşluğu göstərdiyini göstərir."
    )
    nist_text_ru = (
        "Внешние сигналы, сопоставленные с применимыми элементами управления безопасностью. Наблюдения указывают на области, "
        "где внешние доказательства указывают на потенциальный пробел в техническом внедрении."
    )
    nist_texts = {"en": nist_text_en, "az": nist_text_az, "ru": nist_text_ru}
    story.append(Paragraph(nist_texts.get(lang, nist_text_en), ss["Caveat"]))
    story.extend(_framework_table(ss, NIST_CONTROLS, nist_map, "NIST SP 800-53", result.findings))
    story.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════
    # 6. SOC 2 TRUST SERVICE CRITERIA ALIGNMENT
    # ═══════════════════════════════════════════════
    soc2_titles = {
        "en": "5. SOC 2 Type II \u2014 Trust Service Criteria Alignment",
        "az": "5. SOC 2 Type II \u2014 İnanc Xidməti Kriteriyası Sərtiləşdirmə",
        "ru": "5. SOC 2 Type II \u2014 Выравнивание критериев Trust Service"
    }
    story.append(Paragraph(soc2_titles.get(lang, soc2_titles["en"]), ss["SectionHead"]))
    
    soc2_text_en = (
        "External signals mapped to Common Criteria (CC). SOC 2 compliance depends on policies, "
        "procedures, and organizational controls that cannot be assessed externally."
    )
    soc2_text_az = (
        "Ümumi Kriteriyalara (CC) uyğunlaşdırılmış xarici siqnallar. SOC 2 uyğunluğu siyasətlərdən, "
        "prosedurlardan və xarici olaraq qiymətləndirilə bilinməyən təşkilati nəzarətlərdən asılıdır."
    )
    soc2_text_ru = (
        "Внешние сигналы, сопоставленные с Common Criteria (CC). Соответствие SOC 2 зависит от политик, "
        "процедур и организационных элементов управления, которые невозможно оценить внешне."
    )
    soc2_texts = {"en": soc2_text_en, "az": soc2_text_az, "ru": soc2_text_ru}
    story.append(Paragraph(soc2_texts.get(lang, soc2_text_en), ss["Caveat"]))
    story.extend(_framework_table(ss, SOC2_CONTROLS, soc2_map, "SOC 2", result.findings))
    story.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════
    # 7. PORT SCAN RESULTS
    # ═══════════════════════════════════════════════
    ports_meta = meta.get("ports", {})
    open_ports = ports_meta.get("open_ports", [])
    if ports_meta:
        story.append(PageBreak())
        
        port_titles = {
            "en": "6. Port Scan Results",
            "az": "6. Port Skan Nəticələri",
            "ru": "6. Результаты сканирования портов"
        }
        story.append(Paragraph(port_titles.get(lang, port_titles["en"]), ss["SectionHead"]))
        
        scanned_text = {
            "en": "Scanned",
            "az": "Skanlanıb",
            "ru": "Отсканировано"
        }
        open_text = {
            "en": "Open",
            "az": "Açıq",
            "ru": "Открыто"
        }
        closed_text = {
            "en": "Closed",
            "az": "Qapalı",
            "ru": "Закрыто"
        }
        
        story.append(Paragraph(
            f"{scanned_text.get(lang)}: {ports_meta.get('total_scanned', 0)} ports | "
            f"{open_text.get(lang)}: {ports_meta.get('open_count', 0)} | "
            f"{closed_text.get(lang)}: {ports_meta.get('closed_count', 0)}",
            ss["Small"],
        ))
        story.append(Spacer(1, 6))

        if open_ports:
            port_headers = {
                "en": ["Port", "Service", "Version / Banner", "Risk"],
                "az": ["Port", "Xidmət", "Versiya / Banner", "Risk"],
                "ru": ["Порт", "Сервис", "Версия / Баннер", "Риск"]
            }
            port_data = [port_headers.get(lang, port_headers["en"])]
            
            ok_text = {
                "en": "OK",
                "az": "OK",
                "ru": "OK"
            }
            
            for p in open_ports:
                risk_label = p["severity"].upper() if p["risky"] else ok_text.get(lang, "OK")
                banner = p.get("banner", "") or "\u2014"
                port_data.append([str(p["port"]), p["service"], Paragraph(banner[:80], ss["Small"]), risk_label])

            pt = Table(port_data, colWidths=[45, 100, 200, 50], repeatRows=1)
            pt.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BACKGROUND", (0, 0), (-1, 0), _CLR_HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ]))
            story.append(pt)
        else:
            no_ports_text = {
                "en": "No open ports detected.",
                "az": "Açıq port aşkar edilmədi.",
                "ru": "Открытых портов не обнаружено."
            }
            story.append(Paragraph(no_ports_text.get(lang, no_ports_text["en"]), ss["Small"]))
        story.append(Spacer(1, 12))

    # ═══════════════════════════════════════════════
    # 7. AWS SECURITY ASSESSMENT (if applicable)
    # ═══════════════════════════════════════════════
    # 7. AWS-SPECIFIC SECURITY ASSESSMENT (MANDATORY)
    # ═══════════════════════════════════════════════
    aws_summary = result.scan_meta.get("aws_summary", {})
    aws_findings = [f for f in result.findings if f.code.startswith("AWS_")]
    
    # AWS section ALWAYS shown (per Requirement 10)
    story.append(PageBreak())
    
    aws_assessment_title = {
        "en": "7. AWS-Specific Security Assessment",
        "az": "7. AWS-Spesifik Təhlükəsizlik Qiymətləndirməsi",
        "ru": "7. Оценка безопасности AWS"
    }
    story.append(Paragraph(aws_assessment_title.get(lang, aws_assessment_title["en"]), ss["SectionHead"]))
    
    aws_caveat_text = {
        "en": "External signals indicative of AWS infrastructure and potential AWS-specific security weaknesses. AWS services detected are based on DNS/HTTP headers and domain name patterns.",
        "az": "AWS infrastrukturunun xarici siqnalları və potensial AWS-spesifik təhlükəsizlik zəifliklərini göstərir. Aşkar edilən AWS xidmətləri DNS/HTTP başlıqları və domen adı şablonlarına əsaslanır.",
        "ru": "Внешние сигналы, указывающие на инфраструктуру AWS и потенциальные слабости безопасности AWS. Обнаруженные сервисы AWS основаны на заголовках DNS/HTTP и шаблонах имен доменов."
    }
    story.append(Paragraph(aws_caveat_text.get(lang, aws_caveat_text["en"]), ss["Caveat"]))
    story.append(Spacer(1, 8))

    # AWS Summary subheader
    aws_score_contribution = aws_summary.get("aws_score_contribution", 0)
    aws_risk_label = aws_summary.get("aws_risk_label", "None")
    aws_risk_color = RISK_COLORS.get(aws_risk_label, colors.black)

    aws_summary_subtitle = {
        "en": "AWS Security Posture Summary",
        "az": "AWS Təhlükəsizlik Vəziyyəti Xülasəsi",
        "ru": "Резюме безопасности AWS"
    }
    story.append(Paragraph(aws_summary_subtitle.get(lang, aws_summary_subtitle["en"]), ss["SubSection"]))
    
    aws_labels = {
        "risk_contribution": {"en": "AWS Risk Contribution", "az": "AWS Risk Kontribusiyası", "ru": "Вклад AWS в риск"},
        "indicator": {"en": "AWS Risk Indicator", "az": "AWS Risk Göstəricisi", "ru": "Индикатор риска AWS"},
        "findings": {"en": "AWS Findings", "az": "AWS Tapıntıları", "ru": "Выводы AWS"},
        "services": {"en": "Services Detected", "az": "Aşkar Edilən Xidmətlər", "ru": "Обнаруженные услуги"},
    }

    aws_summary_data = [
        [aws_labels["risk_contribution"].get(lang), f"{aws_score_contribution} / 100"],
        [aws_labels["indicator"].get(lang), aws_risk_label],
        [aws_labels["findings"].get(lang), str(aws_summary.get("aws_findings_count", 0))],
    ]
    
    services = aws_summary.get("aws_services_detected", [])
    if services:
        aws_summary_data.append([aws_labels["services"].get(lang), ", ".join(services)])

    aws_tbl = Table(aws_summary_data, colWidths=[120, 350])
    aws_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TEXTCOLOR", (0, 1), (1, 1), aws_risk_color),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(aws_tbl)
    story.append(Spacer(1, 8))

    # AWS findings list or "no findings" message
    if aws_findings:
        aws_findings_subtitle = {
            "en": "AWS-Specific Findings",
            "az": "AWS-Spesifik Tapıntılar",
            "ru": "AWS Специальные выводы"
        }
        story.append(Paragraph(aws_findings_subtitle.get(lang, aws_findings_subtitle["en"]), ss["SubSection"]))
        for idx, f in enumerate(aws_findings, 1):
            sev_color = SEVERITY_COLORS.get(f.severity, colors.black)
            story.append(Paragraph(
                f'<font color="{sev_color.hexval()}">[{f.severity.upper()}]</font> '
                f'{idx}. {f.title} <font color="#999999">({f.code})</font>',
                ss["FindTitle"],
            ))
            story.append(Paragraph(f"<b>Evidence:</b> {f.evidence}", ss["Small"]))
            story.append(Paragraph(f"<b>Recommendation:</b> {f.recommendation}", ss["Small"]))
            story.append(Spacer(1, 6))
    else:
        # NO AWS findings - show informative message
        no_aws_findings_text = {
            "en": "No AWS-specific external security observations detected.",
            "az": "AWS-spesifik xarici təhlükəsizlik müşahidələri tapılmadı.",
            "ru": "Никаких AWS-специфичных внешних наблюдений безопасности не обнаружено."
        }
        story.append(Paragraph(
            f'<font color="#388e3c">✓ {no_aws_findings_text.get(lang, no_aws_findings_text["en"])}</font>',
            ss["BodyText2"],
        ))
    story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════
    # 8. DETAILED FINDINGS
    # ═══════════════════════════════════════════════
    if result.findings:
        story.append(PageBreak())
        
        findings_titles = {
            "en": "7. Detailed Technical Findings",
            "az": "7. Ətraflı Texniki Tapıntılar",
            "ru": "7. Подробные технические выводы"
        }
        story.append(Paragraph(findings_titles.get(lang, findings_titles["en"]), ss["SectionHead"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))

        evidence_text = {
            "en": "Evidence",
            "az": "Sübut",
            "ru": "Доказательство"
        }
        recommendation_text = {
            "en": "Recommendation",
            "az": "Tövsiyə",
            "ru": "Рекомендация"
        }
        related_text = {
            "en": "Related framework controls",
            "az": "Əlaqəli çərçivə nəzarətləri",
            "ru": "Связанные элементы управления структурой"
        }
        strength_text = {
            "en": "Strength",
            "az": "Güc",
            "ru": "Сила"
        }
        confidence_text = {
            "en": "Confidence",
            "az": "Etibar",
            "ru": "Доверие"
        }
        manual_review_text = {
            "en": "manual review required",
            "az": "əl ilə nəzarə tələb olunur",
            "ru": "требуется ручная проверка"
        }

        for idx, f in enumerate(result.findings, 1):
            sev_color = SEVERITY_COLORS.get(f.severity, colors.black)

            story.append(Paragraph(
                f'<font color="{sev_color.hexval()}">[{f.severity.upper()}]</font> '
                f'{idx}. {f.title} <font color="#999999">({f.code})</font>',
                ss["FindTitle"],
            ))

            story.append(Paragraph(f"<b>{evidence_text.get(lang)}:</b> {f.evidence}", ss["Small"]))
            story.append(Paragraph(f"<b>{recommendation_text.get(lang)}:</b> {f.recommendation}", ss["Small"]))

            if f.framework_mappings:
                story.append(Paragraph(f"<b>{related_text.get(lang)}:</b>", ss["Small"]))
                for m in f.framework_mappings:
                    str_clr = STRENGTH_COLORS.get(m.mapping_strength, colors.black).hexval()
                    conf_clr = CONFIDENCE_COLORS.get(m.confidence, colors.black).hexval()
                    review_tag = f' \u2022 <font color="#1565c0">{manual_review_text.get(lang)}</font>' if m.manual_review else ""
                    story.append(Paragraph(
                        f"\u00a0\u00a0\u2022 <b>{m.framework}</b> \u2014 {m.control_id} ({m.control_name}) | "
                        f"{strength_text.get(lang)}: <font color=\"{str_clr}\">{m.mapping_strength}</font> | "
                        f"Evidence: {m.evidence_type} | "
                        f"{confidence_text.get(lang)}: <font color=\"{conf_clr}\">{m.confidence}</font>"
                        f"{review_tag}",
                        ss["CellText"],
                    ))

            story.append(Spacer(1, 6))
    else:
        story.append(Spacer(1, 10))
        
        no_concerns_text = {
            "en": "✓ No security concerns detected from external scanning.",
            "az": "✓ Xarici skanlaşdırmadan təhlükəsizlik narahatlığı aşkar edilmədi.",
            "ru": "✓ Никаких проблем безопасности при внешнем сканировании не обнаружено."
        }
        story.append(Paragraph(
            f'<font color="#388e3c">&#10003; {no_concerns_text.get(lang, no_concerns_text["en"])}</font>',
            ss["SectionHead"],
        ))

    # ═══════════════════════════════════════════════
    # FOOTER / DISCLAIMER
    # ═══════════════════════════════════════════════
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 6))
    
    disclaimer_text_en = (
        "<b>Important Disclaimer:</b> This report presents results of an automated, external, "
        "non-intrusive technical scan. It provides preliminary alignment indicators against "
        "ISO/IEC 27001:2022, NIST SP 800-53 Rev. 5, and SOC 2 Type II Trust Service Criteria. "
        "This report does <b>not</b> constitute a compliance audit, certification, or attestation. "
        "Observations do not confirm non-compliance \u2014 they highlight areas warranting further "
        "investigation. Organizations must engage qualified auditors for formal compliance assessments. "
        "The scanner has no access to internal systems, policies, procedures, or organizational controls."
    )
    disclaimer_text_az = (
        "<b>Vacib İxtar:</b> Bu hesabat avtomatlaşdırılmış, xarici, qeyri-invaziv texniki skanın nəticələrini təqdim edir. "
        "ISO/IEC 27001:2022, NIST SP 800-53 Rev. 5 və SOC 2 Type II Trust Service Criteria üçün ilkin sərtiləşdirmə "
        "göstəricilərini təmin edir. Bu hesabat <b>deyil</b> uyğunluq audibi, sertifikatı və ya attestasiyasıdır. "
        "Müşahidələr qeyri-uyğunluğu təsdiq etmir \u2014 əlavə araşdırmaya ehtiyac olan sahələri vurğulayır. "
        "Təşkilatlar rəsmi uyğunluq qiymətləndirmələri üçün mütəxəssis auditurlarla əlaqə saxlamalıdırlar. "
        "Skanner daxili sistemlərə, siyasətlərə, prosedurla və ya təşkilati nəzarətlərə daxil ola bilməz."
    )
    disclaimer_text_ru = (
        "<b>Важное заявление об отказе от ответственности:</b> Этот отчет представляет результаты автоматизированного, внешнего, "
        "неинвазивного технического сканирования. Он предоставляет предварительные индикаторы соответствия "
        "ISO/IEC 27001:2022, NIST SP 800-53 Rev. 5 и SOC 2 Type II Trust Service Criteria. "
        "Этот отчет <b>не</b> является аудитом соответствия, сертификацией или аттестацией. "
        "Наблюдения не подтверждают несоответствие \u2014 они выделяют области, требующие дальнейшего "
        "исследования. Организации должны привлечь квалифицированных аудиторов для официальной оценки соответствия. "
        "Сканер не имеет доступа к внутренним системам, политикам, процедурам или организационным элементам управления."
    )
    disclaimer_texts = {"en": disclaimer_text_en, "az": disclaimer_text_az, "ru": disclaimer_text_ru}
    story.append(Paragraph(disclaimer_texts.get(lang, disclaimer_text_en), ss["Footer"]))
    
    story.append(Spacer(1, 4))
    
    footer_text_en = "Domain Security Scanner \u2014 External Posture Report"
    footer_text_az = "Domain Security Scanner \u2014 Xarici Vəziyyət Hesabatı"
    footer_text_ru = "Domain Security Scanner \u2014 Отчет о внешней позиции"
    footer_texts = {"en": footer_text_en, "az": footer_text_az, "ru": footer_text_ru}
    
    story.append(Paragraph(
        f"{footer_texts.get(lang)} | {now_str}",
        ss["Footer"],
    ))

    doc.build(story)
    return buf.getvalue()


# ── Lists / History PDF Export ──

CATEGORY_COLORS = {
    "safe": colors.HexColor("#388e3c"),
    "warning": colors.HexColor("#f9a825"),
    "dangerous": colors.HexColor("#d32f2f"),
}


def generate_lists_pdf(title: str, columns: list[str], rows: list[dict]) -> bytes:
    """Generate a PDF for any domain list / scan history category."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
    )
    ss = _styles()
    story: list = []

    # Header
    story.append(Paragraph(title, ss["Title2"]))
    story.append(Paragraph(
        f"Exported: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
        f"Total entries: {len(rows)}",
        ss["Meta"],
    ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 10))

    if not rows:
        story.append(Paragraph("No entries in this list.", ss["Small"]))
    else:
        # Build table data from columns/rows
        table_data = [columns]
        col_keys = [c.lower() for c in columns]

        for r in rows:
            row_cells = []
            for key in col_keys:
                val = r.get(key, "")
                if val is None:
                    val = ""
                # Color category cells
                if key == "category" and str(val).lower() in CATEGORY_COLORS:
                    color_hex = CATEGORY_COLORS[str(val).lower()].hexval()
                    row_cells.append(Paragraph(
                        f'<font color="{color_hex}"><b>{str(val).upper()}</b></font>',
                        ss["Small"],
                    ))
                # Color risk cells
                elif key == "risk" and str(val) in RISK_COLORS:
                    color_hex = RISK_COLORS[str(val)].hexval()
                    row_cells.append(Paragraph(
                        f'<font color="{color_hex}"><b>{val}</b></font>',
                        ss["Small"],
                    ))
                else:
                    row_cells.append(str(val))
            table_data.append(row_cells)

        # Calculate column widths based on number of columns
        available = 170 * mm
        col_widths = [available / len(columns)] * len(columns)
        # Give domain column extra space
        if len(columns) >= 3:
            col_widths[0] = available * 0.28
            remaining = available - col_widths[0]
            for i in range(1, len(columns)):
                col_widths[i] = remaining / (len(columns) - 1)

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1f2b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ]))
        story.append(tbl)

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Domain Security Scanner \u2014 List Export | "
        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        ss["Footer"],
    ))

    doc.build(story)
    return buf.getvalue()
