#!/usr/bin/env python3
"""Fix short/empty sections: delete empties, merge shorts into neighbors."""
import os
import re
import glob

BASE = '/Users/junchen/Desktop/小说/huanhuan/volumes'

def natural_sort_key(path):
    parts = re.split(r'(\d+)', path)
    return [int(p) if p.isdigit() else p.lower() for p in parts]

def get_section_num(filename):
    m = re.search(r'section-(\d+)\.md', filename)
    return int(m.group(1)) if m else 0

def main():
    deleted = []
    merged = []

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

            section_files = sorted(
                [f for f in os.listdir(ch_path) if f.startswith('section-') and f.endswith('.md')],
                key=natural_sort_key
            )

            # Step 1: Delete empty/placeholder files (< 100 bytes)
            to_delete = []
            for sf in section_files:
                sf_path = os.path.join(ch_path, sf)
                size = os.path.getsize(sf_path)
                if size < 100:
                    to_delete.append(sf)
                    deleted.append(os.path.join(ch_dir, sf))

            for sf in to_delete:
                os.remove(os.path.join(ch_path, sf))
                section_files.remove(sf)

            # Step 2: Merge short sections (100-2000 bytes) into previous section
            # Skip section-01 (intro/epigraph - OK to be short)
            to_merge = []
            for sf in section_files:
                if sf == 'section-01.md':
                    continue
                sf_path = os.path.join(ch_path, sf)
                size = os.path.getsize(sf_path)
                if size < 2000:
                    to_merge.append(sf)

            for sf in to_merge:
                if sf not in section_files:
                    continue
                sf_path = os.path.join(ch_path, sf)
                sec_num = get_section_num(sf)

                # Find the previous section file
                prev_sf = None
                for other in section_files:
                    other_num = get_section_num(other)
                    if other_num < sec_num and other_num > 0:
                        if prev_sf is None or get_section_num(other) > get_section_num(prev_sf):
                            prev_sf = other

                if prev_sf:
                    # Merge into previous section
                    prev_path = os.path.join(ch_path, prev_sf)

                    with open(prev_path, 'r', encoding='utf-8') as f:
                        prev_content = f.read()
                    with open(sf_path, 'r', encoding='utf-8') as f:
                        cur_content = f.read()

                    # Strip the title from current section before merging
                    cur_lines = cur_content.split('\n')
                    cur_body = '\n'.join(cur_lines[1:]).strip() if cur_lines else ''

                    if cur_body:
                        merged_content = prev_content.rstrip() + '\n\n' + cur_body + '\n'
                        with open(prev_path, 'w', encoding='utf-8') as f:
                            f.write(merged_content)

                    os.remove(sf_path)
                    section_files.remove(sf)
                    merged.append(f'{os.path.join(ch_dir, sf)} -> {prev_sf}')

            # Step 3: Renumber remaining sections sequentially
            remaining = sorted(
                [f for f in os.listdir(ch_path) if f.startswith('section-') and f.endswith('.md')],
                key=natural_sort_key
            )

            for i, sf in enumerate(remaining):
                new_name = f'section-{i+1:02d}.md'
                if sf != new_name:
                    old_path = os.path.join(ch_path, sf)
                    new_path = os.path.join(ch_path, new_name)
                    os.rename(old_path, new_path)

            # Step 4: Update index.md to reflect new sections
            index_path = os.path.join(ch_path, 'index.md')
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Get chapter title from first line
                ch_title = lines[0].strip() if lines else '# Chapter'

                # Rebuild index
                CN_NUMS = ['一','二','三','四','五','六','七','八','九','十',
                           '十一','十二','十三','十四','十五','十六','十七','十八','十九','二十']
                new_index = [ch_title + '\n']
                for i, sf in enumerate(remaining):
                    new_name = f'section-{i+1:02d}.md'
                    sf_path = os.path.join(ch_path, new_name if os.path.exists(os.path.join(ch_path, new_name)) else sf)

                    # Get section title
                    sec_title = f'第{CN_NUMS[i]}节' if i < len(CN_NUMS) else f'第{i+1}节'
                    try:
                        with open(sf_path, 'r', encoding='utf-8') as f:
                            first_line = f.readline().strip()
                        if first_line.startswith('# '):
                            sec_title = first_line[2:]
                    except:
                        pass

                    new_index.append(f'    * [{sec_title}]({new_name})\n')

                with open(index_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_index)

    print(f'Deleted empty sections: {len(deleted)}')
    for d in deleted:
        print(f'  ✗ {d}')
    print(f'\nMerged short sections: {len(merged)}')
    for m in merged:
        print(f'  → {m}')
    print(f'\nRemaining total: {sum(1 for _ in glob.glob(os.path.join(BASE, "**/section-*.md"), recursive=True))} sections')

if __name__ == '__main__':
    main()
