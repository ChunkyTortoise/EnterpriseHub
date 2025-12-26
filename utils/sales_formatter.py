import argparse
import re
import sys


def format_for_upwork(text: str) -> str:
    """Removes markdown headers and bolding for raw text submission."""
    # Remove markdown headers
    text = re.sub(r"^#+ .*$", "", text, flags=re.MULTILINE)
    # Remove bolding
    text = text.replace("**", "")
    # Remove blockquotes
    text = re.sub(r"^> ", "", text, flags=re.MULTILINE)
    return text.strip()


def format_for_linkedin(text: str) -> str:
    """Adds branding emojis and ensures scannability."""
    # Add emojis to headers
    text = text.replace("# ", "💎 ")
    text = text.replace("## ", "🚀 ")
    # Ensure double spacing for mobile scannability
    text = text.replace("\n", "\n\n")
    return text.strip()


def main():
    parser = argparse.ArgumentParser(description="Format sales assets for different platforms.")
    parser.add_argument("file", help="Path to the markdown asset file.")
    parser.add_argument("--platform", choices=["upwork", "linkedin", "fiverr"], required=True)

    args = parser.parse_args()

    try:
        with open(args.file, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File {args.file} not found.")
        sys.exit(1)

    if args.platform == "upwork":
        print(format_for_upwork(content))
    elif args.platform == "linkedin":
        print(format_for_linkedin(content))
    else:
        # Default for Fiverr/Generic
        print(content)


if __name__ == "__main__":
    main()
