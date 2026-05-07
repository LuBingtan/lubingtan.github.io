from pathlib import Path

META_FILES = {'index.md', 'log.md'}

def _read_title(filepath: Path) -> str | None:
    """Read the first H1 heading (# ) from a file, outside code fences."""
    try:
        with open(filepath) as f:
            in_code_fence = False
            for line in f:
                stripped = line.strip()
                if stripped.startswith('```') or stripped.startswith('~~~'):
                    in_code_fence = not in_code_fence
                    continue
                if in_code_fence:
                    continue
                if stripped.startswith('# ') and not stripped.startswith('## '):
                    return stripped[2:].strip()
    except Exception:
        pass
    return None

class BookChapter:
    def __init__(self, root: Path):
        self.sub_chapters : list[BookChapter] = []
        self.parent : str = root.parent
        self.name : str = root.name.removesuffix('.md')
        self.path : str = root.as_posix().replace(' ', '%20')

        if root.is_file() and root.suffix == '.md':
            title = _read_title(root)
            if title:
                self.name = title

        if root.is_dir():
            self.name = self.name.replace("_", " ")
            for path in root.iterdir():
                if path.is_file():
                    if path.suffix != '.md':
                        continue
                    if path.name in META_FILES:
                        continue
                    sub_chapter = BookChapter(path)
                    self.sub_chapters.append(sub_chapter)
                else:
                    has_md = False
                    for _ in path.rglob('*.md'):
                        has_md = True
                        break
                    if has_md:
                        sub_chapter = BookChapter(path)
                        self.sub_chapters.append(sub_chapter)
        self.sub_chapters.sort(key=lambda x: x.name)

def generate_leveled_summary(level: int, root_chapter: BookChapter) -> None:
    indent = '  ' * (level - 1) if level > 1 else ''
    for chapter in root_chapter.sub_chapters:
        if len(chapter.sub_chapters) == 0 and chapter.path.endswith('.md'):
            print(f"{indent}- [{chapter.name}](./{chapter.path})")
        else:
            if level == 0:
                print(f"\n# {chapter.name}\n")
            else:
                print(f"{indent}- [{chapter.name}]()")
            generate_leveled_summary(level + 1, chapter)

if __name__ == "__main__":
    a = BookChapter(Path('docs'))
    print(f"# Summary\n")
    generate_leveled_summary(0, a)
