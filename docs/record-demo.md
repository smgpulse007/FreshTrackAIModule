# README demo recording

The GIF is assembled from screenshots of the actual FastAPI app running locally,
in an isolated Microsoft Edge browser driven by Playwright CLI. It shows the
built-in synthetic text fixture: no real receipt, external account, OCR, or model
inference is involved. The exported JSON was downloaded through the UI and
checked for `synthetic_fixture` mode and three matched items.

To record an updated animation:

1. Start the primary API using the README instructions.
2. Open its local URL in an isolated browser with a 1280 x 960 viewport.
3. Save `output/playwright/gif-01.png` before loading a receipt.
4. Choose **Try the synthetic example**, wait for the results, and save
   `output/playwright/gif-02.png`.
5. Expand **Inspect extracted text** and save `output/playwright/gif-03.png`.
6. Choose **Download JSON**, save the returned file as
   `.playwright-cli/freshtrack-synthetic-fixture.json`, and capture
   `output/playwright/gif-04.png` with the export control focused.
7. Run `python scripts/assemble_demo.py` from the repository root. Pillow is
   already included in the primary API requirements.

For Playwright CLI, use a fresh `snapshot` to resolve each control before clicking
it, and `screenshot --filename=output/playwright/gif-01.png` to capture a frame.
The assembly script preserves actual screenshot content; pauses are adjusted for
readability, so the GIF is not a performance measurement.

`demo-recording.json` records the source, screenshot, download, and GIF hashes.
Raw browser captures and the downloaded fixture stay in ignored local directories.
The repository retains the finished GIF and this provenance record.
