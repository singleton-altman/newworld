#!/usr/bin/env python3
"""Auto-generate SUMMARY.md for GitBook from the novel's directory structure."""
import os
import re
import glob

BASE = '/Users/junchen/Desktop/小说/huanhuan'
VOLUMES_DIR = os.path.join(BASE, 'volumes')

CN_NUMS = {
    '01': '一', '02': '二', '03': '三', '04': '四',
    '05': '五', '06': '六', '07': '七', '08': '八',
    '09': '九', '10': '十', '11': '十一', '12': '十二'
}

def get_first_heading(filepath):
    """Read the first # or ## heading from a markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    # Remove leading # marks
                    title = re.sub(r'^#+\s*', '', line)
                    return title
    except:
        pass
    return None

def natural_sort_key(path):
    """Sort paths with embedded numbers naturally."""
    parts = re.split(r'(\d+)', path)
    return [int(p) if p.isdigit() else p.lower() for p in parts]

def main():
    lines = []
    lines.append('# Summary\n')
    lines.append('* [首页](README.md)')
    lines.append('* [设定与大纲](设定与大纲.md)')
    lines.append('')

    volume_dirs = sorted(
        [d for d in os.listdir(VOLUMES_DIR) if os.path.isdir(os.path.join(VOLUMES_DIR, d)) and '-' in d],
        key=natural_sort_key
    )

    for vol_dir in volume_dirs:
        vol_num = vol_dir.split('-')[0]
        vol_name = vol_dir.split('-', 1)[1]
        cn_num = CN_NUMS.get(vol_num, vol_num)

        lines.append(f'## 第{cn_num}卷 · {vol_name}')
        lines.append('')

        vol_path = os.path.join(VOLUMES_DIR, vol_dir)
        chapter_dirs = sorted(
            [d for d in os.listdir(vol_path) if os.path.isdir(os.path.join(vol_path, d)) and d.startswith('chapter-')],
            key=natural_sort_key
        )

        for ch_dir in chapter_dirs:
            ch_path = os.path.join(vol_path, ch_dir)
            index_file = os.path.join(ch_path, 'index.md')

            # Get chapter title from index.md
            ch_title = get_first_heading(index_file)
            if not ch_title:
                ch_title = ch_dir.replace('-', ' ').title()

            # Relative path from project root
            rel_index = os.path.relpath(index_file, BASE)
            lines.append(f'* [{ch_title}]({rel_index})')

            # Get section files
            section_files = sorted(
                [f for f in os.listdir(ch_path) if f.startswith('section-') and f.endswith('.md')],
                key=natural_sort_key
            )

            for sec_file in section_files:
                sec_path = os.path.join(ch_path, sec_file)
                sec_title = get_first_heading(sec_path)

                if not sec_title:
                    # Use filename as fallback: section-01 -> 第一节
                    m = re.search(r'section-(\d+)', sec_file)
                    if m:
                        sec_num = int(m.group(1))
                        cn = CN_NUMS.get(f'{sec_num:02d}', str(sec_num))
                        sec_title = f'第{cn}节'
                    else:
                        sec_title = sec_file.replace('.md', '')

                rel_sec = os.path.relpath(sec_path, BASE)
                lines.append(f'    * [{sec_title}]({rel_sec})')

        lines.append('')

    # Write SUMMARY.md
    summary_path = os.path.join(BASE, 'SUMMARY.md')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    # Stats
    section_count = sum(1 for l in lines if l.strip().startswith('    * ['))
    chapter_count = sum(1 for l in lines if l.strip().startswith('* [') and '首页' not in l and '设定' not in l)
    print(f'SUMMARY.md generated: {chapter_count} chapters, {section_count} sections')
    print(f'Output: {summary_path}')

if __name__ == '__main__':
    main()
