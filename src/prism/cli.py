from prism import config


def main() -> None:
    config.load_env()
    print("Hello from prism!")


if __name__ == "__main__":
    main()
