from src.json_support import parse_json_lines_file


def main():
    for tme in parse_json_lines_file("tests/jsons/20220902.json"):
        print(tme)


if __name__ == "__main__":
    main()
