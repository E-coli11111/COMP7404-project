import argparse

def create_parser():
    parser = argparse.ArgumentParser(description="ChatCot CLI")
    parser.add_argument(
        "-q", "--query", 
        type=str, 
        required=True, 
        help="The query to process using ChatCot."
    )
    parser.add_argument(
        "--web", 
        action="store_true", 
        help="Run the ChatCot web interface."
    )
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.web:
        from src.web import launch
        launch()
    else:
        from src.chatcot import chatcot
        response = chatcot(args.query)
        
        for step in response:
            if step['type'] == 'final':
                print("Final Response:", step['content'])
            else:
                print(f"Step {step['step']}: {step['content']}")
        
if __name__ == "__main__":
    main()