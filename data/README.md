# Raw rollout logs

`results_raw.tar.xz` holds every raw rollout log of the study: `results/raw/main` (v1), `results/raw/v2/{A,B,C,D}`, `results/raw/v3/{E1a,E1b,E2,E3,E4}`, `results/raw/v4/{F1,F2}`, the pilots (`pilot`, `pilot2`, `pilot_v2`, `pilot_v3`, `pilot_v4`), the cost probe and the scripted dry runs; 19,757 JSON files, 157 MB unpacked. Everything in them is synthetic sandbox content (fake files, fake addresses, labelled fake secrets); no credential or environment variable of the machine that ran the study is in them.

Check and unpack from the repository root:

```bash
sha256sum -c data/SHA256SUMS
tar -C results -xJf data/results_raw.tar.xz
```

If the archive is ever split into parts (`results_raw.tar.xz.00.part`, ...), reassemble first with `cat data/results_raw.tar.xz.*.part > data/results_raw.tar.xz`.

With the logs in place, every stage can be re-scored and re-analysed with the commands in the main README; the scored CSVs under `results/scored` and the analysis outputs under `results/analysis` are also committed, so the analyses run without unpacking.
