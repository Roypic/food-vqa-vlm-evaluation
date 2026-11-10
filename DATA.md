# Data layout

The project dataset is not included in this repository. Copy the authorized files into this layout:

```text
data/raw/
├── Images GT.xlsx
├── Questions 50.xlsx
├── FDC_USDA_subset.csv
└── Meal Images/
    ├── MEAL1.*
    └── ...
```

The frozen study contains 20 meal images, 44 annotated food instances across 35 labels, and 50 free-text nutrition questions. `Images GT.xlsx` must contain the `Ground truths` sheet used by the scoring code.

The repository intentionally ignores spreadsheet, CSV, archive, and image files under `data/`. Confirm the source dataset's redistribution terms before changing those rules.

