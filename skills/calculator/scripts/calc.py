#!/usr/bin/env python3
"""Simple calculator that evaluates mathematical expressions."""
import argparse


def main():
    parser = argparse.ArgumentParser(description="Evaluate a mathematical expression")
    parser.add_argument("--expression", "-e", required=True, help="Expression to evaluate")
    args = parser.parse_args()
    result = eval(args.expression)
    print(result)


if __name__ == "__main__":
    main()
