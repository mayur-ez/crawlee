from pathlib import Path


ASSETS_DIR = Path("assets")
DEFAULT_DOMAIN_FILE = ASSETS_DIR / "domain_list.txt"


def get_seed_urls() -> list[str]:
    """
    Returns a list of URLs selected by the user.
    """

    while True:
        print("\n========== BookCrawler ==========")
        print("1. Enter URLs manually")
        print("2. Read URLs from custom file")
        print("3. Read URLs from assets/domain_list.txt")
        print("0. Exit")

        choice = input("\nSelect Option : ").strip()

        if choice == "1":
            urls = input("\nEnter URLs (comma separated): ").strip()

            url_list = []

            for url in urls.split(","):
                url = url.strip()

                if url:
                    url_list.append(url)

            return url_list

        elif choice == "2":

            file_path = input("\nEnter file path : ").strip()

            return read_urls(file_path)

        elif choice == "3":

            return read_urls(DEFAULT_DOMAIN_FILE)

        elif choice == "0":
            raise SystemExit("Good Bye!")

        else:
            print("\nInvalid Option\n")


def read_urls(file_path) -> list[str]:

    path = Path(file_path)

    if not path.exists():
        print("\nFile Not Found\n")
        return []

    with open(path, "r") as f:

        urls = []

        for line in f:
            line = line.strip()

            if line:
                urls.append(line)

    return urls

get_seed_urls()