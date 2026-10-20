# Verification record

Verified on 20 October 2026 (America/New_York).

- Application/test checkpoint: `c47e33f04afd30f61ac3bc383157db567e468e93`.
- Local Python 3.12: **41 pytest tests passed**, dependency check passed, CLI demo completed.
- [GitHub Actions run 39510515861](https://github.com/Mathewlewisagani/ai110-module2show-pawpal-starter/actions/runs/39510515861): **success**, including both Python **3.11** and **3.12** jobs. Each job installs requirements, checks dependencies, runs the full test suite, and executes `main.py`.
- Repository verified through GitHub: public fork of `codepath/ai110-module2show-pawpal-starter`; `main` pushes target the owner's fork, with the source retained as `upstream`.
- Real local browser: sample household contains two pets and four tasks; the 08:00 overlap warning appears; the priority plan moves Morning walk to 08:10 and explicitly defers Enrichment play beyond the window.
- Real browser persistence walkthrough: downloaded the sample household JSON, uploaded that same file, checked the replacement confirmation, restored successfully, and verified the returned two-pet/four-task household. The screenshot below captures the restore confirmation and restored schedule.
- The screenshot contains synthetic sample data. Visual review used the actual local Streamlit application; it is not a mockup or a full browser/accessibility certification.
- This final verification record and screenshot are documentation-only changes after the tested application checkpoint.

![Restored sample household in the real PawPal app](pawpal-preview.png)
