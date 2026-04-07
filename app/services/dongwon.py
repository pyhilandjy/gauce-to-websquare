import re
from typing import Dict, Optional, Match

# 외부 매핑 정의
from app.services.mapping import (
    PROPERTY_MAP,
    METHOD_MAP,
    _GAUCE_METHOD_MAP_LOWER,
    GAUCE_DATASET_PROPERTY_SETTER_MAP,
    COMPONENT_PREFIX_MAP,
    EVENT_MAP_BY_TYPE,
    ID_PREFIX_MAP,
    FUNCTION_MAP_LOWER,
)

# ---------------------
# JSP 변수 수집/치환 유틸
# ---------------------
_JSP_INLINE_PAT = re.compile(r"<%=\s*([A-Za-z_]\w*)\s*%>")
_JSP_QUOTED_PAT1 = re.compile(r'"<%=\s*([A-Za-z_]\w*)\s*%>"')
_JSP_QUOTED_PAT2 = re.compile(r"'<%=\s*([A-Za-z_]\w*)\s*%>'")

# ✅ JSP 날짜 표현식: <%= DDate.getDate() %> / <%= Date.getDate().substring(...) %>
_DATE_JSP_RE = re.compile(
    r"""<%=\s*
        (?:(?:DDate|Date)\.getDate\(\))      # DDate.getDate() 또는 Date.getDate()
        (?P<post>\.substring\(\s*[^)]*\))?   # 선택적 .substring(...)
        \s*%>""",
    re.IGNORECASE | re.VERBOSE,
)


def _jsp_quoted_to_scwin(s: str) -> str:
    s = _JSP_QUOTED_PAT1.sub(r"scwin.\1", s)
    s = _JSP_QUOTED_PAT2.sub(r"scwin.\1", s)
    return s


def _jsp_inline_to_scwin(s: str) -> str:
    return _JSP_INLINE_PAT.sub(r"scwin.\1", s)


def _normalize_jsp_dates(code: str) -> str:
    # <%= DDate.getDate() ... %> → scwin.vCurDate[...]
    def repl(m: re.Match) -> str:
        post = m.group("post") or ""
        return f"scwin.vCurDate{post}"

    return _DATE_JSP_RE.sub(repl, code)


def _normalize_jsp_vars(code: str) -> str:
    # ✅ 먼저 getDate()를 scwin.vCurDate로 치환
    code = _normalize_jsp_dates(code)
    # 그다음 일반 JSP 변수 → scwin.*
    return _jsp_inline_to_scwin(_jsp_quoted_to_scwin(code))


def _find_jsp_vars(src: str) -> set[str]:
    names: set[str] = set()
    for pat in (_JSP_INLINE_PAT, _JSP_QUOTED_PAT1, _JSP_QUOTED_PAT2):
        names.update(pat.findall(src))
    return names


# ---------------------
# 전역변수 헤더 생성
# ---------------------
def _already_assigned(name: str, code: str) -> bool:
    return re.search(rf"\bscwin\.{re.escape(name)}\s*=", code) is not None


def _split_date_suffix(name: str) -> tuple[Optional[str], Optional[str]]:
    # 접두사+StDt / 접두사+EndDt 를 분리 (대소문자 구분 그대로 유지)
    if name.endswith("StDt"):
        return name[:-4], "StDt"
    if name.endswith("EndDt"):
        return name[:-5], "EndDt"
    return None, None


def _make_scwin_var_inits(var_names: set[str], existing_code: str) -> str:
    """
    // 전역변수 블록 생성:
      - <prefix>StDt / <prefix>EndDt 를 찾아 월초/월말 로직으로 초기화 (기존 규칙 유지)
      - 나머지 JSP 변수는 ""
      - getDate()가 있었으면 scwin.vCurDate 한 줄만 주입
      - 기존에 scwin.* = ... 있으면 중복 방지
    """
    date_groups: Dict[str, set[str]] = {}
    others: set[str] = set()

    for name in var_names:
        prefix, suf = _split_date_suffix(name)
        if prefix and suf:
            date_groups.setdefault(prefix, set()).add(suf)
        else:
            others.add(name)

    lines: list[str] = []

    # ✅ 코드 본문에 scwin.vCurDate가 있으면(= getDate() 치환 결과) 전역 한 줄 주입
    if "scwin.vCurDate" in existing_code and not _already_assigned(
        "vCurDate", existing_code
    ):
        lines.append("scwin.vCurDate = WebSquare.date.getCurrentServerDate();")

    # StDt/EndDt 초기화 (기존 로직 그대로)
    for prefix in sorted(date_groups.keys()):
        st_name = f"{prefix}StDt"
        en_name = f"{prefix}EndDt"

        if "StDt" in date_groups[prefix] and not _already_assigned(
            st_name, existing_code
        ):
            lines.append(f'scwin.{st_name} = scwin.vCurDate.substring(0, 6) + "01";')
        if "EndDt" in date_groups[prefix] and not _already_assigned(
            en_name, existing_code
        ):
            lines.append(
                "scwin.{0} = scwin.vCurDate.substring(0, 6) + "
                "$c.date.getLastDateOfMonth(scwin.vCurDate);".format(en_name)
            )

    # 기타 JSP 변수 기본값
    for name in sorted(others):
        if not _already_assigned(name, existing_code):
            lines.append(f'scwin.{name} = "";')

    if not lines:
        return ""
    return "// 전역변수\n" + "\n".join(lines) + "\n\n"


# ---------------------
# 속성/메서드 변환
# ---------------------
_PROPERTY_MAP_LOWER: Dict[str, str] = {k.lower(): v for k, v in PROPERTY_MAP.items()}
_METHOD_MAP_LOWER: Dict[str, str] = {k.lower(): v for k, v in METHOD_MAP.items()}


def convert_properties(code: str) -> str:
    def repl(m: re.Match) -> str:
        var, prop, rhs, tail = (
            m.group("var"),
            m.group("prop"),
            (m.group("rhs") or "").strip(),
            m.group("tail") or "",
        )
        rhs = _normalize_jsp_vars(rhs)
        key = prop.lower()

        if key in ("text", "value"):
            return f"{var}.{_PROPERTY_MAP_LOWER[key]}({rhs});{tail}"
        elif key == "enable":
            val = rhs.lower()
            if val in ("true", "false"):
                disabled = "true" if val == "false" else "false"
                return f"{var}.{_PROPERTY_MAP_LOWER[key]}({disabled});{tail}"
            return f"{var}.{_PROPERTY_MAP_LOWER[key]}(/* NOTE:check inversion */ {rhs});{tail}"
        elif key == "disabled":
            return f"{var}.{_PROPERTY_MAP_LOWER[key]}({rhs.lower() if rhs.lower() in ('true','false') else rhs});{tail}"
        return m.group(0)

    pattern = r"""
        (?P<var>[A-Za-z_]\w*)\.
        (?P<prop>Text|value|Enable|disabled)
        \s*=\s*
        (?P<rhs>[^;]*?)
        \s*;
        (?P<tail>\s*(?://[^\n]*)?)        
    """
    return re.sub(pattern, repl, code, flags=re.VERBOSE | re.IGNORECASE)


def convert_property_access(code: str) -> str:
    # ✅ 읽기 접근: .text/.Text/.value → .getValue() (대소문자 무시)
    def repl(m: re.Match) -> str:
        return f"{m.group('var')}.getValue()"

    pattern = r"(?P<var>[A-Za-z_]\w*)\.(Text|text|value)(?!\s*=\s*)"
    return re.sub(pattern, repl, code, flags=re.VERBOSE | re.IGNORECASE)


def convert_methods(code: str) -> str:
    def repl(m: re.Match) -> str:
        var, method, tail = m.group("var"), m.group("method"), m.group("tail") or ""
        if method.lower() in _METHOD_MAP_LOWER:
            return f"{var}.{_METHOD_MAP_LOWER[method.lower()]}();{tail}"
        return m.group(0)

    pattern = (
        r"(?P<var>[A-Za-z_]\w*)\.(?P<method>Focus)\(\)\s*;(?P<tail>\s*(?://[^\n]*)?)"
    )
    return re.sub(pattern, repl, code, flags=re.IGNORECASE)


# ---------------------
# cfXXX/유틸 변환 (lookbehind 없이)
# ---------------------
def _has_c_prefix_before(s: str, pos: int) -> bool:
    # 매치 시작 지점 앞쪽에 `$c.gus.` / `$c.data.` / `$c.win.` 이 붙어있는지 검사
    prefix = s[max(0, pos - 16) : pos]
    return bool(re.search(r"\$c\.(gus|data|win)\.\s*$", prefix, flags=re.IGNORECASE))


def convert_gus_functions(code: str) -> str:
    for asis_lower, tobe_full in FUNCTION_MAP_LOWER.items():
        name_pat = re.escape(asis_lower)

        # 문장형
        stmt = re.compile(
            rf"\b{name_pat}\s*\((?P<args>[^)]*)\)\s*;(?P<tail>\s*(?://[^\n]*)?)",
            re.IGNORECASE,
        )

        def stmt_repl(m):
            if _has_c_prefix_before(m.string, m.start()):
                return m.group(0)
            return f"{tobe_full}({m.group('args')});{m.group('tail') or ''}"

        code = stmt.sub(stmt_repl, code)

        # 표현식형
        expr = re.compile(
            rf"(?P<prefix>!?|\b)\s*{name_pat}\s*\((?P<args>[^)]*)\)",
            re.IGNORECASE,
        )

        def expr_repl(m):
            if _has_c_prefix_before(m.string, m.start()):
                return m.group(0)
            return f"{m.group('prefix')}{tobe_full}({m.group('args')})"

        code = expr.sub(expr_repl, code)

    return code


# ---------------------
# f_ 접두사 사용자 함수 호출 → scwin.* 접두사 부여
# ---------------------
_F_CALL_RE = re.compile(r"(?<![\.\w])\b(f_[A-Za-z0-9_]+)\s*\(", re.IGNORECASE)


def convert_f_function_calls(code: str) -> str:
    """
    Bare 호출(접두사 없이 호출된) f_* 함수에 scwin. 접두사를 부여.
    - 이미 scwin.f_*, this.f_*, obj.f_* 처럼 식별자/점이 앞에 있으면 제외.
    """

    def repl(m: re.Match) -> str:
        fname = m.group(1)
        return f"scwin.{fname}("

    return _F_CALL_RE.sub(repl, code)


# ---------------------
# Transaction → Submission
# ---------------------
def convert_transaction_to_submission(code: str) -> str:
    pattern = re.compile(
        r"""
        \b
        tr_(?P<name>[A-Za-z_]\w*)
        \s*\.\s*
        post
        \s*\(\s*\)\s*
        ;?
        (?P<tail>\s*(?://[^\n]*)?)
        """,
        re.VERBOSE | re.IGNORECASE,
    )
    return pattern.sub(
        lambda m: f"$c.sbm.execute(sbm_{m.group('name')});{m.group('tail') or ''}", code
    )


# ---------------------
# NameValue 처리
# ---------------------
def convert_properties_and_namevalue(code: str) -> str:
    assign_pat = re.compile(
        r"(?P<obj>[A-Za-z_]\w*)\.NameValue\(\s*(?P<row>[^,]+),\s*(?P<col>[^)]+)\)\s*(?P<op>=(?!=))\s*(?P<rhs>[^;]+);"
    )
    code = assign_pat.sub(
        lambda m: f"{m.group('obj')}.setCellData({m.group('row')}, {m.group('col')}, {m.group('rhs')});",
        code,
    )
    get_pat = re.compile(
        r"(?P<obj>[A-Za-z_]\w*)\.NameValue\(\s*(?P<row>[^,]+),\s*(?P<col>[^)]+)\)"
    )
    code = get_pat.sub(
        lambda m: f"{m.group('obj')}.getCellData({m.group('row')}, {m.group('col')})",
        code,
    )
    return convert_properties(code)


# ---------------------
# var/for 변환
# ---------------------
def convert_var_to_let(code: str) -> str:
    return re.sub(r"\bvar\b", "let", code)


def convert_for_loops(code: str) -> str:
    pattern = re.compile(
        r"""
        for\s*\(
        \s*(?:(?:var|let)\s+)?           
        (?P<i>\w+)\s*=\s*1\s*;           
        \s*(?P=i)\s*<=\s*                
        (?P<ds>[A-Za-z_]\w*)\.CountRow   
        \s*;\s*                          
        (?P=i)\+\+                       
        \s*\)                            
        """,
        re.VERBOSE | re.IGNORECASE,
    )
    return pattern.sub(
        r"for (\g<i> = 0; \g<i> < \g<ds>.getRowCount(); \g<i>++)",
        code,
    )


def convert_countrow(code: str) -> str:
    return re.sub(
        r"(?P<ds>[A-Za-z_]\w*)\s*\.\s*CountRow\b",
        r"\g<ds>.getRowCount()",
        code,
        flags=re.IGNORECASE,
    )


# ---------------------
# 함수 정의/RowPosition 변환
# ---------------------
def convert_function_def(code: str) -> str:
    return re.sub(
        r"\bfunction\s+([A-Za-z_]\w*)\s*\(\)\s*{", r"scwin.\1 = function () {", code
    )


def convert_rowposition(code: str) -> str:
    return re.sub(r"\.RowPosition\b", ".rowPosition", code, flags=re.IGNORECASE)


# ---------------------
# GAUCE DataSet API 매핑
# ---------------------
_GAUCE_METHOD_MAP_LOWER = {k.lower(): v for k, v in _GAUCE_METHOD_MAP_LOWER.items()}


def convert_gauce_dataset_methods(code: str) -> str:
    pat = re.compile(
        r"(?P<obj>\b[A-Za-z_]\w*)\s*\.\s*(?P<meth>[A-Za-z_]\w*)(?:\s*\(\s*(?P<args>[^)]*)\s*\))?"
    )

    def repl(m: Match) -> str:
        obj, meth, args = m.group("obj"), m.group("meth"), (m.group("args") or "")
        new = _GAUCE_METHOD_MAP_LOWER.get(meth.lower())
        if new is None or new == "":
            return m.group(0)
        if meth.lower() == "isupdated":
            return f"{obj}.getModifiedIndex().length > 0"
        if args:
            return f"{obj}.{new}({args})"
        else:
            return f"{obj}.{new}()"

    return pat.sub(repl, code)


def convert_gauce_dataset_properties(code: str) -> str:
    for prop, setter in GAUCE_DATASET_PROPERTY_SETTER_MAP.items():
        assign_pat = re.compile(
            rf"(?P<obj>\b[A-Za-z_]\w*)\s*\.\s*{re.escape(prop)}\s*=\s*(?P<rhs>[^;]+);",
            re.IGNORECASE,
        )
        code = assign_pat.sub(
            lambda m: f"{m.group('obj')}.{setter}({m.group('rhs')});", code
        )
    code = re.sub(
        r"(?P<obj>\b[A-Za-z_]\w*)\s*\.\s*IsUpdated\b(?!\s*\()",
        r"\g<obj>.isUpdated()",
        code,
        flags=re.IGNORECASE,
    )
    return code


# ---------------------
# ID 접두어 & 이벤트 핸들러 변환
# ---------------------
def _sorted_prefix_items(d: Dict[str, str]):
    return sorted(d.items(), key=lambda kv: -len(kv[0]))


def convert_id_prefixes(
    code: str,
    extra_overrides: Dict[str, str] | None = None,
    force_autocomplete_ids: set[str] | None = None,
) -> str:
    mapping = dict(ID_PREFIX_MAP)
    overrides = extra_overrides or {}
    force_acb = force_autocomplete_ids or set()

    for old_id, new_id in overrides.items():
        code = re.sub(rf"\b{re.escape(old_id)}\b", new_id, code)
        code = re.sub(
            rf'("{re.escape(old_id)}")|(\'{re.escape(old_id)}\')',
            lambda m: f'"{new_id}"' if m.group(1) else f"'{new_id}'",
            code,
        )

    for plain_id in force_acb:
        if not plain_id.startswith("lc_"):
            continue
        new_id = "acb_" + plain_id[3:]
        code = re.sub(rf"\b{re.escape(plain_id)}\b", new_id, code)
        code = re.sub(
            rf'("{re.escape(plain_id)}")|(\'{re.escape(plain_id)}\')',
            lambda m: f'"{new_id}"' if m.group(1) else f"'{new_id}'",
            code,
        )

    for old, new in _sorted_prefix_items(mapping):
        if old == new:
            continue
        code = re.sub(rf"\b{re.escape(old)}(?=[A-Za-z_]\w*)", new, code)
        code = re.sub(
            rf'(")([^"]*?\b){re.escape(old)}(?=[A-Za-z_]\w*)([^"]*?)(")',
            lambda m: f"{m.group(1)}{m.group(2)}{new}{m.group(3)}{m.group(4)}",
            code,
        )
        code = re.sub(
            rf"(')([^']*?\b){re.escape(old)}(?=[A-Za-z_]\w*)([^']*?)(')",
            lambda m: f"{m.group(1)}{m.group(2)}{new}{m.group(3)}{m.group(4)}",
            code,
        )
    return code


def _infer_component_type(comp_id: str) -> Optional[str]:
    low = comp_id.lower()
    for tp, prefixes in COMPONENT_PREFIX_MAP.items():
        for p in prefixes:
            if low.startswith(p.lower()):
                return tp
    return None


def convert_component_event_handlers(code: str) -> str:
    pat = re.compile(
        r"\bscwin\.(?P<cid>[A-Za-z_]\w*)_(?P<ev>[A-Za-z_]\w*)\s*=\s*function\s*\("
    )

    def repl(m: re.Match) -> str:
        cid, ev = m.group("cid"), m.group("ev")
        tp = _infer_component_type(cid) or ""
        target = None
        if tp and tp in EVENT_MAP_BY_TYPE:
            for k, v in EVENT_MAP_BY_TYPE[tp].items():
                if k.lower() == ev.lower():
                    target = v
                    break
        if not target and ev.startswith("On"):
            target = "on" + ev[2:].lower()
        if not target:
            return m.group(0)
        return f"scwin.{cid}_{target} = function("

    return pat.sub(repl, code)


def add_options_to_hidval(code: str) -> str:
    """
    ✅ 단순히 .hidVal → .options.hidVal 로 변환하는 함수
    - 이미 options.hidVal 인 부분은 그대로 둠
    - 대소문자 무시 옵션 추가
    """
    pattern = re.compile(r"(?<!options)\.hidVal\b", re.IGNORECASE)
    return pattern.sub(".options.hidVal", code)


# ---------------------
# udc popud case 1
# ---------------------
import re

import re


def convert_common_popup_to_udc(code: str) -> str:
    """
    ✅ 공통 팝업 변환
    - switch 구조는 절대 삭제하지 않음
    - cfCommonPopUp → udc_xxx.cfCommonPopUp(scwin.udc_xxx_callBackFunc, ...)
    - cfSetReturnValue → 주석 처리
    - 콜백 함수 자동 생성
    """

    callbacks = []

    # cfCommonPopUp('retrieveXxx', ...) → 추출
    popup_pattern = re.compile(
        r"cfCommonPopUp\s*\(\s*['\"]([^'\"]+)['\"]\s*,([\s\S]*?)\);",
        re.IGNORECASE,
    )

    # cfSetReturnValue(...) → 추출
    return_pattern = re.compile(
        r"cfSetReturnValue\s*\(\s*([^\),]+)\s*,\s*([^\),]+)\s*,\s*([^)]+)\)",
        re.IGNORECASE,
    )

    # switch 블록이 있으면 찾아서 내부만 수정
    m_switch = re.search(r"(switch\s*\(.*?\)[\s\S]*?\})", code, re.IGNORECASE)
    target_scope = m_switch.group(1) if m_switch else code

    matches = list(popup_pattern.finditer(target_scope))
    returns = list(return_pattern.finditer(target_scope))

    for i, match in enumerate(matches):
        fn_name = match.group(1)
        params = match.group(2).strip()

        # retrieve → udc_ 접두사로
        base = re.sub(r"^retrieve", "", fn_name)
        base = base[:1].lower() + base[1:]
        udc_id = f"udc_{base}"
        cb_func = f"scwin.{udc_id}_callBackFunc"

        # cfSetReturnValue 대응
        ret_match = returns[i] if i < len(returns) else None
        if ret_match:
            _, t1, t2 = ret_match.groups()
            t1, t2 = t1.strip(), t2.strip()
        else:
            t1, t2 = "ed_unknown1", "ed_unknown2"

        # ✅ 변환된 팝업 호출문
        new_call = f"{udc_id}.cfCommonPopUp({cb_func}, {params});"
        target_scope = target_scope.replace(match.group(0), new_call)

        # ✅ 콜백 함수 생성
        callback_code = f"""
{cb_func} = function(rtnList) {{
    if (rtnList != null) {{
        if (rtnList[0] == "N/A") return;
        {t1}.setValue(rtnList[0]);
        {t2}.setValue(rtnList[1]);
        {t1}.options.hidVal = rtnList[0];
        {t2}.options.hidVal = rtnList[1];
    }} else {{
        {t1}.setValue("");
        {t2}.setValue("");
        {t1}.options.hidVal = "";
        {t2}.options.hidVal = "";
    }}
}};
""".strip()
        callbacks.append(callback_code)

    # ✅ switch 문이 있었다면 원래 위치에 다시 삽입
    if m_switch:
        code = code.replace(m_switch.group(1), target_scope)
    else:
        code = target_scope

    # ✅ cfSetReturnValue → 주석 처리
    code = re.sub(
        r"(?:\$c\.gus\.\s*)?cfSetReturnValue",
        "// cfSetReturnValue",
        code,
        flags=re.IGNORECASE,
    )

    # ✅ 콜백 함수들 추가
    if callbacks:
        code += (
            "\n\n// ======================\n// 콜백 함수들\n// ======================\n"
        )
        code += "\n\n".join(callbacks)

    return code


def convert_common_popup_instant_to_udc(code: str) -> str:
    """
    ✅ 단순형 변환
    - cfCommonPopUp('retrieveXxx', ...) → udc_xxx.cfCommonPopUp(scwin.udc_xxx_callBackFunc, ...)
    - 콜백 함수 스켈레톤 자동 생성
    """

    callbacks = []

    # cfCommonPopUp('retrieveSomething', ...) 매칭 (멀티라인 포함)
    # 🔥 세미콜론(;) 제거하고 닫는 괄호까지만 인식하도록 수정
    popup_pattern = re.compile(
        r"cfCommonPopUp\s*\(\s*['\"]([^'\"]+)['\"]\s*,([\s\S]*?)\)",
        re.IGNORECASE,
    )

    for match in popup_pattern.finditer(code):
        fn_name = match.group(1)  # retrieveClntInfo 등
        params = match.group(2).strip()

        # retrieve → udc_ 접두사로
        base = re.sub(r"^retrieve", "", fn_name)
        base = base[:1].lower() + base[1:]
        udc_id = f"udc_{base}"
        cb_func = f"scwin.{udc_id}_callBackFunc"

        # ✅ cfCommonPopUp 호출 변환
        new_call = f"{udc_id}.cfCommonPopUp({cb_func}, {params})"
        code = code.replace(match.group(0), new_call)

        # ✅ 콜백 함수 템플릿 생성
        callback_code = f"""
{cb_func} = function(rtnList) {{}};
""".strip()
        callbacks.append(callback_code)

    # ✅ 콜백 함수 구분선 추가
    if callbacks:
        code += (
            "\n\n//-------------------------------------------------------------------------\n"
            "// 팝업결과\n"
            "//-------------------------------------------------------------------------\n"
        )
        code += "\n\n".join(callbacks)

    return code


def remove_jsp_expressions(code: str) -> str:
    """
    ✅ JSP 표현식(<%= ... %>)을 코드에서 제거한다.
    예: <%=ACConstants.ACCTCD_SUS_RECV%> → ACConstants.ACCTCD_SUS_RECV
    """
    # <%= ... %> 패턴 제거
    code = re.sub(r"<%=\s*(.*?)\s*%>", r"\1", code)
    return code


def rename_tagname_to_wtagname(code: str) -> str:
    """
    ✅ tagName → _wTagName 으로 변경
    - 정확히 변수나 속성으로 등장하는 tagName만 변경
    - 문자열이나 주석 안의 tagName은 무시
    """
    # 주석 제거 후, 안전하게 단어 경계 기반 치환
    code = re.sub(r"\btagName\b", "_wTagName", code)
    return code


# ---------------------
# 전체 파이프라인
# ---------------------
def convert_pipeline(code: str) -> str:
    # 0) JSP 변수 수집 (치환 전)
    jsp_vars = _find_jsp_vars(code)

    # 1) JSP 표현식/기본 변환 (getDate 포함)
    code = _normalize_jsp_vars(code)
    code = convert_var_to_let(code)

    # 2) 1-based → 0-based 등
    code = convert_for_loops(code)
    code = convert_countrow(code)

    # 3) 함수 정의/트랜잭션/ID/이벤트
    code = convert_function_def(code)
    code = convert_transaction_to_submission(code)
    code = convert_id_prefixes(code, force_autocomplete_ids=set())
    code = convert_component_event_handlers(code)

    # 4) DataSet/속성/NameValue 등
    code = convert_properties_and_namevalue(code)
    code = convert_methods(code)
    code = convert_property_access(code)  # ✅ .text/.Text/.value 읽기 대응
    code = convert_rowposition(code)
    code = convert_gauce_dataset_methods(code)
    code = convert_gauce_dataset_properties(code)

    # 5) cfXXX/유틸
    code = convert_gus_functions(code)

    # 6) f_* 사용자 함수 호출 → scwin.* 접두사 부여 (가장 마지막에)
    code = convert_f_function_calls(code)


def convert_pipeline(code: str) -> str:
    # 0️⃣ JSP 변수 수집
    jsp_vars = _find_jsp_vars(code)

    # 1️⃣ JSP 표현식/기본 변환
    code = _normalize_jsp_vars(code)
    code = convert_var_to_let(code)

    # 2️⃣ 인덱스 변환 (1-based → 0-based)
    code = convert_for_loops(code)
    code = convert_countrow(code)

    # 3️⃣ 함수 정의 / 트랜잭션 / ID / 이벤트
    code = convert_function_def(code)
    code = convert_transaction_to_submission(code)
    code = convert_id_prefixes(code, force_autocomplete_ids=set())
    code = convert_component_event_handlers(code)

    # 4️⃣ DataSet, 속성, NameValue 등
    code = convert_properties_and_namevalue(code)
    code = convert_methods(code)
    code = convert_property_access(code)
    code = convert_rowposition(code)
    code = convert_gauce_dataset_methods(code)
    code = convert_gauce_dataset_properties(code)

    # 5️⃣ cfXXX 유틸 함수들
    code = convert_gus_functions(code)

    # 6️⃣ 사용자 정의 함수 접두사(scwin.)
    code = convert_f_function_calls(code)
    code = add_options_to_hidval(code)
    code = remove_jsp_expressions(code)
    code = rename_tagname_to_wtagname(code)
    # 7️⃣ 공통 팝업 자동 판별 및 변환
    if "cfCommonPopUp" in code:
        if "cfSetReturnValue" in code:
            # ✅ cfSetReturnValue가 존재 → 콜백형(1st case)
            code = convert_common_popup_to_udc(code)
        else:
            # ✅ cfCommonPopUp만 존재 → 즉시형(2nd case)
            code = convert_common_popup_instant_to_udc(code)

    # 8️⃣ JSP 변수 헤더 prepend
    header = _make_scwin_var_inits(jsp_vars, code)
    return (header + code) if header else code
