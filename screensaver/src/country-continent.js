// country-continent.js — static map from world-atlas (110m) feature id -> continent key.
//
// Why this file exists:
//   The brief originally assumed Natural Earth's CONTINENT property would be
//   present at runtime. The world-atlas v2 distillation (countries-110m.json)
//   strips properties down to { name } only, so we map by ISO 3166-1 numeric
//   id (the feature `id`). Three features have a null id (N. Cyprus,
//   Somaliland, Kosovo) and are mapped by name.
//
// Continent keys MUST match keys in anchor.js BASE_CONTINENTS.

const BY_ID = {
  // Africa (50)
  "012": "Africa", "024": "Africa", "072": "Africa", "108": "Africa", "120": "Africa",
  "140": "Africa", "148": "Africa", "178": "Africa", "180": "Africa", "204": "Africa",
  "226": "Africa", "231": "Africa", "232": "Africa", "262": "Africa", "266": "Africa",
  "270": "Africa", "288": "Africa", "324": "Africa", "384": "Africa", "404": "Africa",
  "426": "Africa", "430": "Africa", "434": "Africa", "450": "Africa", "454": "Africa",
  "466": "Africa", "478": "Africa", "504": "Africa", "508": "Africa", "516": "Africa",
  "562": "Africa", "566": "Africa", "624": "Africa", "646": "Africa", "686": "Africa",
  "694": "Africa", "706": "Africa", "710": "Africa", "716": "Africa", "728": "Africa",
  "729": "Africa", "732": "Africa", "748": "Africa", "768": "Africa", "788": "Africa",
  "800": "Africa", "818": "Africa", "834": "Africa", "854": "Africa", "894": "Africa",

  // Asia (46)
  "004": "Asia", "031": "Asia", "050": "Asia", "051": "Asia", "064": "Asia",
  "096": "Asia", "104": "Asia", "116": "Asia", "144": "Asia", "156": "Asia",
  "158": "Asia", "196": "Asia", "268": "Asia", "275": "Asia", "356": "Asia",
  "360": "Asia", "364": "Asia", "368": "Asia", "376": "Asia", "392": "Asia",
  "398": "Asia", "400": "Asia", "408": "Asia", "410": "Asia", "414": "Asia",
  "417": "Asia", "418": "Asia", "422": "Asia", "458": "Asia", "496": "Asia",
  "512": "Asia", "524": "Asia", "586": "Asia", "608": "Asia", "626": "Asia",
  "634": "Asia", "682": "Asia", "704": "Asia", "760": "Asia", "762": "Asia",
  "764": "Asia", "784": "Asia", "792": "Asia", "795": "Asia", "860": "Asia",
  "887": "Asia",

  // Europe (38)
  "008": "Europe", "040": "Europe", "056": "Europe", "070": "Europe", "100": "Europe",
  "112": "Europe", "191": "Europe", "203": "Europe", "208": "Europe", "233": "Europe",
  "246": "Europe", "250": "Europe", "276": "Europe", "300": "Europe", "348": "Europe",
  "352": "Europe", "372": "Europe", "380": "Europe", "428": "Europe", "440": "Europe",
  "442": "Europe", "498": "Europe", "499": "Europe", "528": "Europe", "578": "Europe",
  "616": "Europe", "620": "Europe", "642": "Europe", "643": "Europe", "688": "Europe",
  "703": "Europe", "705": "Europe", "724": "Europe", "752": "Europe", "756": "Europe",
  "804": "Europe", "807": "Europe", "826": "Europe",

  // North America (18)
  "044": "North_America", "084": "North_America", "124": "North_America",
  "188": "North_America", "192": "North_America", "214": "North_America",
  "222": "North_America", "304": "North_America", "320": "North_America",
  "332": "North_America", "340": "North_America", "388": "North_America",
  "484": "North_America", "558": "North_America", "591": "North_America",
  "630": "North_America", "780": "North_America", "840": "North_America",

  // South America (13)
  "032": "South_America", "068": "South_America", "076": "South_America",
  "152": "South_America", "170": "South_America", "218": "South_America",
  "238": "South_America", "328": "South_America", "600": "South_America",
  "604": "South_America", "740": "South_America", "858": "South_America",
  "862": "South_America",

  // Oceania (7)
  "036": "Oceania", "090": "Oceania", "242": "Oceania", "540": "Oceania",
  "548": "Oceania", "554": "Oceania", "598": "Oceania",

  // Antarctica (2; French Southern & Antarctic Lands grouped here as nearest match)
  "010": "Antarctica", "260": "Antarctica",
};

const BY_NAME = {
  "N. Cyprus": "Asia",
  "Somaliland": "Africa",
  "Kosovo": "Europe",
};

// world-atlas ids may be either string ("004") or number (4) depending on parser.
// Normalize to a 3-char zero-padded string before lookup.
function normalizeId(id) {
  if (id == null) return null;
  const s = String(id);
  return s.padStart(3, "0");
}

export function continentForFeature(feature) {
  const idKey = normalizeId(feature.id);
  if (idKey && BY_ID[idKey]) return BY_ID[idKey];
  const name = feature?.properties?.name;
  if (name && BY_NAME[name]) return BY_NAME[name];
  return null;
}
