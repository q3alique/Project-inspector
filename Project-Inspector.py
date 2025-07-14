import argparse
import os
from collections import defaultdict
from colorama import init, Fore, Style
from termcolor import cprint

init()

CHATGPT_WORD_LIMIT = 3000
MAX_SINGLE_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
SPLIT_FOLDER_NAME = "splits"

STACK_PRESETS = {
    'java': {
        'extensions': ['java', 'xml', 'properties'],
        'include_folders': ['src'],
        'exclude': ['target', '.git', '.idea', 'bin', 'out', 'build', 'lib']
    },
    'python': {
        'extensions': ['py'],
        'include_folders': ['.', 'app'],
        'exclude': ['__pycache__', '.venv', '.git', 'build', 'dist']
    },
    'cs': {
        'extensions': ['cs', 'config', 'csproj'],
        'include_folders': ['src', 'app'],
        'exclude': ['bin', 'obj', '.vs', '.git']
    },
    'dotnet': {
        'extensions': ['cs', 'config', 'csproj'],
        'include_folders': ['src', 'app'],
        'exclude': ['bin', 'obj', '.vs', '.git']
    },
    'cpp': {
        'extensions': ['cpp', 'c', 'h', 'hpp'],
        'include_folders': ['src', 'include'],
        'exclude': ['build', 'bin', '.git']
    },
    'c': {
        'extensions': ['c', 'h'],
        'include_folders': ['src', 'include'],
        'exclude': ['build', 'bin', '.git']
    },
    'rust': {
        'extensions': ['rs', 'toml'],
        'include_folders': ['src'],
        'exclude': ['target', '.git']
    },
    'js': {
        'extensions': ['js', 'json', 'ts'],
        'include_folders': ['src', 'app'],
        'exclude': ['node_modules', 'dist', '.git']
    },
    'fullstack': {
        'extensions': [
            # Backend
            'py', 'java', 'cs', 'c', 'cpp', 'go', 'rs', 'php', 'rb',
            # Frontend
            'js', 'ts', 'jsx', 'tsx', 'html', 'htm', 'css', 'scss', 'sass',
            # Config / Infra / DevOps
            'json', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'env', 'xml',
            'tf', 'tfvars', 'sh', 'bat', 'ps1',
            # Docs / Data / Misc
            'md', 'txt', 'csv', 'tsv', 'sql'
        ],
        'include_folders': ['src', 'app', '.', 'frontend', 'backend', 'infra', 'terraform', 'pipelines'],
        'exclude': [
            'node_modules', 'dist', 'build', 'bin', 'obj', '__pycache__', '.venv',
            '.git', '.idea', '.vscode', '.DS_Store', 'coverage', '.pytest_cache', '.mypy_cache',
            '.next', '.parcel-cache', '.turbo', '.cache', '.nuxt', '.angular', 'target'
        ]
    }
}


def print_custom_help(stack=None):
    print(Fore.BLUE + Style.BRIGHT + "\n🟦 Project Crawler & Analyzer CLI")
    print(Fore.WHITE + Style.NORMAL + "Version: " + Fore.CYAN + "2.0" + Fore.WHITE + " | Author: " + Fore.CYAN + "q3alique")
    print(Fore.WHITE + "Description: " + "Recursively analyzes the structure and contents of a given project folder.")
    print("             Filters relevant files by tech stack, builds a tree, and saves stats and contents.\n")

    print(Fore.WHITE + Style.BRIGHT + "Usage:")
    print("  python script.py --path <project_root> [--stack <tech_stack>] [--include <items>] [--exclude <items>] --output <file>\n")

    print(Fore.WHITE + "🔹 Required Arguments:")
    print(f"  {Fore.CYAN}--path{Style.RESET_ALL:<21} Root folder to start crawling.")
    print(f"  {Fore.CYAN + Style.BRIGHT}--output{Style.RESET_ALL:<19} Output .txt file to save the results.\n")

    print(Fore.WHITE + "🔹 Optional Arguments:")
    print(f"  {Fore.CYAN}--stack{Style.RESET_ALL:<20} Technology stack: java, python, cs, cpp, rust, js, dotnet, c")
    print(f"  {Fore.CYAN}--include{Style.RESET_ALL:<18} Comma-separated list of file extensions, specific files, or folders to include.")
    print(f"  {Fore.CYAN}--exclude{Style.RESET_ALL:<18} Comma-separated list of folder or file names to exclude.\n")
    print(f"  {Fore.CYAN}-h, --help{Style.RESET_ALL:<17} Show this help message and exit.")
    print(f"  {Fore.CYAN}-h, --help <tech_stack>{Style.RESET_ALL:<2} Show detailed information about the <tech_stack>.\n")

    print(Fore.GREEN + "\n🟩 Examples:")
    print("  python script.py --path ./my-java-project --stack java --output report.txt")
    print("  python script.py --path ./my-py-project --stack python --include yaml,txt --output result.txt")
    print("  python script.py --path ./my-js-project --include package.json,src --output report.txt")
    print("  python script.py --path ./my-cpp-code --include hpp --exclude .git,build --output out.txt\n")

    if stack and stack in STACK_PRESETS:
        config = STACK_PRESETS[stack]
        print(Fore.YELLOW + f"\n🟨 Stack Details for: {stack}:")
        print(f"  - Extensions: ." + ", .".join(config['extensions']))
        print("  - Include folders:", ", ".join(config['include_folders']))
        print("  - Exclude folders:", ", ".join(config['exclude']))


def parse_arguments():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--path')
    parser.add_argument('--output')
    parser.add_argument('--stack', choices=STACK_PRESETS.keys())
    parser.add_argument('--include')
    parser.add_argument('--exclude')
    parser.add_argument('-h', '--help', nargs='?', const=True)
    args = parser.parse_args()

    if args.help is True:
        print_custom_help()
        exit(0)
    elif isinstance(args.help, str) and args.help in STACK_PRESETS:
        print_custom_help(stack=args.help)
        exit(0)

    if not args.path or not args.output:
        print_custom_help()
        exit(1)

    return args


def should_exclude(path, exclude_list):
    for ex in exclude_list:
        if ex in path.split(os.sep):
            return True
    return False


def count_words(text):
    return len(text.split())


def build_structure_map(base_path, file_to_part, exclude_list, mini_toc_lines=None):
    lines = []
    lines.append("[Project Structure with File Mapping]\n")
    lines.append(f"{os.path.basename(base_path)}/")

    def walk(current_path, prefix=''):
        try:
            entries = sorted(os.listdir(current_path))
        except Exception:
            return

        entries = [e for e in entries if not should_exclude(os.path.join(current_path, e), exclude_list)]
        for index, entry in enumerate(entries):
            full_path = os.path.join(current_path, entry)
            rel_path = os.path.relpath(full_path, base_path)
            connector = '└── ' if index == len(entries) - 1 else '├── '
            line = f"{prefix}{connector}{entry}"

            if os.path.isfile(full_path) and rel_path in file_to_part:
                part = file_to_part[rel_path]
                line += f"    → Part {part}"
                if mini_toc_lines is not None:
                    mini_toc_lines.append(f"  • {rel_path} → Part {part}")
            lines.append(line)

            if os.path.isdir(full_path):
                extension = '    ' if index == len(entries) - 1 else '│   '
                walk(full_path, prefix + extension)

    walk(base_path)
    lines.append("\n(End of structure. Parts follow below.)\n")
    return "\n".join(lines)


def split_large_output(full_output, base_path, output_file, file_to_part, part_files):
    split_dir = os.path.join(base_path, SPLIT_FOLDER_NAME)
    os.makedirs(split_dir, exist_ok=True)

    encoded = full_output.encode('utf-8')
    max_size = MAX_SINGLE_FILE_SIZE
    total_parts = (len(encoded) // max_size) + 1

    mini_toc_lines = ["[Mini Table of Contents: File → Part]"]
    structure_header = build_structure_map(base_path, file_to_part, [], mini_toc_lines)

    byte_index = 0
    for i in range(total_parts):
        chunk = encoded[byte_index:byte_index + max_size]
        part_path = os.path.join(split_dir, f"{os.path.splitext(output_file)[0]}_part_{i + 1:02}.txt")
        with open(part_path, 'w', encoding='utf-8') as f:
            f.write(f"[Split File {i + 1} of {total_parts}]\n")
            f.write("Please wait until all parts are uploaded before analyzing.\n\n")
            if i == 0:
                f.write("\n".join(mini_toc_lines) + "\n\n")
                f.write(structure_header + "\n" + "=" * 80 + "\n\n")
            f.write(chunk.decode('utf-8', errors='ignore'))

        part_files.append(part_path)
        byte_index += max_size

    cprint(f"\n[!] Output exceeded 100MB and was split into {total_parts} parts in '{split_dir}'", "yellow", attrs=["bold"])


def crawl_and_collect(base_path, extensions, output_file, exclude_list, include_files, include_dirs):
    matched_files = 0
    extension_counts = defaultdict(int)
    include_matches = set()
    full_output = ""
    file_to_part = {}
    part_files = []

    file_contents = []

    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d), exclude_list)]

        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_path)

            if should_exclude(rel_path, exclude_list):
                continue

            ext = os.path.splitext(file)[1][1:]
            in_included_dir = any(inc in os.path.relpath(root, base_path) for inc in include_dirs)
            file_match = file in include_files or ext in extensions or in_included_dir

            if file_match and os.path.getsize(file_path) > 0:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    word_count = count_words(content)
                    file_size = os.path.getsize(file_path)
                    long_warning = word_count > CHATGPT_WORD_LIMIT

                    cprint(f"\n[+] Found file: {rel_path}", "green")
                    cprint(f"    - Size: {file_size} bytes", "cyan")
                    cprint(f"    - Word count: {word_count}", "cyan")
                    if long_warning:
                        cprint("    - [Note]: File is too long for direct prompt input.", "yellow")
                        cprint("      You can still upload it as a file and it will be processed correctly.", "green")

                    entry = f"[FILE]: {rel_path}\n[SIZE]: {file_size} bytes\n[WORDS]: {word_count}\n"
                    if long_warning:
                        entry += "[NOTE]: Too long for direct prompt input.\n"
                        entry += "[OK]: Uploading as a file is fully supported and preferred.\n"
                    entry += f"[PART REF]: Will appear in Part ? (assigned below)\n"
                    entry += content + "\n\n" + "=" * 80 + "\n\n"

                    file_contents.append((rel_path, entry))
                    matched_files += 1
                    extension_counts[ext] += 1
                    if file in include_files:
                        include_matches.add(file)

                except Exception as e:
                    cprint(f"[!] Failed to read file: {rel_path} | Error: {e}", "red")

    current_size = 0
    part_index = 1
    new_output = []
    for rel_path, entry in file_contents:
        entry_size = len(entry.encode('utf-8'))
        if current_size + entry_size > MAX_SINGLE_FILE_SIZE:
            part_index += 1
            current_size = 0
        file_to_part[rel_path] = part_index
        current_size += entry_size
        # Replace the PART REF tag with actual part number
        entry = entry.replace("Part ? (assigned below)", f"Part {part_index}")
        new_output.append(entry)

    full_output = "".join(new_output)

    if len(full_output.encode('utf-8')) <= MAX_SINGLE_FILE_SIZE:
        mini_toc_lines = ["[Mini Table of Contents: File → Part]"]
        structure = build_structure_map(base_path, file_to_part, exclude_list, mini_toc_lines)
        with open(output_file, 'w', encoding='utf-8') as out:
            out.write("\n".join(mini_toc_lines) + "\n\n")
            out.write(structure + "\n" + "=" * 80 + "\n\n")
            out.write(full_output)
        print(Fore.YELLOW + f"\n✅ Output saved to: {os.path.abspath(output_file)}")
    else:
        split_large_output(full_output, base_path, output_file, file_to_part, part_files)

    cprint(f"\nDone. Total files processed: {matched_files}", "yellow", attrs=["bold"])

    if extension_counts:
        print(Fore.MAGENTA + "\n🟪 Processed by Extension:")
        for ext, count in extension_counts.items():
            print(f"  .{ext}: {count} file(s)")

    if include_files:
        print(Fore.MAGENTA + "\n🟪 Included Files Summary:")
        unmatched = [f for f in include_files if f not in include_matches]
        for f in include_matches:
            print(f"  ✔ Matched: {f}")
        for f in unmatched:
            print(f"  ✖ No Match: {f}")
        if not include_matches:
            print("  ⚠ No provided --include file matched any file in the project.")


def main():
    args = parse_arguments()
    base_path = args.path
    output_file = args.output
    extensions = []
    exclude_list = []
    include_files = []
    include_dirs = []

    if args.stack:
        config = STACK_PRESETS[args.stack]
        extensions = config['extensions']
        exclude_list = config['exclude']

    if args.include:
        for item in args.include.split(','):
            item = item.strip()
            if not item:
                continue
            if item.startswith('.'):
                extensions.append(item[1:])
            elif '.' in item:
                include_files.append(item)
            else:
                include_dirs.append(item)

    if args.exclude:
        exclude_list.extend([ex.strip() for ex in args.exclude.split(',') if ex.strip()])

    crawl_and_collect(base_path, extensions, output_file, exclude_list, include_files, include_dirs)


if __name__ == '__main__':
    main()
