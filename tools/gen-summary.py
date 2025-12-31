from pathlib import Path
import os

class BookChapter:
    def __init__(self, root: Path):
        self.sub_chapters : list[BookChapter] = []
        self.parent : str = root.parent
        self.name : str = root.name
        self.name.removesuffix('.md')
        # replace blank space with %20 for URL encoding
        self.path : str = root.as_posix().replace(' ', '%20')
        if root.is_dir():
            for path in root.iterdir():
                # if path is a file and not a markdown file, skip it
                # if patah is a directory but no markdown file inside, skip it
                if path.is_file():
                    if path.suffix != '.md':
                        continue
                    else:
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
    # no indent for level 0 and level 1
    indent = '  ' * (level - 1) if level > 1 else ''
    for chapter in root_chapter.sub_chapters:
        if len(chapter.sub_chapters) == 0 and chapter.path.endswith('.md'):
            print(f"{indent}- [{chapter.name.removesuffix('.md')}](./{chapter.path})")
        else:
            if level == 0:
                print(f"\n# {chapter.name.replace("_", " ")}\n")
            else:
                print(f"{indent}- [{chapter.name.replace("_", " ")}]()")
            generate_leveled_summary(level + 1, chapter)

if __name__ == "__main__":
    a = BookChapter(Path('docs'))
    print(f"# Summary\n")
    generate_leveled_summary(0, a)

