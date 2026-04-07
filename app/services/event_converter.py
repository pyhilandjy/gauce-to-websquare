# event_converter.py
from __future__ import annotations
import re
from typing import Match, Optional, Iterable, List
from .event_mapping import (
    infer_target_type,
    EVENT_NAME_MAP_BY_TYPE,
    default_event_suffix,
    PARAMS_MAP_BY_TYPE,
    normalize_target_id_for_event,
)

SCRIPT_TAG_RE = re.compile(
    r"""(?is)
    <script\b[^>]*          # <script ... 
    \bfor\s*=\s*            #   for=
    (?P<q1>["'])?           #   optional quote
    (?P<target>[A-Za-z_]\w*)#   component id
    (?P=q1)?                #   optional close quote
    [^>]*\bevent\s*=\s*     #   ... event=
    (?P<q2>["'])?           #   optional quote
    (?P<ev>[A-Za-z_]\w*)    #   event name (OnClick ...)
    (?:\((?P<sig>[^)]*)\))? #   optional signature tokens (Row,Colid)
    (?P=q2)?                #   optional close quote
    [^>]*>                  #   >
    (?P<body>.*?)           #   body
    </script>               # </script>
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)

WS_BOUNDS = r"(?<![A-Za-z_0-9]){old}(?![A-Za-z_0-9])"


# --- 1) 본문 들여쓰기 ---
def _indent_body(body: str, indent: str = "  ") -> str:
    body = body.strip("\n\r ")
    if not body:
        return ""
    lines = body.splitlines()
    return "\n".join((indent + ln if ln.strip() != "" else "") for ln in lines)


# --- 2) f_* 로컬 함수 호출에 scwin. 자동 접두 ---
#    - 이미 점(.)으로 수식된 호출(obj.f_xxx(...))은 건드리지 않음
#    - 정의가 아니라 "호출"만 처리 (name(...))
#    - 기본 접두 후보: f_, F_
def _qualify_scwin_user_funcs(body: str, prefixes: Iterable[str] = ("f_", "F_")) -> str:
    # prefix들을 OR로 묶은 정규식
    p_alt = "|".join(re.escape(p) for p in prefixes)
    # name(...): 앞에 단어경계가 있고, name 앞에 '.'가 바로 붙어 있지 않아야 함
    call_re = re.compile(rf"\b(?P<name>(?:{p_alt})[A-Za-z_]\w*)\s*\(", re.MULTILINE)

    def repl(m: Match) -> str:
        start = m.start("name")
        src = m.string
        # 이미 obj.f_xxx(...) 형태면 skip
        if start > 0 and src[start - 1] == ".":
            return m.group(0)
        # 드문 케이스: function f_xxx( ... ) 정의가 본문에 있을 수 있으니 방지
        # 바로 앞 20자 안에 'function ' 토큰이 있는지 대충 점검
        lookbehind = src[max(0, start - 20) : start]
        if re.search(r"\bfunction\s*$", lookbehind):
            return m.group(0)
        # 접두 추가
        return "scwin." + m.group("name") + "("

    return call_re.sub(repl, body)


# --- 3) 이벤트명/파라미터 정규화 ---
def _map_event_suffix(target_type: Optional[str], ev_name: str) -> str:
    if target_type and target_type in EVENT_NAME_MAP_BY_TYPE:
        m = EVENT_NAME_MAP_BY_TYPE[target_type].get(ev_name)
        if m:
            return m
    return default_event_suffix(ev_name)


def _norm_args_and_body(
    target_type: Optional[str], ev_name: str, body: str
) -> tuple[list[str], str]:
    args = ["e"]
    rename_map = None
    if target_type and target_type in PARAMS_MAP_BY_TYPE:
        spec = PARAMS_MAP_BY_TYPE[target_type].get(ev_name)
        if spec:
            args, rename_map = spec
    # 변수명 치환 (Row -> rowIndex 등)
    if rename_map:
        for old, new in rename_map.items():
            patt = re.compile(WS_BOUNDS.format(old=re.escape(old)))
            body = patt.sub(new, body)
    # f_* 호출에 scwin. 접두
    body = _qualify_scwin_user_funcs(body, prefixes=("f_", "F_"))
    return args, body


# --- 4) 핸들러 생성 ---
def _build_handler(target_id: str, ev_suffix: str, args: list[str], body: str) -> str:
    body_indented = _indent_body(body, indent="  ")
    return f"scwin.{target_id}{ev_suffix} = function ({', '.join(args)}) {{\n{body_indented}\n}};\n"


# --- 5) 메인: 스크립트 이벤트 변환 ---
def convert_script_events(code: str, *, promote_ds_to_submission: bool = False) -> str:
    """
    <script for=... event=...>...</script> → scwin.<id>_<event> = function (...) { ... };
    - 들여쓰기 정상화
    - 본문 내 f_* 호출에 scwin. 자동 접두 (이미 obj.f_*는 제외)
    - (옵션) ds_* 이벤트를 sbm_* 완료/에러로 승격
    """
    out_parts: List[str] = []
    last = 0

    for m in SCRIPT_TAG_RE.finditer(code):
        out_parts.append(code[last : m.start()])

        target = m.group("target")
        ev_name = m.group("ev")
        body = m.group("body") or ""

        target_type = infer_target_type(target)
        ev_suffix = _map_event_suffix(target_type, ev_name)

        # tr_ → sbm_ 정규화
        norm_id = normalize_target_id_for_event(target, target_type)

        # 인자/본문 정규화 + scwin. 접두
        args, body2 = _norm_args_and_body(target_type, ev_name, body)

        # (선택) ds_* → sbm_* 승격
        if promote_ds_to_submission and target_type == "dataset":
            if ev_name == "OnLoadCompleted":
                if norm_id.lower().startswith("ds_"):
                    norm_id = "sbm_" + norm_id[3:]
                ev_suffix = "_submitdone"
            elif ev_name == "OnLoadError":
                if norm_id.lower().startswith("ds_"):
                    norm_id = "sbm_" + norm_id[3:]
                ev_suffix = "_submiterror"

        handler = _build_handler(norm_id, ev_suffix, args, body2)
        out_parts.append(handler)
        last = m.end()

    out_parts.append(code[last:])
    return "".join(out_parts)
