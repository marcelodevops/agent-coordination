"""Run with python3 -m reviewer; all paths are explicit coordinator inputs."""
import argparse
import json
import sys
from pathlib import Path

from .core import prepare, evaluate, apply_decision


def load(path):
    return json.loads(Path(path).read_text())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    packet = sub.add_parser('prepare')
    packet.add_argument('--repo', required=True)
    packet.add_argument('--task', required=True)
    packet.add_argument('--assignment', required=True)
    packet.add_argument('--evidence', action='append', required=True)
    packet.add_argument('--output', required=True, help='New file outside reviewed repository')
    check = sub.add_parser('evaluate')
    for name in ('repo', 'packet', 'report', 'policy', 'verification'):
        check.add_argument('--' + name, required=True)
    check.add_argument('--apply-task', help='Explicitly authorize this one task; omitted means no writes')
    check.add_argument('--plan')
    check.add_argument('--receipt')
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            value = prepare(args.repo, args.task, args.assignment, args.evidence)
            output = Path(args.output)
            if output.resolve().is_relative_to(Path(args.repo).resolve()):
                raise ValueError('Packet must live outside reviewed repository')
            with output.open('x') as stream:
                json.dump(value, stream, indent=2)
                stream.write('\n')
        else:
            packet, report, policy, verification = [load(p) for p in (args.packet, args.report, args.policy, args.verification)]
            if args.apply_task:
                if not args.plan or not args.receipt:
                    raise ValueError('--apply-task requires --plan and --receipt')
                value = apply_decision(args.repo, packet, report, policy, verification, args.plan, args.apply_task, args.receipt)
            else:
                if args.plan or args.receipt:
                    raise ValueError('--plan/--receipt require --apply-task')
                value = evaluate(args.repo, packet, report, policy, verification)
            print(json.dumps(value, indent=2))
            return 0 if value.get('eligible') else 1
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
