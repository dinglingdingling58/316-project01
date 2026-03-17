import re
from typing import Dict, Any, List

from utils.util_config import (
    MD_HEADING_PATTERNS,
    SINGLE_LETTER_VARS,
    PY_DEF_PATTERN,
    PY_CLASS_PATTERN,
    PY_VAR_PATTERN
)


def parse_markdown(content: str) -> Dict[str, Any]:
    result = {
        'headings': {1: 0, 2: 0, 3: 0, 4: 0},
        'heading_list': {1: [], 2: [], 3: [], 4: []},
        'code_blocks': 0,
        'links': 0,
        'tables': 0,
        'paragraphs': 0,
        'total_lines': len(content.splitlines())
    }

    lines = content.splitlines()
    in_code_block = False
    in_table = False
    paragraph_buffer = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('```'):
            in_code_block = not in_code_block
            if in_code_block:
                result['code_blocks'] += 1
            continue

        if in_code_block:
            continue

        if re.match(r'^\|.*\|$', stripped):
            content_only = stripped.replace('|', '').strip()
            if not re.match(r'^[\-\:\=\+]+$', content_only):
                if not in_table:
                    result['tables'] += 1
                    in_table = True
            continue
        else:
            in_table = False

        for level in range(1, 5):
            pattern = MD_HEADING_PATTERNS[level]
            match = re.match(pattern, stripped)
            if match:
                result['headings'][level] += 1
                result['heading_list'][level].append(match.group(1))
                if paragraph_buffer:
                    result['paragraphs'] += 1
                    paragraph_buffer = []
                break
        else:
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            links_found = re.findall(link_pattern, stripped)
            result['links'] += len(links_found)

            if stripped and not stripped.startswith('#'):
                paragraph_buffer.append(stripped)
            elif not stripped and paragraph_buffer:
                result['paragraphs'] += 1
                paragraph_buffer = []

    if paragraph_buffer:
        result['paragraphs'] += 1

    return result


def parse_python(content: str) -> Dict[str, Any]:
    result = {
        'function_count': 0,
        'class_count': 0,
        'single_letter_vars': [],
        'questionable_private_vars': [],
        'total_lines': len(content.splitlines())
    }

    lines = content.splitlines()
    in_string = False
    string_char = ''

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('#'):
            continue

        def_matches = re.findall(PY_DEF_PATTERN, line)
        result['function_count'] += len(def_matches)

        class_matches = re.findall(PY_CLASS_PATTERN, line)
        result['class_count'] += len(class_matches)

        var_matches = re.findall(PY_VAR_PATTERN, line)
        for var in var_matches:
            if len(var) == 1 and var.lower() in SINGLE_LETTER_VARS:
                result['single_letter_vars'].append(var)
            if var.startswith('_') and not (var.startswith('__') and var.endswith('__')):
                if not var.startswith('__'):
                    result['questionable_private_vars'].append(var)

    result['single_letter_count'] = len(set(result['single_letter_vars']))
    result['questionable_private_count'] = len(set(result['questionable_private_vars']))

    return result


def parse_text(content: str) -> Dict[str, Any]:
    lines = content.splitlines()
    non_empty_lines = [l for l in lines if l.strip()]
    paragraphs = 0
    para_buffer = []

    for line in lines:
        if line.strip():
            para_buffer.append(line)
        elif para_buffer:
            paragraphs += 1
            para_buffer = []

    if para_buffer:
        paragraphs += 1

    return {
        'total_lines': len(lines),
        'non_empty_lines': len(non_empty_lines),
        'paragraphs': paragraphs,
        'word_count': len(content.split())
    }


def parse_rst(content: str) -> Dict[str, Any]:
    result = {
        'total_lines': len(content.splitlines()),
        'headings': 0,
        'code_blocks': 0,
        'links': 0
    }

    lines = content.splitlines()
    for i, line in enumerate(lines):
        if i > 0:
            prev_line = lines[i - 1].strip()
            curr_stripped = line.strip()
            if prev_line and len(set(curr_stripped)) == 1 and curr_stripped[0] in '=-~*+#^':
                if len(curr_stripped) >= len(prev_line):
                    result['headings'] += 1

        if '`' in line and '<' in line and '>' in line:
            result['links'] += 1

        if line.strip() == '::':
            result['code_blocks'] += 1

    return result


def parse_html(content: str) -> Dict[str, Any]:
    return {
        'total_lines': len(content.splitlines()),
        'links': len(re.findall(r'<a\s+[^>]*href=', content, re.IGNORECASE)),
        'tables': len(re.findall(r'<table', content, re.IGNORECASE)),
        'code_blocks': len(re.findall(r'<code|<pre', content, re.IGNORECASE)),
        'headings': len(re.findall(r'<h[1-4]', content, re.IGNORECASE))
    }


def parse_file(file_path: str, content: str, extension: str) -> Dict[str, Any]:
    parsers = {
        '.md': parse_markdown,
        '.py': parse_python,
        '.txt': parse_text,
        '.rst': parse_rst,
        '.html': parse_html
    }

    try:
        if extension in parsers:
            return parsers[extension](content)
        else:
            return {'total_lines': len(content.splitlines())}
    except Exception:
        return {'error': 'Parse failed', 'total_lines': 0}
