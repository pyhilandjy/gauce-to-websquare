import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.mapping import DGAUCE_CLASSID_MAP, DGAUCE_PREFIX_MAP


# -------------------------
# Regex helpers
# -------------------------
def _get_attr(html: str, key: str) -> Optional[str]:
    """attr 값 파싱: key="..." | '...' | unquoted"""
    m = re.search(
        rf'(?is)\b{re.escape(key)}\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))',
        html,
    )
    if not m:
        return None
    return next((g for g in m.groups() if g is not None), None).strip()


def _iter(pattern: str, s: str):
    return re.finditer(pattern, s, flags=re.IGNORECASE | re.DOTALL)


def _strip_tags(html: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)
    text = re.sub(r"<\s*br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" :\u00a0\t\r\n")


# -------------------------
# Prefix / type helpers
# -------------------------
def _apply_prefix(prefix: Optional[str], obj_id: str) -> str:
    """
    중복 접두사 허용: 동일 접두사가 이미 있어도 무조건 다시 앞에 붙임.
    예) ed_ + ed_id -> ed_ed_id
    """
    return f"{prefix or ''}{obj_id}"


def _parse_classid_token_and_type(
    classid: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """classid='<%=DGauceCLSID.GRID%>' → ('GRID','gridview')"""
    if not classid:
        return None, None
    m = re.search(r"DGauceCLSID\.(\w+)", classid)
    if not m:
        return None, None
    token = m.group(1).upper()
    type_name = DGAUCE_CLASSID_MAP.get(token, token)
    return token, type_name


def _prefix_for(token: Optional[str], type_name: Optional[str]) -> Optional[str]:
    """프리픽스 결정: 타입 우선 → 토큰 백업"""
    if type_name and type_name in DGAUCE_PREFIX_MAP:
        return DGAUCE_PREFIX_MAP[type_name]
    if token and token in DGAUCE_PREFIX_MAP:
        return DGAUCE_PREFIX_MAP[token]
    return None


# -------------------------
# GAUCE params helpers
# -------------------------
def _collect_params_filtered(
    object_block: str, keys: List[str]
) -> Dict[str, Tuple[str, str, Optional[str]]]:
    """
    <param ...> 수집 (선택 키만)
    반환: {lower_key: (original_key, value, abc_optional)}
    """
    want = {k.lower() for k in keys}
    params: Dict[str, Tuple[str, str, Optional[str]]] = {}
    for m in _iter(r"<\s*param\b([^>]*)/?>", object_block):
        attrs = m.group(1) or ""
        name = _get_attr(attrs, "name") or _get_attr(attrs, "Name")
        if name and name.lower() in want:
            value = _get_attr(attrs, "value") or ""
            abc_val = _get_attr(attrs, "abc")  # abc on param
            params[name.lower()] = (name, value, abc_val)
    return params


# -------------------------
# Label/TD grouping helpers
# -------------------------
def _tds_in_tr(tr_html: str) -> List[Tuple[str, str]]:
    """tr 내부 td들을 [(attrs, innerHTML)] 순서로 반환"""
    return [
        (m.group(1) or "", m.group(2) or "")
        for m in _iter(r"<\s*td\b([^>]*)>(.*?)</\s*td\s*>", tr_html)
    ]


def _is_label_td(td_html: str) -> bool:
    """
    라벨 TD 판단: 텍스트가 의미있고, 컨트롤 태그(<object>,<input>)가 없는 경우를 우선 라벨로 간주.
    (현장 규격상 '...:&nbsp;' 형태를 주로 사용)
    """
    # 컨트롤이 있으면 라벨이 아님
    if re.search(r"<\s*object\b|<\s*input\b", td_html, flags=re.IGNORECASE):
        return False
    text = _strip_tags(td_html)
    if not text:
        return False
    # 너무 짧은 공백/구두점만 있는 경우 제외
    return True


def _has_calendar_hint(td_html: str) -> bool:
    """같은 TD 안에서 calendar.gif가 보이면 InputCalendar 접두사 최우선"""
    return bool(re.search(r"calendar\.gif", td_html, flags=re.IGNORECASE))


# -------------------------
# Controls extractors (within a single TD)
# -------------------------
def _extract_objects_from_td(
    td_html: str,
    object_attr_keys: List[str],
    param_keys: List[str],
    force_ica: bool,
) -> List[Dict[str, Any]]:
    """
    TD 내부의 <comment?><object>...</object></comment?> 블록들을 파싱
    반환: [{id, orig_id, attrs:{}, params:{}, comment_abc}]
    """
    results: List[Dict[str, Any]] = []

    for om in _iter(
        r"(?:<\s*comment\b([^>]*)>\s*)?"
        r"(<\s*object\b([^>]*)>.*?</\s*object\s*>)"
        r"(?:\s*</\s*comment\s*>)?",
        td_html,
    ):
        comment_attrs = om.group(1) or ""  # comment 속성 (abc 지원)
        o_raw = om.group(2) or ""  # object 전체 블록
        o_attrs_m = re.search(
            r"<\s*object\b([^>]*)>", o_raw, flags=re.IGNORECASE | re.DOTALL
        )
        o_attrs = o_attrs_m.group(1) if o_attrs_m else ""

        obj_id = _get_attr(o_attrs, "id")
        if not obj_id:
            continue

        # classid → prefix
        classid = _get_attr(o_attrs, "classid")
        token, type_name = _parse_classid_token_and_type(classid)
        prefix = _prefix_for(token, type_name)

        # 캘린더 힌트 시 ica_ 최우선
        if force_ica:
            prefix = "ica_"

        id_prefixed = _apply_prefix(prefix, obj_id)

        # object attributes (필터키만)
        picked_obj_attrs: Dict[str, str] = {}
        for k in object_attr_keys:
            v = _get_attr(o_attrs, k)
            if v is not None:
                picked_obj_attrs[k] = v

        # params (필터키만)
        picked_params = _collect_params_filtered(o_raw, param_keys)

        # comment abc
        comment_abc = _get_attr(comment_attrs, "abc")

        results.append(
            {
                "id": id_prefixed,
                "orig_id": obj_id,
                "attrs": picked_obj_attrs,
                "params": picked_params,  # {lower_key: (orig, val, abc)}
                "comment_abc": comment_abc,
            }
        )

    return results


def _extract_inputs_from_td(
    td_html: str,
    input_attr_keys: List[str],
) -> List[Dict[str, Any]]:
    """
    TD 내부의 <input ...> 추출 (무조건 ed_ 접두사, 중복 허용)
    반환: [{id, orig_id, attrs:{}}]
    """
    results: List[Dict[str, Any]] = []
    for im in _iter(r"<\s*input\b([^>]*)>", td_html):
        i_attrs = im.group(1) or ""
        iid = _get_attr(i_attrs, "id")
        if not iid:
            continue

        id_prefixed = _apply_prefix("ed_", iid)

        picked_inp: Dict[str, str] = {}
        for k in input_attr_keys:
            v = _get_attr(i_attrs, k)
            if v is not None:
                picked_inp[k] = v

        # input abc (항상 지원)
        abc_val = _get_attr(i_attrs, "abc")
        if abc_val is not None:
            picked_inp["abc"] = abc_val

        results.append(
            {
                "id": id_prefixed,
                "orig_id": iid,
                "attrs": picked_inp,
            }
        )

    return results


# -------------------------
# Main
# -------------------------
def extract_table_controls_text(
    input_html: str,
    object_attr_keys: List[str],  # 예: ["objType","mandatory","validExp"]
    param_keys: List[str],  # 예: ["Format","UpperFlag","ReadOnly","PromptChar"]
    input_attr_keys: Optional[
        List[str]
    ] = None,  # 예: ["objType","mandatory","validExp","maxlength"]
) -> str:
    if input_attr_keys is None:
        input_attr_keys = []

    out_lines: List[str] = []
    table_idx = 0

    # 모든 table 순회
    for tm in _iter(r"<\s*table\b([^>]*)>(.*?)</\s*table\s*>", input_html):
        table_attrs = tm.group(1) or ""
        table_body = tm.group(2) or ""
        table_id = _get_attr(table_attrs, "id")
        table_idx += 1

        out_lines.append(f"📦 TABLE [{table_idx}] id={table_id or '-'}")

        # 각 tr 안에서 td들을 순서대로 보고, 라벨 TD → 컨트롤 TD 쌍을 묶음
        for tr in _iter(r"<\s*tr\b[^>]*>(.*?)</\s*tr\s*>", table_body):
            tr_body = tr.group(1) or ""
            tds = _tds_in_tr(tr_body)
            if not tds:
                continue

            i = 0
            while i < len(tds):
                attrs_i, html_i = tds[i]
                if _is_label_td(html_i):
                    label = _strip_tags(html_i)
                    # 다음 TD가 컨트롤 컨테이너(일반적으로 바로 다음)
                    if i + 1 < len(tds):
                        ctrl_attrs, ctrl_html = tds[i + 1]

                        # 같은 TD 내 calendar.gif 여부 체크 → ica_ 우선
                        force_ica = _has_calendar_hint(ctrl_html)

                        # 1) object들
                        objs = _extract_objects_from_td(
                            ctrl_html, object_attr_keys, param_keys, force_ica
                        )
                        # 2) inputs들
                        ins = _extract_inputs_from_td(ctrl_html, input_attr_keys)

                        controls = objs + ins

                        if controls:
                            # 라벨 헤더
                            out_lines.append(f"  • {label}")

                            # 각 컨트롤 상세
                            for c in controls:
                                out_lines.append(
                                    f"    - id={c['id']}  (orig: {c['orig_id']})"
                                )

                                # attributes
                                # object: attrs + comment abc
                                # input: attrs(dict에 이미 abc 포함시켜둠)
                                all_attrs = dict(c.get("attrs") or {})
                                if c.get("comment_abc") is not None:
                                    all_attrs["abc"] = c["comment_abc"]

                                if all_attrs:
                                    out_lines.append(f"      - attributes:")
                                    # object_attr_keys / input_attr_keys 순서를 우선
                                    ordered_keys = (
                                        object_attr_keys
                                        if "params" in c
                                        else input_attr_keys
                                    )
                                    for k in ordered_keys:
                                        if k in all_attrs:
                                            out_lines.append(
                                                f"          {k} = {all_attrs[k]}"
                                            )
                                    # 나머지 키(abc 등)
                                    for k, v in all_attrs.items():
                                        if k not in ordered_keys:
                                            out_lines.append(f"          {k} = {v}")

                                # params (object만)
                                if "params" in c and c["params"]:
                                    out_lines.append(f"      - params:")
                                    for k in param_keys:
                                        lk = k.lower()
                                        if lk in c["params"]:
                                            _orig, val, abc = c["params"][lk]
                                            out_lines.append(f"          {k} = {val}")
                                            if abc is not None:
                                                out_lines.append(
                                                    f"          {k}.abc = {abc}"
                                                )

                            # 라벨 쌍을 소비했으니 i += 2
                            i += 2
                            continue
                # 라벨이 아니거나 컨트롤이 없으면 다음 td
                i += 1

        out_lines.append("")  # 테이블 구분 빈줄

    # 꼬리 공백 정리
    while out_lines and out_lines[-1] == "":
        out_lines.pop()

    return "\n".join(out_lines)
