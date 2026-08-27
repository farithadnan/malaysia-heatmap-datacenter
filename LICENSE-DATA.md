# LICENSE-DATA — Database content license (ODbL)

The **data** in this repository (`data/`: CSVs, GeoJSON, query definitions,
and derived extracts) is licensed to you under the

**Open Database License (ODbL) v1.0**
<https://opendatacommons.org/licenses/odbl/1-0/>

The full license text is available at that URI (ODbL §4.3 permits referencing
the license by URI in produced works and databases).

## Why ODbL, and what it means to you

A portion of this dataset is derived from **OpenStreetMap** (© OpenStreetMap
contributors), whose own data is published under ODbL. Using ODbL keeps the
derivative database compatible with that source (spec §11 requirement).

In plain terms (the license text prevails):

- **Share** — you may copy and redistribute the database, commercially or not.
- **Create / Adapt** — you may produce works (e.g. maps) from it.
- **Attribute** — you must credit this project **and** OpenStreetMap
  contributors, and make the licensing clear:
  `Data © OpenStreetMap contributors (ODbL 1.0), Malaysia Data Center Map project`
- **Share-Alike** — public adaptations of the *database itself* must remain
  under ODbL.
- **Keep open** — if you redistribute a technological-restriction-protected
  version, you must also offer one without.

## Code vs data

- **Code** (map page, scripts, workflows) → MIT, see [`LICENSE`](LICENSE).
- **Data** (everything under `data/`) → ODbL (this file).

Source-note row precedent: each data row carries its own `capacity_source`,
so non-OSM-sourced facts (press releases, official announcements) retain
their provenance alongside the OSM-derived ones.
