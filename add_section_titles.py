#!/usr/bin/env python3
"""Add proper # titles to all section files that are missing them."""
import os
import re
import glob

BASE = '/Users/junchen/Desktop/小说/huanhuan/volumes'

CN_NUMS = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
           '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十']

def get_chapter_title(index_path):
    """Read chapter title from index.md."""
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# '):
                    return re.sub(r'^#+\s*', '', line)
    except:
        pass
    return None

def has_heading(content):
    """Check if content starts with a # or ## heading."""
    first_line = content.split('\n')[0].strip() if content.strip() else ''
    return first_line.startswith('#')

def get_existing_heading(content):
    """Get the existing heading text if any."""
    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            return re.sub(r'^#+\s*', '', stripped), line
    return None, None

def natural_sort_key(path):
    parts = re.split(r'(\d+)', path)
    return [int(p) if p.isdigit() else p.lower() for p in parts]

def main():
    total_fixed = 0
    total_converted = 0
    total_skipped = 0

    volume_dirs = sorted(
        [d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d)) and '-' in d],
        key=natural_sort_key
    )

    for vol_dir in volume_dirs:
        vol_path = os.path.join(BASE, vol_dir)
        chapter_dirs = sorted(
            [d for d in os.listdir(vol_path) if os.path.isdir(os.path.join(vol_path, d)) and d.startswith('chapter-')],
            key=natural_sort_key
        )

        for ch_dir in chapter_dirs:
            ch_path = os.path.join(vol_path, ch_dir)
            index_path = os.path.join(ch_path, 'index.md')
            ch_title = get_chapter_title(index_path) or ch_dir

            section_files = sorted(
                [f for f in os.listdir(ch_path) if f.startswith('section-') and f.endswith('.md')],
                key=natural_sort_key
            )

            for sec_file in section_files:
                sec_path = os.path.join(ch_path, sec_file)

                with open(sec_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if not content.strip():
                    continue

                existing_heading, heading_line = get_existing_heading(content)

                if existing_heading:
                    # Has a heading - check if it's ## and needs upgrade to #
                    if heading_line.startswith('## ') and not heading_line.startswith('### '):
                        # Upgrade ## to #
                        new_content = content.replace(heading_line, heading_line.replace('## ', '# ', 1), 1)
                        with open(sec_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        total_converted += 1
                    else:
                        total_skipped += 1
                else:
                    # No heading - need to add one
                    sec_num_match = re.search(r'section-(\d+)', sec_file)
                    sec_num = int(sec_num_match.group(1)) if sec_num_match else 1

                    if sec_num == 1:
                        # First section: usually the 历史摘录/introduction
                        if '历史摘录' in content[:200] or '【历史' in content[:200] or content.strip().startswith('>'):
                            title = '引言'
                        else:
                            title = '第一节'
                    else:
                        # Use 第X节 format
                        if sec_num - 1 <= len(CN_NUMS):
                            title = f'第{CN_NUMS[sec_num - 2]}节'
                        else:
                            title = f'第{sec_num}节'

                    # Prepend the title
                    new_content = f'# {title}\n\n{content}'
                    with open(sec_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    total_fixed += 1

    print(f'Titles added to sections without headings: {total_fixed}')
    print(f'## headings upgraded to #: {total_converted}')
    print(f'Already had # heading (skipped): {total_skipped}')
    print(f'Total processed: {total_fixed + total_converted + total_skipped}')

if __name__ == '__main__':
    main()
