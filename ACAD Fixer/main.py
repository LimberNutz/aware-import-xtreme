import argparse
import sys
import os
import logging
from app.cli import setup_parser
from app.pipeline.run_job import JobManager

def main():
    parser = setup_parser()
    args = parser.parse_args()

    # Launch GUI if requested
    if args.gui:
        from app.gui import main as gui_main
        gui_main()
        return

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Initialize Logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )

    manager = JobManager(args)

    if args.command == 'run':
        manager.run()
    elif args.command == 'parse':
        manager.parse_only()
    elif args.command == 'validate':
        manager.validate_only()
    elif args.command == 'probe-dxf':
        manager.probe_dxf(args.file)
    elif args.command == 'probe-pdf':
        manager.probe_pdf(args.file)
    elif args.command == 'batch':
        manager.batch_run()

if __name__ == "__main__":
    main()
