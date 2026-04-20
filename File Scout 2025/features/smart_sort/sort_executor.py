import shutil
from pathlib import Path


def execute_sort_operations(operations, do_copy, generate_unique_dest_path, process_events=None):
    success = 0
    errors = []
    moved_paths = []
    row_results = []

    for operation in operations:
        src = Path(operation['source_path'])
        dest_text = operation.get('destination_path', '')
        if not dest_text:
            continue

        dest = Path(dest_text)

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            final_dest = generate_unique_dest_path(dest)

            if do_copy:
                shutil.copy2(src, final_dest)
            else:
                src.rename(final_dest)
                moved_paths.append(src)

            success += 1
            row_results.append({
                'row_index': operation['row_index'],
                'status': 'Done',
                'background': '#e6e6e6',
            })
        except Exception as e:
            errors.append((str(src), str(e)))
            row_results.append({
                'row_index': operation['row_index'],
                'status': 'Error',
                'background': '#ff9999',
            })

        if process_events and success % 10 == 0:
            process_events()

    return {
        'success_count': success,
        'errors': errors,
        'moved_paths': moved_paths,
        'row_results': row_results,
    }
