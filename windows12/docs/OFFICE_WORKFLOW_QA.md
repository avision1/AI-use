# Public Office workflow QA

This is a small, synthetic, dependency-free corpus, not evidence of Office compatibility. It contains no personal data, macros, external relationships, embedded applications or network operations. Source structure and XML well-formedness checks cannot establish rendering or round-trip success. All GUI acceptance checks below remain **unperformed** until separately recorded against a real image and application version.

From `windows12/`, generate with:

```sh
python3 -B scripts/make-office-fixtures.py
```

Default output is `artifacts/office-fixtures/`. `--output` accepts only a directory inside this project and refuses existing symlink components/output files; relative paths are project-relative. Run in a trusted local workspace without concurrent path changes. The command replaces only its five named outputs. It uses fixed ZIP timestamps, sorted entries, stored ZIP members and fixed content. Identical source produces identical fixture bytes. `SHA256SUMS` covers the three Office files and `expected.json`; it does not cover itself. Preserve that original manifest and originals; edit copies in a separate project-contained evidence directory. No package installation, application launch or download occurs.

## Routes and evidence

LibreOffice Writer/Calc/Impress, if present in the selected image, is an **alternative** for offline Office interchange. Record exact version, image hash, fonts and locale. Authenticated Word/Excel/PowerPoint web workflows are a separate **partial** route requiring account access, network and applicable policy/licensing. A launcher or successful website load is not an authenticated edit/save test or native Microsoft desktop Office support. Do not infer one route's results from the other.

Use only these public fixtures. In the contained GUI, an authorized tester may upload these fixtures to the selected Microsoft service and download results into the contained evidence location; record that service/version where visible. Do not use private files, record credentials, send messages, share documents or create public links. If sign-in or required authorization is unavailable, mark the web route blocked and continue independent offline checks.

## Bounded acceptance procedure

For each file, preserve the original, open a working copy, record any repair/conversion/missing-font warning, inspect at normal zoom, make the specified edit, save as the original OOXML format, close the application, reopen that saved file and inspect again. Record format confirmation prompts and any lost feature. Export the reopened copy to PDF, reopen the PDF and inspect every page/slide. Keep before/after screenshots and the edited OOXML/PDF with the result record. Byte equality after application save is not expected. When possible, open the round-tripped OOXML in the intended consumer and record its exact version separately.

| File | Original acceptance content | Edit and post-reopen acceptance | Render/export acceptance |
|---|---|---|---|
| `garden-report.docx` | Title “Community garden report”; headings “Season overview” and “Review note”; five-row, two-column bordered table including header and total 54; Unicode line matching `expected.json` | Replace the instruction sentence with “Reviewed in the test desktop.”; headings, Unicode and table remain intact after save/reopen | Target one A4 page; no overlap, clipped text or missing glyphs; borders and all cells visible. Record actual page count and font substitutions. PDF preserves text/table and the edit. |
| `garden-budget.xlsx` | Sheet `Harvest`, A1:D7; D2=30, D3=45, D4=60, B5=54, D5=135, B6=18; B7 “Café / 日本語”. Formula cells contain formulas plus initial cached values. Inspect formula bar as well as display. | Change B2 from 12 to 14 and recalculate: D2=35, B5=56, D5=140, B6=56/3 (about 18.66666667). Save/reopen; confirm formulas remain formulas and all four results persist. | Labels and values readable without clipping or error cells; inspect print preview and export all used cells to PDF, fitting to one page if needed. Record print setting changes; confirm totals and edit in PDF. |
| `garden-review.pptx` | Exactly two 16:9 slides: “Community garden” with Unicode text, blue rectangle “54 baskets” and green ellipse “3 plots”; “Harvest review” lists North 12, East 18, South 24 | On slide 2 replace instruction text with “Reviewed in the test desktop.”; save/reopen with same two slides, text, shape colors/geometry and positions | Inspect both slides in editing and slideshow modes; no text overflow, overlap or missing glyphs. PDF has two landscape pages preserving both shapes and the edit. |

Record each stage independently as pass/fail/blocked/unperformed: original open, render, edit, OOXML save, reopen, recalculation (XLSX), slideshow (PPTX), PDF export/reopen and intended-consumer round trip. Include UTC date, image SHA256, route, application/browser version, relevant fonts/locale, fixture SHA256, output paths and observed defects. A failed or unperformed stage prevents a claim that the complete workflow passed. A successful small corpus does not certify complex layouts, charts, tracked changes, collaboration, macros, VBA, enterprise policies or all Office files.

## Format references

The generator uses standard OOXML package relationships/content types; DOCX includes styles, XLSX uses inline strings and numeric formula caches, and PPTX includes presentation properties, slides, a master, a layout and a complete theme. The XML parser check is not schema validation.

- Microsoft, [Structure of a PresentationML document](https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document).
- Microsoft, [Working with formulas](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/working-with-formulas) (the `v` element stores a cached formula value; the generator does not calculate formulas dynamically).
- Project route classifications and limitations: [COMPATIBILITY.md](COMPATIBILITY.md).

## Generation record — 2026-11-06
Lead executed only deterministic artifact generation and ZIPCRC/XML inspection, not an Office application. Two independent project-contained outputs were byte-identical. DOCX5371bytes SHA256629e5f9c37fc27366b5ed6a39a20c63f92ff1e2251e5d87494b8089f80ce8ee3; XLSX3684bytes SHA2569eba998075c889d5bd7ee1977332d6a171706434da9192ac5ae429cfe414d3c1; PPTX15750bytes SHA25684418688588f40508edd95b6fb45debcecfb43005f0c8f55f462c3b96c82e911. Generated artifacts are ignored/reproducible; no binary committed. All application acceptance stages remain unperformed.
