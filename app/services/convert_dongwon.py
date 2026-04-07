import re
from typing import Dict, Optional, Tuple, List
from .mapping import GRIDVIEW_PROPERTY_MAP


def convert_function_def(code: str) -> str:
    return re.sub(
        r"\bfunction\s+([A-Za-z_]\w*)\s*\(\)\s*{", r"scwin.\1 = function () {", code
    )


import re
from typing import List, Tuple, Dict


def extract_gauce_headers(input_text: str) -> str:
    """
    GAUCE SetDataHeader 구문으로부터 헤더 정의를 추출한다.
    - ds_xxx → dma_xxx 로 접두사 변경
    - STRING/DECIMAL/INT → text/number 변환
    - 각 컬럼에 주석 포함
    """
    TYPE_MAP = {"STRING": "text", "DECIMAL": "number", "INT": "number"}

    # 1️⃣ dataset과 header 변수 매핑
    ds_to_header_var: List[Tuple[str, str]] = []
    for m in re.finditer(
        r"(\b[A-Za-z_]\w*)\s*\.SetDataHeader\(\s*([A-Za-z_]\w*)\s*\)",
        input_text,
    ):
        ds_id, header_var = m.group(1), m.group(2)
        ds_to_header_var.append((ds_id, header_var))

    if not ds_to_header_var:
        return ""

    # 2️⃣ header 변수 정의 추출 (var|let|const 생략 가능, 멀티라인 문자열 포함)
    header_defs: Dict[str, str] = {}
    for m in re.finditer(
        r"(?:var|let|const)?\s*([A-Za-z_]\w*)\s*=\s*((?:.|\n|\r)*?;[ \t]*(?://[^\n\r]*)?)",
        input_text,
        flags=re.MULTILINE,
    ):
        var_name, rhs = m.group(1), m.group(2)
        header_defs[var_name] = rhs

    # 3️⃣ HEADER 문자열 파싱
    def parse_one_header(rhs: str) -> List[Tuple[str, str, str]]:
        items: List[Tuple[str, str, str]] = []

        # 각 문자열 조각과 // 코멘트까지 함께 추출
        for sm in re.finditer(r'"([^"]*)"\s*(?:\+\s*)?(?:;)?\s*(?://\s*(.*))?', rhs):
            content = sm.group(1)
            comment = (sm.group(2) or "").strip()

            # "a:STRING(3),b:INT(1)" → 분리
            for frag in [p for p in content.split(",") if p.strip()]:
                frag = frag.strip().rstrip(",").strip()
                mcol = re.match(r"([A-Za-z0-9_]+)\s*:\s*([A-Z]+)(?:\([^)]*\))?$", frag)
                if not mcol:
                    continue
                col, dtype = mcol.group(1), mcol.group(2)
                mapped = TYPE_MAP.get(dtype, dtype.lower())
                items.append((col, mapped, comment))

        # 마지막 항목의 코멘트가 비어 있으면 RHS 끝부분 코멘트 추가
        if items:
            m_tail = re.search(r";\s*//\s*(.*)$", rhs.strip())
            if m_tail and not items[-1][2]:
                col, mapped, _ = items[-1]
                items[-1] = (col, mapped, m_tail.group(1).strip())

        return items

    # 4️⃣ 출력 구성 (id: ds_xxx → dma_xxx 변환 포함)
    out_lines: List[str] = []
    for ds_id, header_var in ds_to_header_var:
        dma_id = re.sub(r"^ds_", "dma_", ds_id)  # ✅ 접두사 변경
        rhs = header_defs.get(header_var, "")
        out_lines.append(f"id: {dma_id}")
        if rhs:
            for col, mapped, comment in parse_one_header(rhs):
                out_lines.append(
                    f"{col}\t{comment}\t{mapped}" if comment else f"{col}\t\t{mapped}"
                )
        out_lines.append("")

    # 마지막 공백 제거
    while out_lines and out_lines[-1] == "":
        out_lines.pop()

    return "\n".join(out_lines)


# ----------------------------------------------------------------------------------------#

import re

_GRIDVIEW_PROPERTY_MAP_LOW = {k.lower(): v for k, v in GRIDVIEW_PROPERTY_MAP.items()}


def _norm(v: str) -> str:
    return (v or "").strip().lower()


def _map_grid_param_via_property_map(name: str, value: str) -> str:
    spec = _GRIDVIEW_PROPERTY_MAP_LOW.get(_norm(name))
    if not spec:
        return "-"
    v = _norm(value)
    by_value = spec.get("by_value", {})
    for key, mapped in by_value.items():
        if _norm(key) == v:
            lines = mapped if isinstance(mapped, list) else [mapped]
            return ", ".join(lines) if lines else "-"
    return "-"


import re

_GRIDVIEW_PROPERTY_MAP_LOW = {k.lower(): v for k, v in GRIDVIEW_PROPERTY_MAP.items()}


def _norm(v: str) -> str:
    return (v or "").strip().lower()


def _map_grid_param_via_property_map(name: str, value: str) -> str:
    spec = _GRIDVIEW_PROPERTY_MAP_LOW.get(_norm(name))
    if not spec:
        return "-"
    v = _norm(value)
    by_value = spec.get("by_value", {})
    for key, mapped in by_value.items():
        if _norm(key) == v:
            lines = mapped if isinstance(mapped, list) else [mapped]
            return ", ".join(lines) if lines else "-"
    return "-"


import re


def extract_grid_schema(input_text: str) -> str:
    def pick(attr_str: str, key: str):
        m = re.search(
            rf'(?i)\b{re.escape(key)}\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>/]+))',
            attr_str,
        )
        if not m:
            return None
        return (m.group(1) or m.group(2) or m.group(3) or "").strip()

    out_lines = []

    for obj in re.finditer(r"(?is)<object\b[^>]*>(.*?)</object>", input_text):
        block = obj.group(0)

        # GRID id (compID 구성용)
        m_grid_id = re.search(
            r'(?is)\bid\s*=\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s>]+))', block
        )
        grid_id = (
            (m_grid_id.group(1) or m_grid_id.group(2) or m_grid_id.group(3)).strip()
            if m_grid_id
            else ""
        )

        # DataID 추출
        m_dataid = re.search(
            r'(?is)<\s*param\b[^>]*\bname\s*=\s*"?dataid"?[^>]*\bvalue\s*=\s*"([^"]+)"',
            block,
        ) or re.search(
            r'(?is)<\s*param\b[^>]*\bname\s*=\s*"DataID"[^>]*\bvalue\s*=\s*"([^"]+)"',
            block,
        )
        if not m_dataid:
            continue
        data_id = m_dataid.group(1).strip()
        out_lines.append(f"id: {data_id}")

        # Format 추출
        formats = [
            m.group(1)
            for m in re.finditer(
                r"(?is)<\s*param\b[^>]*\bname\s*=\s*\"?format\"?[^>]*\bvalue\s*=\s*'([^']*)'",
                block,
            )
        ] or [
            m.group(1)
            for m in re.finditer(
                r"(?is)<\s*param\b[^>]*\bName\s*=\s*\"Format\"[^>]*\bvalue\s*=\s*'([^']*)'",
                block,
            )
        ]
        if not formats:
            continue

        fmt_text = "\n".join(formats)
        fmt_norm = re.sub(r"(?is)<\s*(?:c|fc)\b", "<col", fmt_text)
        fmt_norm = re.sub(r"(?is)</\s*(?:c|fc)\s*>", "</col>", fmt_norm)

        all_cols, sum_cols = [], []
        code_options = []
        decode_funcs = {}

        col_tag_pat = (
            r"(?is)<\s*(col|h)\b([^>/]*)(/?)\s*>(?:\s*(.*?)\s*</\s*(?:col|h)\s*>)?"
        )
        for col in re.finditer(col_tag_pat, fmt_norm):
            attrs = (col.group(2) or "").strip()
            inner = (col.group(4) or "").strip()
            blob = f"{attrs} {inner}".strip()

            col_id = pick(blob, "id")
            if not col_id:
                continue

            name = pick(blob, "name") or ""
            name = re.sub(r'"\s*;\s*"', " ", name)
            name = re.sub(r"'\s*;\s*'", " ", name)
            name = name.replace('"', "").replace("'", "").strip()

            # ✅ 합계식(sum, sumText)
            if re.search(
                r'\bsum(text)?\s*=\s*(?:"@sum"|\'@sum\'|@sum)', blob, re.IGNORECASE
            ):
                sum_cols.append((name or col_id, col_id))

            # ✅ 코드리스트 (getGridCombo, getCodeList, getCodeListByUpperCd)
            m_combo = re.search(
                r"GauceUtil\.(getGridCombo|getCodeList|getCodeListByUpperCd)\s*\(([^)]*)\)",
                blob,
                re.IGNORECASE,
            )
            if m_combo:
                func_name = m_combo.group(1)
                args_raw = m_combo.group(2)
                args = [
                    a.strip().strip('"').strip("'")
                    for a in args_raw.split(",")
                    if a.strip()
                ]
                if args:
                    grp_cd = args[0]
                    opt = {}
                    if func_name.lower() == "getcodelistbyuppercd" and len(args) >= 2:
                        opt = {"upperCd": args[1]}
                    elif (
                        func_name.lower() in ("getcodelist", "getgridcombo")
                        and len(args) >= 3
                    ):
                        opt = {"range": f"{args[1]},{args[2]}"}
                    entry = {"grpCd": grp_cd, "compID": f"{grid_id}:{col_id}"}
                    if opt:
                        entry["opt"] = opt
                    code_options.append(entry)

            # ✅ decode 함수
            m_decode = re.search(r"decode\s*\(([^)]+)\)", blob, re.IGNORECASE)
            if m_decode:
                args = m_decode.group(1).strip()
                parts = [p.strip() for p in re.split(r",(?![^()]*\))", args)]
                cleaned_parts = []

                for p in parts:
                    if p == col_id:  # col_id → data
                        cleaned_parts.append("data")
                        continue
                    if re.fullmatch(r"null", p, re.IGNORECASE):  # null 처리
                        prev = cleaned_parts[-1] if cleaned_parts else ""
                        if re.match(r'^".*"$', prev):
                            cleaned_parts.append('""')
                        else:
                            cleaned_parts.append("null")
                        continue
                    cleaned_parts.append(p)

                # 중복 첫 인자 제거
                if cleaned_parts and cleaned_parts[0] == "data":
                    cleaned_parts = cleaned_parts[1:]

                decode_funcs[col_id] = ", ".join(cleaned_parts)

            all_cols.append(f"{col_id}\t{name}" if name else f"{col_id}")

        # === 출력 ===
        out_lines.extend(all_cols)

        if sum_cols:
            out_lines.append("- expressions -")
            for cname, cid in sum_cols:
                out_lines.append(f'{cname}\tSUM("{cid}")')

        if code_options:
            out_lines.append("")
            out_lines.append("-- 코드리스트 --")
            out_lines.append("const codeOptions = [")
            for opt in code_options:
                if "opt" in opt:
                    out_lines.append(
                        f'    {{ grpCd : "{opt["grpCd"]}", compID : "{opt["compID"]}", opt : {opt["opt"]} }},'
                    )
                else:
                    out_lines.append(
                        f'    {{ grpCd : "{opt["grpCd"]}", compID : "{opt["compID"]}" }},'
                    )
            out_lines.append("];")
            out_lines.append("$c.data.setCommonCode(codeOptions);")

        if decode_funcs:
            out_lines.append("")
            out_lines.append("-- decode function --")
            out_lines.append("// grid decode format")
            for col_id, args in decode_funcs.items():
                out_lines.append(f"scwin.{col_id}DisplayFm = function(data) {{")
                out_lines.append(f"    return $c.gus.decode(data, {args});")
                out_lines.append("}")

        # 옵션 매핑
        param_pairs = []
        for pm in re.finditer(r"(?is)<\s*param\b([^>]*)>", block):
            attrs = pm.group(1) or ""
            p_name = pick(attrs, "name")
            p_value = pick(attrs, "value")
            if not p_name or str(p_name).strip().lower() in ("format",):
                continue
            param_pairs.append((p_name.strip(), (p_value or "").strip()))

        if param_pairs:
            out_lines.append("")
            out_lines.append("- 옵션 매핑 -")
            for p_name, p_val in param_pairs:
                tobe = _map_grid_param_via_property_map(p_name, p_val)
                out_lines.append(f"{p_name}\t{p_val}\t->\t{tobe}")

        out_lines.append("")

    while out_lines and out_lines[-1] == "":
        out_lines.pop()

    return "\n".join(out_lines)


# ----------------------------------------------------------------------------------------#

# ========================================================================
# ============================ Header 변환 ================================
# ========================================================================

# 타입 분류 (GAUCE 타입 → WebSquare 유형)
_NUMERIC_TYPES = {
    "DECIMAL",
    "NUMERIC",
    "NUMBER",
    "INT",
    "INTEGER",
    "SMALLINT",
    "BIGINT",
    "FLOAT",
    "DOUBLE",
    "REAL",
}
_TEXT_TYPES = {
    "STRING",
    "CHAR",
    "NCHAR",
    "VARCHAR",
    "VARCHAR2",
    "NVARCHAR",
    "NVARCHAR2",
}


def _map_type_to_ws(type_base: Optional[str]) -> str:
    if not type_base:
        return "text"
    t = type_base.upper()
    if t in _NUMERIC_TYPES:
        return "number"
    if t in _TEXT_TYPES:
        return "text"
    return "text"


def _comment_out_block(block: str) -> str:
    """블록 전체를 한 줄 주석으로 처리"""
    lines = block.splitlines(True)
    return "".join(
        "// " + ln if not ln.strip().startswith("//") else ln for ln in lines
    )


def _find_var_decl_span_for_header_var(
    code: str, header_var: str, end_pos: int
) -> Optional[Tuple[int, int, str]]:
    """
    header_var 의 가장 가까운 var/let/const 선언 위치 ~ SetDataHeader 직전까지를 찾아
    그 구간 내 문자열 리터럴을 모두 이어붙인 spec 문자열을 만들어 돌려준다.
    """
    decl_pattern = re.compile(
        rf"(?:var|let|const)\s+{re.escape(header_var)}\s*=\s*", re.IGNORECASE
    )
    match = None
    for m in decl_pattern.finditer(code, 0, end_pos):
        match = m
    if not match:
        return None

    decl_start = match.start()
    segment = code[match.end() : end_pos]
    string_literals = re.findall(r'"([^"]*)"', segment)
    literal_concat = "".join(string_literals)
    return (decl_start, end_pos, literal_concat)


def _parse_header_spec_to_columns(spec: str) -> List[Tuple[str, Optional[str]]]:
    """
    "colA:STRING(6),colB:DECIMAL(13)" → [("colA","STRING"),("colB","DECIMAL")]
    """
    cols: List[Tuple[str, Optional[str]]] = []
    for raw in spec.split(","):
        token = raw.strip()
        if not token:
            continue
        m = re.match(
            r"^([A-Za-z_]\w*)"  # 이름
            r"(?:\s*:\s*([A-Za-z_]\w*)\s*"  # :TYPE
            r"(?:\(\s*[-\w\s]+\s*\))?"  # (길이/정밀도)
            r")?$",
            token,
        )
        if not m:
            cols.append((token, None))
        else:
            name = m.group(1)
            tbase = m.group(2)
            cols.append((name, tbase))
    return cols


def _build_create_datamap_code(
    indent: str, ds_name: str, cols: List[Tuple[str, Optional[str]]]
) -> str:
    names = [c[0] for c in cols]
    types = [_map_type_to_ws(c[1]) for c in cols]

    inner = indent + "  "

    def fmt(arr: List[str]) -> str:
        if not arr:
            return "[]"
        body = "".join(f'{inner}"{x}",\n' for x in arr)
        # 마지막 콤마 제거
        if body.endswith(",\n"):
            body = body[:-2] + "\n"
        return "[\n" + body + indent + "]"

    return (
        f"\n{indent}$c.data.createDataMap(\n"
        f"{indent}  {ds_name},\n"
        f"{indent}  {fmt(names)},\n"
        f"{indent}  {fmt(types)}\n"
        f"{indent});\n"
    )


def _find_addrow_for_ds(
    code: str, ds: str, start_idx: int, window_lines: int = 12
) -> Optional[Tuple[int, int]]:
    """SetDataHeader 이후 근처의 AddRow()를 함께 주석 처리하기 위해 위치를 찾는다."""
    tail = code[start_idx:]
    lines = tail.splitlines(True)
    sub = "".join(lines[:window_lines])
    pat = re.compile(rf"([ \t]*){re.escape(ds)}\.AddRow\(\s*\)\s*;", re.MULTILINE)
    m = pat.search(sub)
    if not m:
        return None
    s = start_idx + m.start()
    e = start_idx + m.end()
    return (s, e)


def convert_gauce_headers_to_wsq(code: str) -> str:
    """
    ds_xxx.SetDataHeader(GVAR); (+ 근처 AddRow()) → $c.data.createDataMap(ds_xxx, [...], [...])
    선언부(GVAR 연결 문자열)는 통째로 주석 처리
    """
    sethdr_pattern = re.compile(
        r"(?P<indent>[ \t]*)"
        r"(?P<ds>[A-Za-z_]\w*)\.SetDataHeader\(\s*(?P<hvar>[A-Za-z_]\w*)\s*\)\s*;",
        re.MULTILINE,
    )

    out = []
    cur = 0
    for m in sethdr_pattern.finditer(code):
        ds = m.group("ds")
        hvar = m.group("hvar")
        indent = m.group("indent")
        set_s, set_e = m.span()

        # 선언 블록 추출
        decl_info = _find_var_decl_span_for_header_var(code, hvar, set_s)
        if not decl_info:
            # 선언 못 찾으면 SetDataHeader만 주석 처리
            out.append(code[cur:set_s])
            out.append(_comment_out_block(code[set_s:set_e]) + "\n")
            cur = set_e
            continue

        decl_s, decl_to_set, literal_concat = decl_info

        # 선언 이전까지 원문 유지
        out.append(code[cur:decl_s])

        # 선언~SetDataHeader까지 주석 처리
        out.append(_comment_out_block(code[decl_s:set_e]) + "\n")

        # AddRow 있으면 같이 주석 처리
        add_span = _find_addrow_for_ds(code, ds, set_e)
        next_pos = set_e
        if add_span:
            a_s, a_e = add_span
            out.append(code[set_e:a_s])  # 사이 구간 원문 유지
            out.append(_comment_out_block(code[a_s:a_e]) + "\n")
            next_pos = a_e

        # spec 파싱 → createDataMap 생성
        cols = _parse_header_spec_to_columns(literal_concat)
        out.append(_build_create_datamap_code(indent, ds, cols))

        cur = next_pos

    out.append(code[cur:])
    return "".join(out)


def convert_header_pipeline(code: str) -> str:
    # 함수 정의 치환 (function f_xxx → scwin.f_xxx = function)
    code = convert_function_def(code)
    # 헤더 변환
    code = convert_gauce_headers_to_wsq(code)
    return code


import re


def extract_bind_schema(input_text: str) -> str:
    def pick(attr_str: str, key: str):
        m = re.search(
            rf'(?i)\b{re.escape(key)}\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>/]+))',
            attr_str,
        )
        if not m:
            return None
        return (m.group(1) or m.group(2) or m.group(3) or "").strip()

    out_lines = []

    for obj in re.finditer(r"(?is)<object\b[^>]*>(.*?)</object>", input_text):
        block = obj.group(0)

        # GRID id (compID 구성용)
        m_grid_id = re.search(
            r'(?is)\bid\s*=\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s>]+))', block
        )
        grid_id = (
            (m_grid_id.group(1) or m_grid_id.group(2) or m_grid_id.group(3)).strip()
            if m_grid_id
            else ""
        )

        # DataID 추출
        m_dataid = re.search(
            r'(?is)\bname\s*=\s*"?DataID"?[^>]*\bvalue\s*=\s*"([^"]+)"', block
        )
        if not m_dataid:
            continue
        data_id = m_dataid.group(1).strip()
        out_lines.append(f"id: {data_id}")

        # ✅ BindInfo 처리 (데이터 매핑 스키마)
        m_bindinfo = re.search(
            r'(?is)\bname\s*=\s*"?BindInfo"?[^>]*\bvalue\s*=\s*[\'"]([\s\S]*?)[\'"]',
            block,
        )
        if m_bindinfo:
            bind_text = m_bindinfo.group(1)
            bind_cols = re.findall(
                r"<C>\s*Col\s*=\s*([^\s]+)\s+Ctrl\s*=\s*([^\s]+)\s+Param\s*=\s*([^\s<]+)\s*</C>",
                bind_text,
                re.IGNORECASE,
            )
            out_lines.append("- Bind Schema -")
            for col, ctrl, param in bind_cols:
                out_lines.append(f"{col.ljust(25)}Ctrl={ctrl.ljust(20)}Param={param}")
            out_lines.append("")

        # ✅ Format (그리드 컬럼 구조)
        formats = [
            m.group(1)
            for m in re.finditer(
                r"(?is)\bname\s*=\s*\"?format\"?[^>]*\bvalue\s*=\s*'([^']*)'",
                block,
            )
        ] or [
            m.group(1)
            for m in re.finditer(
                r"(?is)\bName\s*=\s*\"Format\"[^>]*\bvalue\s*=\s*'([^']*)'",
                block,
            )
        ]
        if not formats:
            continue

        fmt_text = "\n".join(formats)
        fmt_norm = re.sub(r"(?is)<\s*(?:c|fc)\b", "<col", fmt_text)
        fmt_norm = re.sub(r"(?is)</\s*(?:c|fc)\s*>", "</col>", fmt_norm)

        all_cols, sum_cols = [], []
        code_options, decode_funcs = [], {}

        col_tag_pat = (
            r"(?is)<\s*(col|h)\b([^>/]*)(/?)\s*>(?:\s*(.*?)\s*</\s*(?:col|h)\s*>)?"
        )

        for col in re.finditer(col_tag_pat, fmt_norm):
            attrs = (col.group(2) or "").strip()
            inner = (col.group(4) or "").strip()
            blob = f"{attrs} {inner}".strip()

            col_id = pick(blob, "id")
            if not col_id:
                continue

            name = pick(blob, "name") or ""
            name = name.replace('"', "").replace("'", "").strip()

            if re.search(
                r'\bsum(text)?\s*=\s*(?:"@sum"|\'@sum\'|@sum)', blob, re.IGNORECASE
            ):
                sum_cols.append((name or col_id, col_id))

            all_cols.append(f"{col_id.ljust(25)}{name}")

        # === 출력 ===
        if all_cols:
            out_lines.extend(all_cols)
            out_lines.append("")

        if sum_cols:
            out_lines.append("- expressions -")
            for cname, cid in sum_cols:
                out_lines.append(f'{cname.ljust(25)}SUM("{cid}")')
            out_lines.append("")

        # 옵션 매핑
        param_pairs = []
        for pm in re.finditer(r"(?is)<\s*param\b([^>]*)>", block):
            attrs = pm.group(1) or ""
            p_name = pick(attrs, "name")
            p_value = pick(attrs, "value")
            if not p_name or str(p_name).strip().lower() in ("format",):
                continue
            param_pairs.append((p_name.strip(), (p_value or "").strip()))

        if param_pairs:
            out_lines.append("- 옵션 매핑 -")
            for p_name, p_val in param_pairs:
                out_lines.append(f"{p_name.ljust(25)}{p_val}")
            out_lines.append("")

    while out_lines and not out_lines[-1].strip():
        out_lines.pop()

    return "\n".join(out_lines)
