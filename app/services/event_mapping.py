# event_mapping.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional

# ---- 1) 대상 타입 추론용 접두어 규칙 ----
TARGET_TYPE_PREFIXES: Dict[str, List[str]] = {
    "transaction": ["tr_"],  # GAUCE TR
    "submission": ["sbm_"],  # WebSquare Submission (이미 변환된 케이스)
    "dataset": ["ds_", "dlt_", "dma_", "dsa_"],
    "gridview": ["gr_", "grid_", "gv_"],
    "input": ["ed_", "em_", "ibx_", "ipt_", "ed", "em"],  # 관용적
    "text": ["txt_"],
    "trigger": ["btn_", "img_"],
    "radio": ["rd_"],
    "select": ["lc_"],
    "treeview": ["tv_", "tree_", "trv_"],
    "tab": ["tac_", "tab_", "mxTab"],
}


def infer_target_type(comp_id: str) -> Optional[str]:
    low = comp_id.lower()
    for tp, prefixes in TARGET_TYPE_PREFIXES.items():
        for p in prefixes:
            if low.startswith(p.lower()):
                return tp
    return None


# ---- 2) 이벤트명 매핑(타입별) ----
EVENT_NAME_MAP_BY_TYPE: Dict[str, Dict[str, str]] = {
    # Transaction/Submission
    "transaction": {
        "OnSuccess": "_submitdone",
        "OnFail": "_submiterror",
    },
    "submission": {
        "OnSuccess": "_submitdone",
        "OnFail": "_submiterror",
    },
    # Dataset (보수적: 그대로 dataset의 이벤트로 보냄)
    # 필요 시 프로젝트 정책으로 Submission 완료로 승격하여 합치는 로직을 event_converter에서 옵션으로 제공
    "dataset": {
        "OnLoadStarted": "_onloadstarted",
        "OnLoadCompleted": "_onloadcompleted",  # rowCnt → 내부에서 ds.getRowCount() 재계산 주석/보정
        "OnLoadError": "_onloaderror",
    },
    # Grid
    "gridview": {
        "OnClick": "_oncellclick",
        "OnDblClick": "_oncelldblclick",
        "OnHeadCheckClick": "_onheaderclick",
        "OnPopup": "_onpopup",
    },
    # Input/Text/Trigger 등 공통
    "input": {
        "OnKillFocus": "_onblur",
        "onKillFocus": "_onblur",
        "OnFocus": "_onfocus",
        "OnChange": "_onchange",  # Text는 onviewchange를 쓰는 프로젝트도 있음
        "OnKeyUp": "_onkeyup",
        "OnKeyDown": "_onkeydown",
    },
    "text": {
        "OnChange": "_onviewchange",
        "OnKeyUp": "_onkeyup",
        "OnKeyDown": "_onkeydown",
    },
    "trigger": {
        "OnClick": "_onclick",
        "click": "_onclick",
    },
    "radio": {
        "OnSelChange": "_onchange",
    },
    "select": {
        "OnSelChange": "_onchange",
        "OnCloseUp": "_onchange",
        "onDropDown": "_onclick",  # 필요 시 _onbeforeselect로 교체
    },
    "treeview": {
        "OnClick": "_onclick",
        "OnItemClick": "_onlabelclick",
    },
    "tab": {
        "OnChange": "_onchange",
    },
}


# ---- 3) 기본 폴백: OnXxx → onxxx ----
def default_event_suffix(ev_name: str) -> str:
    if not ev_name:
        return "_onunknown"
    if ev_name.startswith("On"):
        return "_on" + ev_name[2:].lower()
    if ev_name.startswith("on"):
        return "_" + ev_name.lower()
    return "_" + ev_name.lower()


# ---- 4) 시그니처/파라미터 이름 매핑 ----
# (본문 내부 변수 이름도 함께 치환하기 위함)
PARAMS_MAP_BY_TYPE: Dict[str, Dict[str, Tuple[List[str], Dict[str, str]]]] = {
    # type → event → (args list, body rename map)
    "gridview": {
        "OnClick": (
            ["rowIndex", "columnIndex", "columnId"],
            {
                "Row": "rowIndex",
                "Col": "columnIndex",
                "Colid": "columnId",
                "row": "rowIndex",
                "colid": "columnId",
            },
        ),
        "OnDblClick": (
            ["rowIndex", "columnIndex", "columnId"],
            {
                "Row": "rowIndex",
                "Col": "columnIndex",
                "Colid": "columnId",
                "row": "rowIndex",
                "colid": "columnId",
            },
        ),
        "OnHeadCheckClick": (
            ["headerId"],
            {
                "Colid": "headerId",
                "Col": "headerId",
                "bCheck": "/* bCheck: 헤더 체크 상태는 별도 조회 필요 */",
            },
        ),
        "OnPopup": (
            ["rowIndex", "columnId", "data"],
            {"row": "rowIndex", "colid": "columnId"},
        ),
    },
    "dataset": {
        "OnLoadStarted": (["e"], {}),
        "OnLoadCompleted": (
            ["e"],
            {"rowCnt": "/* rowCnt: ds.getRowCount() 사용 권장 */"},
        ),
        "OnLoadError": (["e"], {}),
    },
    "transaction": {
        "OnSuccess": (["e"], {}),
        "OnFail": (["e"], {}),
    },
    "submission": {
        "OnSuccess": (["e"], {}),
        "OnFail": (["e"], {}),
    },
    "input": {
        "OnKillFocus": (["e"], {}),
        "OnFocus": (["e"], {}),
        "OnChange": (["e"], {}),
        "OnKeyUp": (["e"], {}),
        "OnKeyDown": (["e"], {}),
    },
    "text": {
        "OnChange": (["info"], {}),
        "OnKeyUp": (["e"], {}),
        "OnKeyDown": (["e"], {}),
    },
    "trigger": {
        "OnClick": (["e"], {}),
        "click": (["e"], {}),
    },
    "radio": {
        "OnSelChange": (["e"], {}),
    },
    "select": {
        "OnSelChange": (["e"], {}),
        "OnCloseUp": (["e"], {}),
        "onDropDown": (["e"], {}),
    },
    "treeview": {
        "OnClick": (["e"], {}),
        "OnItemClick": (["e"], {}),
    },
    "tab": {
        "OnChange": (["e"], {}),
    },
}


# ---- 5) tr_ → sbm_ 네이밍 규칙 ----
def normalize_target_id_for_event(comp_id: str, target_type: Optional[str]) -> str:
    if target_type == "transaction" and comp_id.lower().startswith("tr_"):
        return "sbm_" + comp_id[3:]
    return comp_id
