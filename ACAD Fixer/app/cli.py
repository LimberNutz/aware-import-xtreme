import argparse

def setup_parser():
    parser = argparse.ArgumentParser(description="GG CML Title Block Update Tool")
    parser.add_argument('--gui', action='store_true', help='Launch graphical user interface')
    subparsers = parser.add_subparsers(dest='command')

    # Run command
    run_parser = subparsers.add_parser('run', help='Execute a full update job')
    run_parser.add_argument('--asset', required=False, help='Asset ID to process')
    run_parser.add_argument('--csv', required=False, help='Path to CML Import CSV')
    run_parser.add_argument('--lookup', required=False, help='Path to existing lookup file')
    run_parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without modifying files')

    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse CSV and generate lookup only')
    parse_parser.add_argument('--asset', required=True)
    parse_parser.add_argument('--csv', required=True)

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate lookup file')
    validate_parser.add_argument('--lookup', required=True)

    # Probe commands
    probe_dxf = subparsers.add_parser('probe-dxf', help='Probe DXF attributes')
    probe_dxf.add_argument('--file', required=True)

    probe_pdf = subparsers.add_parser('probe-pdf', help='Probe PDF text segments')
    probe_pdf.add_argument('--file', required=True)

    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Process all assets from CSV')
    batch_parser.add_argument('--csv', required=True, help='Path to CML Import CSV')
    batch_parser.add_argument('--exclude', required=False, default='', help='Comma-separated list of asset IDs to exclude')
    batch_parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without modifying files')

    return parser
