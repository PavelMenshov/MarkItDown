import sys
import os
import traceback
from markitdown import MarkItDown
from pdf2markdown4llm import PDF2Markdown4LLM
import ocrmypdf as OcrMyPdf

HISTORY_FILE = ".markitdown_history"
MD_FOLDER = "MD_Folder"
OCR_FOLDER = "OCR"

def load_history(history_path):
    if os.path.exists(history_path):
        with open(history_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    return set()

def progress_callback(progress):
    """Callback function to handle progress"""
    print(
        "Phase: {phase}, Page {current}/{total}, Progress: {percentage:.1f}%, Message: {message}".format(
            phase=progress.phase.value,
            current=progress.current_page,
            total=progress.total_pages,
            percentage=progress.percentage,
            message=progress.message,
        )
    )


def run_ocr_on_pdf(pdf_path, ocr_pdf_path, verbose):
    """Run OCR on the provided PDF and return the path to the OCR output file."""
    if verbose:
        print(f"Running OCR on '{pdf_path}' -> '{ocr_pdf_path}'")
    try:
        os.makedirs(os.path.dirname(ocr_pdf_path), exist_ok=True)
        OcrMyPdf.ocr(
            pdf_path,
            ocr_pdf_path,
            language="eng+chi_sim+chi_tra+nld+spa+tur",
            force_ocr=True,
            progress_bar=False,
        )
        return ocr_pdf_path
    except Exception as e:
        print(f"OCR failed for '{pdf_path}': {type(e).__name__}: {e}")
        if verbose:
            traceback.print_exc()
        return None


def save_history(history_path, processed_files):
    with open(history_path, 'w', encoding='utf-8') as f:
        for path in processed_files:
            f.write(path + '\n')

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert files in a directory to Markdown.")
    parser.add_argument("directory", help="Root directory to process")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    root_dir = args.directory
    verbose = args.verbose
    if not os.path.isdir(root_dir):
        print(f"Error: Directory not found at '{root_dir}'")
        sys.exit(1)

    history_path = os.path.join(os.path.dirname(__file__), HISTORY_FILE)
    md_folder_path = os.path.join(root_dir, MD_FOLDER)
    ocr_folder_path = os.path.join(root_dir, OCR_FOLDER)
    os.makedirs(md_folder_path, exist_ok=True)
    os.makedirs(ocr_folder_path, exist_ok=True)

    processed_files = load_history(history_path)
    new_processed = set()

    md = MarkItDown()

    def convert_pdf_with_fallback(pdf_path, verbose):
        converter = PDF2Markdown4LLM(
            remove_headers=False,
            skip_empty_tables=True,
            table_header="### Table",
            progress_callback=progress_callback,
        )
        try:
            return converter.convert(pdf_path) or ""
        except Exception as e:
            print(f"Fallback PDF conversion failed for '{pdf_path}': {type(e).__name__}: {e}")
            if verbose:
                traceback.print_exc()
            return ""

    for dirpath, dirnames, filenames in os.walk(root_dir):
        if os.path.abspath(dirpath) == os.path.abspath(md_folder_path):
            continue

        dirnames[:] = [d for d in dirnames if d not in {MD_FOLDER, OCR_FOLDER}]
        for filename in filenames:
            input_file_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(input_file_path, root_dir)
            markdown_exts = {'.md', '.markdown'}
            if (
                rel_path in processed_files
                or os.path.splitext(filename)[1].lower() in markdown_exts
                or filename == HISTORY_FILE
                or filename.lower().endswith('_ocr.pdf')
            ):
                continue
            output_dir = md_folder_path
            os.makedirs(output_dir, exist_ok=True)

            flattened_name = rel_path.replace(os.sep, '__').replace('/', '__')
            output_filename = os.path.splitext(flattened_name)[0] + '.md'
            output_file_path = os.path.join(output_dir, output_filename)

            markdown_output = ""
            conversion_error = None
            try:
                result = md.convert(input_file_path)
                markdown_output = result.markdown or result.text_content or ""
            except Exception as e:
                conversion_error = e
                print(f"Error processing '{input_file_path}': {type(e).__name__}: {e}")
                if verbose:
                    traceback.print_exc()

            fallback_used = False
            ocr_used = False
            if not markdown_output and filename.lower().endswith('.pdf'):
                if not os.path.exists(output_file_path):
                    markdown_output = convert_pdf_with_fallback(input_file_path, verbose) or ""
                    fallback_used = bool(markdown_output)
                    if fallback_used and verbose:
                        print(f"Converted '{input_file_path}' using PDF fallback to '{output_file_path}'")
                    elif verbose and not markdown_output:
                        print(f"Fallback PDF conversion did not produce output for '{input_file_path}'")
                elif verbose:
                    print(
                        f"Skipping fallback for '{input_file_path}' because '{output_file_path}' already exists."
                    )

            if not markdown_output and filename.lower().endswith('.pdf'):
                ocr_rel_dir = os.path.dirname(rel_path)
                ocr_basename = os.path.splitext(filename)[0] + '_ocr.pdf'
                ocr_output_dir = os.path.join(ocr_folder_path, ocr_rel_dir) if ocr_rel_dir else ocr_folder_path
                ocr_pdf_path = os.path.join(ocr_output_dir, ocr_basename)
                ocr_pdf_path = run_ocr_on_pdf(input_file_path, ocr_pdf_path, verbose)
                if ocr_pdf_path and os.path.exists(ocr_pdf_path):
                    ocr_used = True
                    try:
                        result = md.convert(ocr_pdf_path)
                        markdown_output = result.markdown or result.text_content or ""
                    except Exception as e:
                        print(f"Error processing OCR output '{ocr_pdf_path}': {type(e).__name__}: {e}")
                        if verbose:
                            traceback.print_exc()

                    if not markdown_output:
                        markdown_output = convert_pdf_with_fallback(ocr_pdf_path, verbose) or ""
                        fallback_used = fallback_used or bool(markdown_output)
                        if fallback_used and verbose:
                            print(
                                f"Converted OCR output '{ocr_pdf_path}' using PDF fallback to '{output_file_path}'"
                            )
                        elif verbose and not markdown_output:
                            print(
                                f"Fallback PDF conversion did not produce output for OCR file '{ocr_pdf_path}'"
                            )
                elif verbose and ocr_pdf_path is None:
                    print(f"Skipping OCR conversion for '{input_file_path}' due to OCR failure.")

            if not markdown_output:
                if conversion_error is None and verbose:
                    print(f"No markdown output generated for '{input_file_path}'")
                continue

            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_output)
            if verbose:
                if ocr_used:
                    print(f"Converted '{input_file_path}' after OCR to '{output_file_path}'")
                elif not fallback_used:
                    print(f"Converted '{input_file_path}' to '{output_file_path}'")
            new_processed.add(rel_path)

    save_history(history_path, processed_files.union(new_processed))

if __name__ == "__main__":
    main()
