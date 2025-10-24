from __future__ import annotations
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Literal
import os
import pandas as pd
import re
import yaml
from pathlib import Path
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import Environment, meta as jinja_meta, nodes
from jinja2.visitor import NodeVisitor

def csv_to_srt(
    csv_file: str,
    output_path: str,
    content_col_name: str = 'ko', # ko, en, ja, etc
    speaker_col_name: str = 'Speaker Name',
    start_time_col_name: str = 'Start Time',
    end_time_col_name: str = 'End Time',
    include_speaker: bool = False
):

    """
    Read a single CSV through TTS_CSV and export it as an SRT file.

    Args:
        csv_file (str): Path to the input CSV file.
        output_path (str): Path where the .srt will be saved.
        content_key (str): Column name to use for subtitle text.
        speaker_key (str): Column name for speaker names.
        include_speaker (bool): If True, prepend the speaker name to each subtitle line.
    """
    # 1) Load CSV into TTS_CSV (handles time conversion, diff, merging, etc.)
    df = pd.read_csv(csv_file)

    # 2) Sort rows by start time
    df.sort_values(by=start_time_col_name, inplace=True, ignore_index=True)

    def convert_time_format(time_str):
        """
        hh:mm:ss:ms -> hh:mm:ss,ms 형식으로 변환
        """
        if isinstance(time_str, str) and len(time_str.split(':')) == 4:
            parts = time_str.split(':')
            milliseconds = parts[3].ljust(3, '0')  # 밀리초를 3자리로 맞춤
            return f"{parts[0]}:{parts[1]}:{parts[2]},{milliseconds}"
        else:
            raise ValueError(f"Invalid time format: {time_str}")

    # 4) Build SRT blocks
    srt_blocks = []
    for idx, row in df.iterrows():
        start_ts = convert_time_format(row[start_time_col_name])
        end_ts   = convert_time_format(row[end_time_col_name])
        text     = str(row.get(content_col_name, "")).strip()

        # Optionally prepend speaker
        if include_speaker:
            speaker = row.get(speaker_col_name, "")
            if isinstance(speaker, str) and speaker:
                text = f"{speaker}: {text}"

        block = (
            f"{idx+1}\n"
            f"{start_ts} --> {end_ts}\n"
            f"{text}\n"
        )
        srt_blocks.append(block)

    # 5) Write out to .srt file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(srt_blocks))

    print(f"\033[92mSRT file saved to {output_path}\033[0m")

    return output_path


def parse_inputs_meta(tpl_src: str) -> Dict[str, Any]:
    """
    inputs: 블록을 견고하게 파싱 (주석/빈줄 허용, 최상위 키에서 종료).
    """
    lines = tpl_src.splitlines(True)
    start_idx = None
    for i, line in enumerate(lines):
        # 주석/공백 무시하면서 'inputs:' 찾기
        if re.match(r'^\s*inputs\s*:\s*(#.*)?\r?\n?$', line):
            start_idx = i
            break
    if start_idx is None:
        return {}

    # inputs: 다음 줄부터 들여쓴 라인만 수집
    buf = ["inputs:\n"]
    for line in lines[start_idx + 1:]:
        if re.match(r'^[ \t]+', line):             # 들여쓴 라인(서브 블록)
            buf.append(line)
        elif re.match(r'^\s*$', line):             # 빈 줄은 유지
            buf.append(line)
        else:
            # 최상위(들여쓰기 0) 라인이면 종료 (주석 포함)
            break

    try:
        data = yaml.safe_load("".join(buf)) or {}
        return data.get("inputs", {}) if isinstance(data, dict) else {}
    except Exception:
        return {}


def extract_jinja_default_filters_ast(tpl_src: str) -> dict[str, object]:
    env = Environment()
    ast = env.parse(tpl_src)
    out: dict[str, object] = {}

    class Visitor(NodeVisitor):
        def visit_Filter(self, node: nodes.Filter, *args, **kwargs):
            if node.name == "default" and node.node is not None and node.args:
                # recover the variable name (supports dotted names)
                var_name = _resolve_var_name(node.node)
                if var_name:
                    # first arg is the default value expression
                    val = _eval_literal(node.args[0])
                    out.setdefault(var_name, val)
            self.generic_visit(node)

    def _resolve_var_name(node: nodes.Node) -> str | None:
        if isinstance(node, nodes.Name):
            return node.name
        if isinstance(node, nodes.Getattr):
            base = _resolve_var_name(node.node)
            return f"{base}.{node.attr}" if base else None
        if isinstance(node, nodes.Getitem):
            base = _resolve_var_name(node.node)
            key = _eval_literal(node.arg)
            if base is not None and isinstance(key, (str, int)):
                return f"{base}.{key}"
        return None

    def _eval_literal(node: nodes.Node):
        if isinstance(node, nodes.Const):
            return node.value
        if isinstance(node, nodes.List):
            return [_eval_literal(x) for x in node.items]
        if isinstance(node, nodes.Dict):
            return { _eval_literal(k): _eval_literal(v) for k,v in zip(node.items[::2], node.items[1::2]) }
        if isinstance(node, nodes.NameConstant):
            return node.value
        # Fallback: stringified representation
        return getattr(node, "value", None)

    Visitor().visit(ast)
    return out


# --- helpers --------------------------------------------------------------

def _cast_value(kind: str, val):
    if val is None:
        return None
    try:
        if kind == "str":   return str(val)
        if kind == "int":   return int(val)
        if kind == "float": return float(val)
        if kind == "bool":
            if isinstance(val, bool): return val
            s = str(val).lower()
            if s in {"1","true","yes","y","on"}:  return True
            if s in {"0","false","no","n","off"}: return False
            return bool(val)
        if kind == "list":
            return list(val) if not isinstance(val, str) else yaml.safe_load(val)
        if kind == "dict":
            return dict(val) if not isinstance(val, str) else yaml.safe_load(val)
    except Exception:
        pass
    return val

def _to_nested(flat: dict[str, object]) -> dict:
    """'a.b': 1 형태를 {'a': {'b': 1}} 로 바꾸기"""
    root: dict = {}
    for k, v in flat.items():
        cur = root
        parts = k.split(".")
        for p in parts[:-1]:
            if p not in cur or not isinstance(cur[p], dict):
                cur[p] = {}
            cur = cur[p]
        cur[parts[-1]] = v
    return root

def _deep_merge(dst: dict, src: dict) -> dict:
    """src가 우선. dict만 재귀 병합, 나머지는 덮어씀"""
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst

def _flatten(nested: dict, prefix: str = "") -> dict[str, object]:
    out = {}
    for k, v in (nested or {}).items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out

# --- main ----------------------------------------------------------------

def read_yaml(yaml_path: str, ctx: Optional[dict[str, object]] = None) -> dict[str, object]:
    """
    YAML 파일을 읽고, 내부에 포함된 Jinja 템플릿 변수를 자동으로 채워서 최종 설정 딕셔너리로 반환합니다.

    주요 기능 요약:
    ----------------
    1. **inputs: 메타블록 파싱**
       - YAML 파일 상단의 `inputs:` 블록을 읽어 각 입력 변수의 `type`, `default` 값을 가져옵니다.
       - 이 블록은 주석이나 빈 줄이 포함되어도 안전하게 파싱됩니다.

    2. **Jinja 변수 자동 추출**
       - YAML 안에 등장하는 `{{ variable }}` 형태의 Jinja 변수명을 전부 수집합니다.
       - `|default('값')` 같은 필터가 붙은 변수의 기본값도 AST 기반으로 자동 추출합니다.

    3. **변수 스펙 구성 (full_spec)**
       - 위 두 정보를 합쳐 각 변수별로 `{ "type": ..., "default": ... }` 형태의 스펙을 만듭니다.
       - `inputs:` 블록에 정의되지 않은 변수는 기본적으로 `type=str`, `default=None`으로 처리합니다.

    4. **기본값 캐스팅**
       - 각 변수의 `type`에 맞게 `default` 값을 Python 타입으로 변환합니다.
         예: `"true"` → `True`, `"123"` → `123`, `"['a', 'b']"` → `['a', 'b']`

    5. **사용자 컨텍스트(ctx) 우선 적용**
       - 외부에서 `ctx` 딕셔너리를 인자로 넘길 수 있습니다.
       - `ctx`에 들어 있는 값은 `inputs:` 기본값보다 **우선 적용**됩니다.
       - `ctx`는 평범한 dict 형태(`{"var": 1}`)뿐 아니라 중첩된 dict나 점 표기(`{"a.b": 1}`)도 지원합니다.
       - 타입 정의가 되어 있으면 `ctx` 값도 해당 타입으로 자동 캐스팅됩니다.

    6. **렌더링 및 로드**
       - 모든 변수를 병합한 최종 값으로 Jinja 템플릿을 렌더링(render)합니다.
       - 렌더링 결과를 YAML로 다시 파싱하여 Python dict로 반환합니다.
       - 최상위 레벨이 dict가 아닐 경우 오류를 발생시킵니다.

    변수 값 우선순위:
    -----------------
    아래 순서대로 우선 적용됩니다 (위쪽이 더 우선):
      1️⃣ `ctx` 인자에서 전달된 값  
      2️⃣ `inputs:` 블록의 `default` 값  
      3️⃣ 템플릿 내부의 `| default('...')` 필터 값 (최후 fallback)

    즉, `ctx`가 있으면 그 값이 쓰이고,
    `ctx`가 없을 경우 `inputs:`의 기본값이,
    그것마저 없을 경우 Jinja의 `default('...')` 값이 사용됩니다.

    예시:
    -----
    ```yaml
    # example.yaml
    inputs:
      name:
        type: str
        default: "World"
      repeat:
        type: int
        default: 2

    message: "Hello {{ name | default('User') }}!"
    times: {{ repeat }}
    ```

    아래는 상황별 결과 예시입니다:

    cfg = read_yaml("example.yaml", ctx={"name": "Mingi"}) │ {'message': 'Hello Mingi!', 'times': 2} │
    (ctx 우선 적용)
    
    cfg = read_yaml("example.yaml")     │ {'message': 'Hello World!', 'times': 2} │
    (inputs: 기본값 적용)
    
    (inputs 블록 제거 후)               │ {'message': 'Hello User!'}  │
    (템플릿 default() 적용)


    정리하자면,
    ➤ `ctx` > `inputs:` > `| default('...')`
    순으로 값이 결정됩니다.
    """
    yaml_txt = Path(yaml_path).read_text(encoding="utf-8").lstrip("\ufeff")

    # 1) inputs / jinja 분석
    meta_inputs = parse_inputs_meta(yaml_txt)
    env = SandboxedEnvironment()
    ast = env.parse(yaml_txt)

    jinja_vars = sorted(jinja_meta.find_undeclared_variables(ast))
    jinja_defaults = extract_jinja_default_filters_ast(yaml_txt)  # dotted name 지원

    # 2) full_spec 구성 (type/default 스펙)
    full_spec: dict[str, dict[str, object]] = {}
    for var in jinja_vars:
        if var in meta_inputs:
            full_spec[var] = meta_inputs[var]
        elif var in jinja_defaults:
            full_spec[var] = {"type": "str", "default": jinja_defaults[var]}
        else:
            full_spec[var] = {"type": "str", "default": None}

    # 3) defaults (스펙 기반 캐스팅)
    defaults_flat = {k: _cast_value(v.get("type", "str"), v.get("default"))
                     for k, v in full_spec.items()}

    # jinja_defaults 중 'foo.bar' 같은 점 표기는 defaults에 없을 수 있음 → 추가
    for k, v in jinja_defaults.items():
        defaults_flat.setdefault(k, v)

    # 4) ctx 우선 적용: (a) ctx를 평탄화, (b) 가능한 경우 타입 캐스팅, (c) defaults 위에 덮기
    ctx = ctx or {}
    ctx_flat = _flatten(ctx) if any(isinstance(v, dict) for v in ctx.values()) else dict(ctx)

    # 타입 캐스팅: full_spec에 정확히 일치하는 키만 캐스팅 (점 표기는 스펙 없으면 생략)
    for k, v in list(ctx_flat.items()):
        if k in full_spec:
            ctx_flat[k] = _cast_value(full_spec[k].get("type", "str"), v)

    # 5) 렌더 변수 만들기: flat → nested, deep-merge (ctx가 최우선)
    vars_nested = _to_nested(defaults_flat)
    vars_nested = _deep_merge(vars_nested, _to_nested(ctx_flat))  # ctx wins

    template = env.from_string(yaml_txt)
    rendered = template.render(**vars_nested)

    config = yaml.safe_load(rendered)
    if not isinstance(config, dict):
        raise ValueError(f"Rendered YAML must be a dict at top level (got {type(config)})")
    return config

if __name__ == "__main__":
    # Example usage
    # io_instance = Base_io(uri="example_uri")
    # print(io_instance)
    
    example_yaml = "/mnt/CINELINGO_BACKUP/CineLingo/easy_translation/assets/example_translation_pipeline_gpt5.yaml"
    
    # spec = read_yaml(example_yaml)
    # print(spec)
    
    test = read_yaml(example_yaml, ctx={"root_path": "/tmp/test_output"})
    print(test)