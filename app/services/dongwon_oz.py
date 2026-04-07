import re
from textwrap import indent


def convert_oz(js_code: str) -> str:
    # ✅ cfOZReport 라인 추출
    cfoz_line = ""
    m_report = re.search(r"(cfOZReport\s*\([^)]+\)\s*;)", js_code)
    if m_report:
        cfoz_line = m_report.group(1).strip()
        js_code = js_code.replace(cfoz_line, "")

    # ✅ reportName 추출
    report_match = re.search(r'"/([^"]+\.ozr)"', cfoz_line)
    report_name = f"/{report_match.group(1)}" if report_match else ""

    # ✅ odiParam.add 추출
    odi_param_entries = re.findall(
        r'odiParam\.add\(\s*"([^"]+)"\s*,\s*([^)]+)\)', js_code
    )
    odi_dict = {}
    for key, val in odi_param_entries:
        val = val.strip()

        # ✅ 모든 encodeURI / encodeURIComponent 제거 (괄호 안 닫혀도 포함)
        val = re.sub(
            r"encodeURI\s*\(\s*encodeURIComponent\s*\((.*?)\)\s*\)?", r"\1", val
        )
        val = re.sub(r"encodeURIComponent\s*\((.*?)\)\)?", r"\1", val)
        val = re.sub(r"encodeURI\s*\((.*?)\)\)?", r"\1", val)

        # ✅ .BindColVal / .Text / .text → .getValue()
        val = re.sub(r"\.(BindColVal|Text|text)\b", ".getValue()", val)

        # ✅ 괄호 보정
        if ".getValue(" in val and not ".getValue()" in val:
            val = val.replace(".getValue(", ".getValue()")
        val = val.replace("trim(", "trim()")

        odi_dict[key] = val

    # ✅ viewerParam.add 추출
    viewer_entries = re.findall(
        r'viewerParam\.add\(\s*"([^"]+)"\s*,\s*"?(true|false|\d+)"?\s*\)', js_code, re.I
    )
    viewer_dict = {
        k.split(".")[-1]: (v.lower() == "true" if v.lower() in ["true", "false"] else v)
        for k, v in viewer_entries
    }

    # ✅ formParam.add 추출 (주석 제외)
    form_entries = re.findall(
        r'(?<!//)\s*formParam\.add\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)',
        js_code,
    )
    form_dict = {k: v for k, v in form_entries}

    # ✅ JS 문자열 구성
    odi_lines = [f"{k}: {v}," for k, v in odi_dict.items()]
    viewer_lines = [f"{k}: {str(v).lower()}," for k, v in viewer_dict.items()]
    form_lines = [f'{k}: "{v}",' for k, v in form_dict.items()]

    odi_block = indent("\n".join(odi_lines) or "//", " " * 8)
    viewer_block = indent("\n".join(viewer_lines) or "//", " " * 8)
    form_block = indent("\n".join(form_lines) or "//", " " * 8)

    # ✅ 최종 출력 구성
    out = []
    out.append("    let data = {")
    out.append(f'        reportName: "{report_name}",')
    out.append(f"        odiParam: {{\n{odi_block}\n            }},")
    out.append(f"        viewerParam: {{\n{viewer_block}\n            }},")
    out.append(f"        formParam: {{\n{form_block}\n            }}")
    out.append("        }")
    if cfoz_line:
        out.append(f"// {cfoz_line}")
    out.append("    scwin.openPopup(data);")
    out.append("};")

    out.append(
        """
scwin.openPopup = async function(data){
    let opts = {
        id: "ozReportPopup",
        popupName: "오즈 리포트",
        modal: true,
        type: "browserPopup",
        width: 1000,
        height: 600,
        title: "오즈 리포트"
    };

    await $c.win.openPopup("/ui/cm/zz/ozreportPopup.xml", opts, data);
}"""
    )

    return "\n".join(out)
