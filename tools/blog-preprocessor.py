#!/usr/bin/env python3

import json
import sys
import os

def set_default_cotent(chapter : dict) -> None:
    if chapter["path"] is None:
        chapter["path"] = chapter["name"].lower().replace(' ', '_') + '.md'
        chapter["content"] = f"# {chapter['name']}\n"
    if "sub_items" in chapter:
        for item in chapter["sub_items"]:
            if "Chapter" in item:
                set_default_cotent(item["Chapter"])

def md_files_with_date(root: str) -> list[str]:
    md_files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith('.md'):
                full_path = os.path.join(dirpath, filename)
                added_date = get_git_added_date(full_path)
                if added_date not in md_files:
                    md_files[added_date] = []
                md_files[added_date].append(full_path)
    return md_files

def get_git_added_date(file_path: str) -> str:
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'log', '--diff-filter=A', '--follow', '--format=%ad', '--date=short', '--', file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        date = result.stdout
        return date
    except subprocess.CalledProcessError:
        return "Unknown Date"

if __name__ == '__main__':
    if len(sys.argv) > 1: # we check if we received any argument
        if sys.argv[1] == "supports": 
            # then we are good to return an exit status code of 0, since the other argument will just be the renderer's name
            sys.exit(0)

    # load both the context and the book representations from stdin
    context, book = json.load(sys.stdin)
    # add set path to the chapter's name for chapters that has a non-existing path
    for item in book['items']:
        if 'Chapter' in item:
            set_default_cotent(item['Chapter'])
    # and now, we can just modify the content of the first chapter
    files_group_by_date = md_files_with_date('src/docs/')
    lines = []
    # get latest 10 dates
    for date in sorted(files_group_by_date.keys(), reverse=True)[:10]:
        lines.append(f"## {date}\n")
        for file in sorted(files_group_by_date[date]):
            relative_path = file.replace(' ', '%20')
            name = os.path.splitext(os.path.basename(file))[0]
            lines.append(f"> #### [{name}](./{relative_path})")
        lines.append("")  # add an empty line after each date group
    # with open('bin/debug_files.md', 'w', encoding='utf-8') as f:
    #     f.write("\n".join(all_files))
    book['items'].insert(0, {
        "Chapter": {
            "name": "New Post",
            "content": "\n".join(lines),
            "sub_items": [],
            "path": "new_post.md",
            "source_path": None,
            "parent_names": []
        }
    })
    with open('bin/debug.json', 'w', encoding='utf-8') as f:
        json.dump(book, f, indent=4, ensure_ascii=False)
    # book['items'][0]['Chapter']['content'] = '# Haha'
    # we are done with the book's modification, we can just print it to stdout, 
    print(json.dumps(book))
