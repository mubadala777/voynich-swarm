"""Repeat the frozen layout benchmark at the practice rates of two example symbols."""
import argparse
import sys

import bench

if __name__ == '__main__':
    reader = argparse.ArgumentParser(add_help=False)
    reader.add_argument('--practice-rate', choices=('o', 'r'), required=True)
    options, rest = reader.parse_known_args()
    bench.BASE_RATE, seed_offset = {'o': (0.124, 20000), 'r': (0.036, 30000)}[options.practice_rate]
    bench.SEED += seed_offset
    sys.argv = [sys.argv[0], *rest]
    bench.main()
