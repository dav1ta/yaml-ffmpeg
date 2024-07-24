import argparse
from yaml_video import parse_yaml, tokenize_yaml, process_tokens

def main():
    parser = argparse.ArgumentParser(description='Process a YAML file to render video.')
    parser.add_argument('file', metavar='F', type=str, help='a YAML file to process')
    args = parser.parse_args()

    yaml_data = parse_yaml(args.file)
    renderer = yaml_data.get("renderer", "x264")
    output = yaml_data["output"]
    tokens = tokenize_yaml(yaml_data)
    print(tokens)
    process_tokens(tokens, renderer, output)


if __name__ == "__main__":
    main()
