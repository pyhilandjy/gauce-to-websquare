from typing import Dict, List

# -----------------------
# 1) 단순 속성/메서드 매핑
# -----------------------
PROPERTY_MAP: Dict[str, str] = {
    "Text": "setValue",
    "value": "setValue",
    "Enable": "setDisabled",  # true/false 반전
    "disabled": "setDisabled",  # 그대로 true/false
    "NameValue.set": "setCellData",
    "NameValue.get": "getCellData",
}

METHOD_MAP: Dict[str, str] = {
    "Focus": "focus",
    "AddRow": "addRow",
    "ClearData": "clearData",
    "SetDataHeader": "setDataHeader",
    "Post": "send",
}

# mapper.py

# ...기존 항목 유지...

# GAUCE/GUS 유틸 호출 → WebSquare 호출 (완전수식)
# 값은 *인자 없는* “접두사+함수명”까지만 둔다. 인자는 변환기에서 그대로 전달.
FUNCTION_MAP: Dict[str, str] = {
    # ---- $c.gus.* ----
    "cfProgressWinOpen": "$c.gus.cfProgressWinOpen",
    "cfProgressWinClose": "$c.gus.cfProgressWinClose",
    "cfGetFileURL": "$c.gus.cfGetFileURL",
    "cfGetTargetFileURL": "$c.gus.cfGetTargetFileURL",
    "cfDownloadFile": "$c.gus.cfDownloadFile",
    "cfCopyDataSet": "$c.gus.cfCopyDataSet",
    "cfCopyDataSetHeader": "$c.gus.cfCopyDataSetHeader",
    "cfCopyRecord": "$c.gus.cfCopyRecord",
    "cfParseFeature": "$c.gus.cfParseFeature",
    "cfPrepareHidVal": "$c.gus.cfPrepareHidVal",
    "cfPrepareObjectHidVal": "$c.gus.cfPrepareObjectHidVal",
    "cfUndoGridRows": "$c.gus.cfUndoGridRows",
    "cfGrdHeiht": "$c.gus.cfGrdHeiht",
    "cfDelHistoryAll": "$c.gus.cfDelHistoryAll",
    "cfDelOption": "$c.gus.cfDelOption",
    "cfCanOpenPopup": "$c.gus.cfCanOpenPopup",
    "cfSetReturnValue": "$c.gus.cfSetReturnValue",
    "cfSetGridReturnValue": "$c.gus.cfSetGridReturnValue",
    "cfShowCrnInfo": "$c.gus.cfShowCrnInfo",
    "cfViewClntInfo": "$c.gus.cfViewClntInfo",
    "cfShowSlipInfo": "$c.gus.cfShowSlipInfo",
    "cfGetAuthCode": "$c.gus.cfGetAuthCode",
    "cfCheckAuth": "$c.gus.cfCheckAuth",
    "cfCheckAuthCREATE": "$c.gus.cfCheckAuthCREATE",
    "cfCheckAuthRETRIEVE": "$c.gus.cfCheckAuthRETRIEVE",
    "cfCheckAuthUPDATE": "$c.gus.cfCheckAuthUPDATE",
    "cfCheckAuthDELETE": "$c.gus.cfCheckAuthDELETE",
    "cfCheckAuthPRINT": "$c.gus.cfCheckAuthPRINT",
    "cfCheckAuthEXCEL": "$c.gus.cfCheckAuthEXCEL",
    "cfValidate": "$c.gus.cfValidate",
    "cfValidateItem": "$c.gus.cfValidateItem",
    "cfValidateGrid": "$c.gus.cfValidateGrid",
    "isMandatory": "$c.gus.isMandatory",
    "cfTurnCreateFlag": "$c.gus.cfTurnCreateFlag",
    "cfCheckCreateFlag": "$c.gus.cfCheckCreateFlag",
    "cfLimitByteLength": "$c.gus.cfLimitByteLength",
    "cfIsAfterDate": "$c.gus.cfIsAfterDate",
    "cfEnableKeyData": "$c.gus.cfEnableKeyData",
    "cfDisableKeyData": "$c.gus.cfDisableKeyData",
    "cfDisableKey": "$c.gus.cfDisableKey",
    "cfEnableAllBtn": "$c.gus.cfEnableAllBtn",
    "cfDisableAllBtn": "$c.gus.cfDisableAllBtn",
    "cfDisableBtn": "$c.gus.cfDisableBtn([$c.gus.getctrlBtn])<-",
    "cfDisableBtnOnly": "$c.gus.cfDisableBtnOnly",
    "cfEnableBtnOnly": "$c.gus.cfEnableBtnOnly",
    "cfEnableObj": "$c.gus.cfEnableObj",
    "cfCheckExchRt": "$c.gus.cfCheckExchRt",
    "cfGoPrevPosition": "$c.gus.cfGoPrevPosition",
    "cfHistoryExist": "$c.gus.cfHistoryExist",
    "cfToUpper": "$c.gus.cfToUpper",
    "cfToLower": "$c.gus.cfToLower",
    "cfGetSysCdFromPageId": "$c.gus.cfGetSysCdFromPageId",
    "cfDigitalNumber": "$c.gus.cfDigitalNumber",
    "cfDisable": "$c.gus.cfDisable",
    "cfDisableObjects": "$c.gus.cfDisableObjects",
    "cfEnableObjects": "$c.gus.cfEnableObjects",
    "cfInitHidVal": "$c.gus.cfInitHidVal",
    "cfInitObjects": "$c.gus.cfInitObjects",
    "cfDisableElement": "$c.gus.cfDisableElement",
    "cfEnable": "$c.gus.cfEnable",
    "cfEnableElement": "$c.gus.cfEnableElement",
    "cfGetCurrentDate": "$c.gus.cfGetCurrentDate",
    "cfGetElementType": "$c.gus.cfGetElementType",
    "cfGetByteLength": "$c.gus.cfGetByteLength",
    "cfGetLeftPad": "$c.gus.cfGetLeftPad",
    "cfInsertComma": "$c.gus.cfInsertComma",
    "cfGetFormatStr": "$c.gus.cfGetFormatStr",
    "cfAddTempColumn": "$c.gus.cfAddTempColumn",
    "cfGetMsg": "$c.gus.cfGetMsg",
    "cfInitObj": "$c.gus.cfInitObj",
    "cfIsEnterKey": "$c.gus.cfIsEnterKey",
    "cfIsNull": "$c.gus.cfIsNull",
    "cfIsIn": "$c.gus.cfIsIn",
    "cfClearPairObj": "$c.gus.cfClearPairObj",
    "cfGetValue": "$c.gus.cfGetValue",
    "cfSetValue": "$c.gus.cfSetValue",
    "cfGetHiddenValue": "$c.gus.cfGetHiddenValue",
    "cfSetHiddenValue": "$c.gus.cfSetHiddenValue",
    "cfYearsBetween": "$c.gus.cfYearsBetween",
    "cfMonthsBetween": "$c.gus.cfMonthsBetween",
    "cfDifferBetween": "$c.gus.cfDifferBetween",
    "putMapValue": "$c.gus.putMapValue",
    "getMapValue": "$c.gus.getMapValue",
    "JsMap": "$c.gus.JsMap",
    "cfConvert2Weight": "$c.gus.cfConvert2Weight",
    "cfCheckCrnBusiCls": "$c.gus.cfCheckCrnBusiCls",
    "cfisEnglish": "$c.gus.cfisEnglish",
    "cfisEnglishCnt": "$c.gus.cfisEnglishCnt",
    "cfisNumberCnt": "$c.gus.cfisNumberCnt",
    "cfnumChainChk": "$c.gus.cfnumChainChk",
    "cfSmsTelValidChk": "$c.gus.cfSmsTelValidChk",
    "cfGrdWidth": "$c.gus.cfGrdWidth",
    # ---- $c.data.* ----
    "cfGridToExcel": "$c.data.downloadGridViewExcel",
    "cfNaviPageIn": "$c.data.getParameter",
    "cfNaviPageOut": "$c.data.getParameter",  # 필요시 setParameter로 교체
    "coMessage": "$c.data.getMessage",
    "coMessage_getMsg": "$c.data.getMessage.getMsg",
    # ---- $c.win.* ----
    "cfConfirmMsg": "await $c.win.confirm",
    "cfAlertMsg": "$c.win.alert",
}

FUNCTION_MAP_LOWER = {k.lower(): v for k, v in FUNCTION_MAP.items()}


# -----------------------------------------
# 2) GAUCE DataSet API → WebSquare 매핑 추가
# -----------------------------------------
_GAUCE_METHOD_MAP_LOWER = {
    "cleardata": "removeAll",
    "addrow": "insertRow",
    "insertrow": "insertRow",
    "deleterow": "removeRow",
    "removerow": "removeRow",
    "resetstatus": "resetStatus",
    "undoall": "undoAll",
    "undo": "undoRow",
    "filter": "filter",
    "deletemarked": "deleteRows",
    "countrow": "getRowCount",
    "isupdated": "getModifiedIndex().length > 0",
}

GAUCE_DATASET_PROPERTY_SETTER_MAP: Dict[str, str] = {
    "UseChangeInfo": "setUseChangeInfo",
}

# ------------------------------------------------
# 3) 컴포넌트 접두어/이벤트 매핑 (id 기반 자동 추론)
# ------------------------------------------------
COMPONENT_PREFIX_MAP = {
    "gridview": ["gr_", "grid_", "gv_", "gr_"],
    "selectbox": ["lc_"],
    "autocomplete": ["acb_", "lux_d_"],
    "inputbox": ["ed_", "em_", "txt_", "ipt_", "ibx_"],
    "treeview": ["tv_", "tree_", "trv_"],
    "radio": ["rd_"],
    "tab": ["tac_", "tab_", "mxTab"],
    "dataset": ["ds_", "dlt_", "dma_", "dsa_", "bd_"],
    "trigger": ["btn_", "img_"],
    "submission": ["sbm_", "tr_"],
    "textarea": ["txt_", "ta_", "tb_", "txa_"],
}

EVENT_MAP_BY_TYPE = {
    "selectbox": {
        "OnSelChange": "onchange",
        "OnSelChange2": "onselected",
        "OnCloseUp": "onchange",
        "onDropDown": "onclick",  # 필요 시 onbeforeselect로 교체
    },
    "gridview": {
        "OnClick": "oncellclick",
        "OnDblClick": "oncelldblclick",
        "OnHeadCheckClick": "onheaderclick",
        "OnDropDown": "onbeforeedit",
        "OnCloseUp": "oneditend",
        "OnColumnPosChanged": "onaftercolumnmove",
        "OnColIndexChanged": "onaftercolumnmove",
    },
    "inputbox": {
        "onKillFocus": "onblur",
        "onKeyUp": "onkeyup",
        "onChange": "onviewchange",
    },
    "treeview": {
        "OnClick": "onclick",
        "OnItemClick": "onlabelclick",
    },
    "radio": {
        "OnSelChange": "onchange",
    },
    "dataset": {
        "OnRowPosChanged": "onrowpositionchange",
        "onColumnChanged": "oncelldatachange",
        "OnRowsetChanged": "onaftercolumnfilterchange",
    },
}

# --------------------------------------------
# 4) ID 접두어 치환 (Gauce → WebSquare)
# --------------------------------------------
ID_PREFIX_MAP: Dict[str, str] = {
    "em_": "ed_",
    "txt_": "ed_",  # 텍스트 입력 통합
    # TAB
    "mxTab": "tac_",
    # BIND → DataMap
    "bd_": "dma_",
    # DATASET
    "ds_": "ds_",
    # TR → Submission
    "tr_": "sbm_",
    # TEXTAREA 묶음
    "ta_": "txt_",
    "tb_": "txt_",
    "txa_": "txt_",
    # img → Trigger
    "img_": "btn_",
}


# --------------------------------------------
# 4) 그리드 속성 치환 (Gauce → WebSquare)
# --------------------------------------------
GRIDVIEW_PROPERTY_MAP = {
    # 열 더블클릭로 자동 너비 맞춤(행 내용 기준)
    "AutoResizing": {
        "by_value": {
            "true": ["autoFit = allColumn"],
            "1": ["autoFit = allColumn"],
            "false": ["-"],
            "0": ["-"],
        }
    },
    # 셀 편집 시 에디트박스 표시 트리거
    # (False면 명시적으로 끄거나 생략하고 싶으면 "editModeEvent = none" 또는 "-"로)
    "AllShowEdit": {
        "by_value": {
            "true": ["editModeEvent = onclick"],
            "1": ["editModeEvent = onclick"],
            "false": ["editModeEvent = none"],
            "0": ["editModeEvent = none"],
        }
    },
    # 컬럼 리사이즈 가능
    "ColSizing": {
        "by_value": {
            "true": ["-"],
            "1": ["-"],
            "false": ["Resize = false"],
            "0": ["Resize = false"],
        }
    },
    # 컬럼 드래그-앤-드롭 이동
    "DragDropEnable": {
        "by_value": {
            "true": ["columnMove = true"],
            "1": ["columnMove = true"],
            "false": ["Resize = false"],
            "0": ["Resize = false"],
        }
    },
    # 다중 행 선택(드래그/Shift/Ctrl)
    "MultiRowSelect": {
        "by_value": {
            "true": [
                "-",
                "dataDragSelectAutoScroll = true",
                "focusMode = cell or row or both",
            ],
            "1": [
                "-",
                "dataDragSelectAutoScroll = true",
                "focusMode = cell or row or both",
            ],
            "false": [
                "dataDragSelect = false",
                "focusMode = cell",
            ],
            "0": [
                "dataDragSelect = false",
                "focusMode = cell",
            ],
        }
    },
    # 윈도우 스타일 다중 선택(라이브러리별 옵션 명만 다름 → 동일 처리)
    "AddSelectRows": {
        "by_value": {
            "true": [
                "dataDragSelectAutoScroll = true",
            ],
            "1": [
                "dataDragSelectAutoScroll = true",
            ],
            "false": [
                "dataDragSelect = false",
            ],
            "0": [
                "dataDragSelect = false",
            ],
        }
    },
    # 요약(합계) 행
    "ViewSummary": {
        "by_value": {
            "1": ["퍼블(footer)"],
            "true": ["퍼블(footer)"],
            "0": ["퍼블(footer)"],
            "false": ["퍼블(footer)"],
        }
    },
    # 편집 가능 여부 → readOnly 반전
    "Editable": {
        "by_value": {
            "true": ["-"],
            "1": ["-"],
            "false": ["readOnly = true"],
            "0": ["readOnly = true"],
        }
    },
    # 정렬 라벨/방향
    "SortView": {
        "by_value": {
            "left": ["-"],
            "right": ["-"],
        }
    },
    # 원클릭 체크(체크박스 동작 단순화)
    "UsingOneClick": {
        "by_value": {
            "1": ["-"],
            "true": ["-"],
            "0": ["-"],
            "false": ["-"],
        }
    },
    # 반전 여부
    "colselect": {
        "by_value": {
            "true": ["focusMode = cell"],
            "1": ["focusMode = cell"],
            "false": ["-"],
            "0": ["-"],
        }
    },
    # 재그리기(대부분 기본 동작이므로 생략)
    "ReDraw": {"by_value": {}},  # 매핑 없음 → '-'
    # DataID는 컬럼/데이터 바인딩 메타 → 전역 옵션 변환 없음
    "DataID": {"by_value": {}},
    # 셀 렌더러/에디터 전용 이미지 설정 → 전역 옵션 변환 없음
    "UrlImages": {"by_value": {}},
}


############# 프로퍼티 ####################
# mapper.py

# DGauce 토큰 → 내부 타입 매핑
DGAUCE_CLASSID_MAP: Dict[str, str] = {
    "EMEDIT": "inputbox",
    "GRID": "gridview",
    "TREE": "treeview",
    "COMBO": "selectbox",
    "RADIO": "radio",
    "TEXTAREA": "textarea",
    "DATASET": "dataset",
    "SUBMIT": "submission",
}

# 타입/토큰 → id prefix 매핑
DGAUCE_PREFIX_MAP: Dict[str, str] = {
    # 타입 기준
    "gridview": "gr_",
    "inputbox": "ed_",
    "treeview": "tr_",
    "selectbox": "cb_",
    "radio": "rb_",
    "textarea": "ta_",
    "dataset": "ds_",
    "submission": "sbm_",
    # 토큰 백업
    "GRID": "gr_",
    "EMEDIT": "ed_",
    "TREE": "tr_",
    "COMBO": "cb_",
    "RADIO": "rb_",
    "TEXTAREA": "ta_",
    "DATASET": "ds_",
    "SUBMIT": "sbm_",
}

# (참고/확장용) WebSquare 컴포넌트 → prefix 매핑표
# 현재 로직에서는 'calendar.gif' 힌트 시 ica_ 우선 적용만 사용.
COMPONENT_PREFIX_MAP: Dict[str, str] = {
    "Accordion": "acd_",
    "aliasDataList": "adl_",
    "aliasDataMap": "adm_",
    "Anchor": "btn_",
    "Article": "art_",
    "Aside": "asi_",
    "Audio": "aud_",
    "AutoComplete": "acb_",
    "Button": "btn_",
    "Calendar": "cal_",
    "Canvas": "cvs_",
    "Caption": "",
    "Checkbox": "cbx_",
    "CheckCombobox": "ccb_",
    "DataList": "ds_",
    "DataMap": "dma_",
    "DatePicker": "dpk_",
    "Editor": "edt_",
    "Fliptoggle": "ftg_",
    "FloatingLayer": "flt_",
    "Footer": "fot_",
    "Fusionchart": "cht_",
    "FwBulletChart": "cht_",
    "FwFunnelChart": "cht_",
    "FwGanttChart": "cht_",
    "FwGaugeChart": "cht_",
    "FwPyramidChart": "cht_",
    "FwRealtimeChart": "cht_",
    "FwSparkChart": "cht_",
    "Generator": "gen_",
    "GridBody": "",
    "GridFooter": "",
    "GridHeader": "",
    "GridLayout": "gdl_",
    "GridSubTotal": "",
    "GridView": "gr_",
    "Group": "grp_",
    "Header": "hea_",
    "IFrame": "ifm_",
    "Image": "img_",
    "InputBox": "ed_",
    "InputCalendar": "ica_",
    "LinkedDataList": "ldt_",
    "MapChart": "cht_",
    "MultiSelect": "msb_",
    "Multiupload": "mpd_",
    "Navigation": "nav_",
    "Output": "opt_",
    "PageControl": "pgc_",
    "PageFrame": "pfm_",
    "PageList": "pgl_",
    "Pivot": "piv_",
    "Progressbar": "prg_",
    "Radio": "rd_",
    "RoundedRectangle": "rdr_",
    "ScheduleCalendar": "shc_",
    "ScrollView": "scv_",
    "SearchBox": "sbx_",
    "Secret": "sct_",
    "Section": "sec_",
    "SelectBox": "lc_",
    "SlideHide": "shd_",
    "Slider": "sld_",
    "Span": "spa_",
    "Spinner": "spi_",
    "Submission": "sbm_",
    "Switch": "swh_",
    "TabControl": "tac_",
    "TableLayout": "tbl_",
    "Tag": "tag_",
    "Textarea": "txt_",
    "Textbox": "tbx_",
    "TreeView": "tv_",
}
