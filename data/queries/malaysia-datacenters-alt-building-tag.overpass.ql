// Malaysia data centers — ALTERNATE tag query (supplemental)
// Some mappers use building=data_center instead of telecom=data_center.
// WARNING: results overlap the primary query (facilities can carry both tags).
// Deduplicate by OSM element id when merging into data/pending.csv.
// Result provenance: data/raw/osm-building-data_center-2026-08-26.json  (15 elements,
//   incl. 14 unnamed consecutive ways forming one campus cluster — review as one facility)
[out:json][timeout:60];
area["ISO3166-1"="MY"]->.searchArea;
(
  node["building"="data_center"](area.searchArea);
  way["building"="data_center"](area.searchArea);
  relation["building"="data_center"](area.searchArea);
);
out center tags;
