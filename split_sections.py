#!/usr/bin/env python3
"""Split each chapter into individual section files."""
import os
import re
import glob
import shutil

BASE = '/Users/junchen/Desktop/小说/huanhuan/volumes'
CN_NUMS = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']

def get_chapter_title(line):
    """Extract chapter title from # heading line."""
    m = re.match(r'^#\s+第\S+章\s+(.+)', line)
    if m:
        return line.strip()
    return None

def split_by_section_markers(content, chapter_title):
    """Split content by ## or ### section markers (一, 二, 三...)."""
    lines = content.split('\n')
    sections = []
    current_section = []
    current_title = None
    
    # Pattern to match section headings like ## 一, ### 二, etc.
    section_pattern = re.compile(r'^#{2,3}\s+([一二三四五六七八九十]+)\s*$')
    
    for line in lines:
        m = section_pattern.match(line)
        if m:
            # Save previous section
            if current_title is not None or current_section:
                sections.append((current_title, '\n'.join(current_section).strip()))
            current_title = m.group(1)
            current_section = []
        else:
            current_section.append(line)
    
    # Save last section
    if current_title is not None or current_section:
        sections.append((current_title, '\n'.join(current_section).strip()))
    
    return sections

def split_by_paragraphs(content, num_sections=5):
    """Split content without markers into roughly equal sections by paragraphs."""
    lines = content.split('\n')
    
    # Find paragraph break positions (lines followed by blank line)
    break_positions = []
    for i in range(len(lines) - 1):
        if lines[i].strip() == '' and i > 0:
            break_positions.append(i)
    
    if len(break_positions) < num_sections:
        num_sections = max(1, len(break_positions))
    
    # Split into roughly equal parts
    chunk_size = max(1, len(break_positions) // num_sections)
    sections = []
    start = 0
    
    for i in range(num_sections):
        if i == num_sections - 1:
            end = len(lines)
        else:
            bp_idx = min((i + 1) * chunk_size, len(break_positions)) - 1
            if bp_idx < 0:
                bp_idx = 0
            end = break_positions[bp_idx] + 1
        
        section_text = '\n'.join(lines[start:end]).strip()
        if section_text:
            sections.append((None, section_text))
        start = end
    
    return sections

def process_chapter(chapter_path, volume_dir, chapter_num):
    """Process a single chapter file and split it into section files."""
    with open(chapter_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    chapter_title = None
    body_start = 0
    
    # Extract chapter title from first line
    if lines and lines[0].startswith('# '):
        chapter_title = lines[0].strip()
        body_start = 1
    
    body = '\n'.join(lines[body_start:])
    
    # Detect section markers
    section_markers = re.findall(r'^#{2,3}\s+[一二三四五六七八九十]+\s*$', body, re.MULTILINE)
    
    if section_markers:
        # Has section markers - split by them
        sections = split_by_section_markers(body, chapter_title)
    else:
        # No markers - detect natural breaks
        # Look for --- dividers, *** dividers, or scene breaks
        divider_positions = [m.start() for m in re.finditer(r'\n---\n|\n\*\*\*\n|\n___\n', body)]
        
        if len(divider_positions) >= 2:
            # Has dividers, but need to skip the first --- (usually after the title/历史摘录)
            parts = re.split(r'\n---\n', body)
            # Skip empty parts and the 历史摘录 header if it's just metadata
            real_parts = [p.strip() for p in parts if p.strip() and not p.strip().startswith('> **历史摘录')]
            
            if len(real_parts) >= 2:
                sections = [(None, p) for p in real_parts]
            else:
                sections = split_by_paragraphs(body, 5)
        else:
            # Split into ~5 equal sections
            sections = split_by_paragraphs(body, 5)
    
    # Create chapter directory
    ch_dir_name = f'chapter-{chapter_num:02d}'
    ch_dir = os.path.join(volume_dir, ch_dir_name)
    os.makedirs(ch_dir, exist_ok=True)
    
    # Write section files
    for i, (sec_title, sec_content) in enumerate(sections):
        sec_num = i + 1
        sec_file = os.path.join(ch_dir, f'section-{sec_num:02d}.md')
        
        with open(sec_file, 'w', encoding='utf-8') as f:
            if sec_title:
                f.write(f'## {sec_title}\n\n')
            f.write(sec_content)
            f.write('\n')
    
    # Write chapter index
    index_file = os.path.join(ch_dir, 'index.md')
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(f'{chapter_title}\n\n')
        f.write(f'**卷**: {os.path.basename(volume_dir)}\n\n')
        f.write(f'**章节数**: {len(sections)}\n\n')
        f.write('**目录**:\n\n')
        for i, (sec_title, _) in enumerate(sections):
            sec_num = i + 1
            label = sec_title if sec_title else f'第{CN_NUMS[i] if i < len(CN_NUMS) else sec_num}节'
            f.write(f'- [{label}](section-{sec_num:02d}.md)\n')
    
    return len(sections)

def main():
    total_sections = 0
    total_chapters = 0
    
    volume_dirs = sorted(glob.glob(os.path.join(BASE, '*-*')))
    
    for vol_dir in volume_dirs:
        vol_name = os.path.basename(vol_dir)
        print(f'\n=== {vol_name} ===')
        
        chapter_files = sorted(glob.glob(os.path.join(vol_dir, 'chapter-*.md')))
        
        for ch_file in chapter_files:
            # Extract chapter number
            m = re.search(r'chapter-(\d+)\.md', ch_file)
            if not m:
                continue
            ch_num = int(m.group(1))
            
            # Move original file to backup first
            backup_file = ch_file + '.bak'
            shutil.copy2(ch_file, backup_file)
            
            # Process and split
            num_sections = process_chapter(ch_file, vol_dir, ch_num)
            
            # Remove original chapter file
            os.remove(ch_file)
            os.remove(backup_file)
            
            total_sections += num_sections
            total_chapters += 1
            print(f'  chapter-{ch_num:02d}: {num_sections} sections')
    
    print(f'\n{"="*50}')
    print(f'Total: {total_chapters} chapters split into {total_sections} section files')

if __name__ == '__main__':
    main()
