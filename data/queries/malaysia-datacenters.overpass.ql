// Malaysia data centers — primary seed query (spec §6 source 1, Issue #2)
// Tag: telecom=data_center (the tag the spec names)
// Run in Overpass Turbo (https://overpass-turbo.eu) or via the API:
//   curl "https://overpass-api.de/api/interpreter" --data-urlencode data@malaysia-datacenters.overpass.ql
// Result provenance: data/raw/osm-telecom-data_center-2026-08-26.json  (24 elements)
[out:json][timeout:60];
area["ISO3166-1"="MY"]->.searchArea;
(
  node["telecom"="data_center"](area.searchArea);
  way["telecom"="data_center"](area.searchArea);
  relation["telecom"="data_center"](area.searchArea);
);
out center tags;
