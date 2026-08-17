---
name: markitdown
description: Convert documents into Markdown so their text can be read and analyzed — PDF, Word (.docx), Excel (.xlsx/.xls), PowerPoint (.pptx), Outlook (.msg), EPub, HTML, CSV, JSON, XML, ZIP archives, images (EXIF/OCR), audio (transcription), and YouTube URLs. Use whenever the user points at such a file and wants it summarized, searched, extracted from, reviewed, or turned into Markdown — especially for binary formats that cannot be read directly.
homepage: https://github.com/microsoft/markitdown
compatibility: Requires the `markitdown` CLI on PATH. Installed here via `uv tool install 'markitdown[all]'` (v0.1.5).
platforms: [macos, linux, windows]
---

# MarkItDown

Microsoft's document-to-Markdown converter. Its job is to make binary and structured
document formats readable, preserving structure (headings, lists, tables, links) as
Markdown rather than extracting a flat blob of text.

Reach for this whenever a task involves a file the Read tool cannot usefully open.

## Usage

```bash
markitdown report.pdf                  # to stdout
markitdown report.pdf -o report.md     # to a file
cat report.pdf | markitdown            # from stdin
markitdown https://example.com/a.docx  # from a URL
```

## Working with the output

Send the output to a file rather than reading a large document into context:

```bash
markitdown "long-report.pdf" -o /tmp/report.md && wc -l /tmp/report.md
```

Then Read or Grep that Markdown file. A 50-page PDF can exceed 100k characters, so
check the size before reading it whole, and prefer Grep when hunting for something
specific.

Quote paths — document filenames very often contain spaces.

## Notes on specific formats

- **Scanned PDFs / images** fall back to OCR and EXIF. Quality varies; if output looks
  empty or garbled, say so rather than treating the result as authoritative.
- **Spreadsheets** convert each sheet to a Markdown table. Formulas render as their
  computed values, not the formula text.
- **Audio** uses speech recognition and needs network access. Transcripts are
  best-effort — treat them as approximate.
- **YouTube URLs** pull the transcript, not the video.
- **ZIP archives** are walked and each contained file converted in turn.

## Failure modes

A non-zero exit usually means a missing optional dependency or a corrupt/encrypted
file. Encrypted PDFs fail — there is no password flag; report that back to the user
instead of trying to work around it.

Check the installation with `markitdown --version`. To upgrade:
`uv tool upgrade markitdown`.

## Privacy

Conversion is local for every format except audio transcription and YouTube, which
make network calls. When converting a user's personal documents, don't echo the full
contents into the transcript unless asked — report what was found and write the
Markdown to a file.
