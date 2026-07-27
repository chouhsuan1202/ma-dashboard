const fs = require("fs");
const assert = require("assert");

const html = fs.readFileSync(new URL("../index.html", `file://${__filename}`), "utf8");
const watchlist = JSON.parse(
  fs.readFileSync(new URL("../watchlist.json", `file://${__filename}`), "utf8"),
);
const match = html.match(/function dataUrlsForProtocol\(protocol\)\s*\{([\s\S]*?)\n\}/);

assert(match, "index.html should define dataUrlsForProtocol(protocol)");

const dataUrlsForProtocol = new Function(
  "protocol",
  `${match[1]}`,
);

assert.deepStrictEqual(dataUrlsForProtocol("https:"), [
  "watchlist.json",
  "data.json",
]);
assert.deepStrictEqual(dataUrlsForProtocol("file:"), [
  "https://raw.githubusercontent.com/chouhsuan1202/ma-dashboard/main/watchlist.json",
  "https://raw.githubusercontent.com/chouhsuan1202/ma-dashboard/main/data.json",
]);

const taiwan50 = watchlist.market_holdings.find((item) => item.s === "0050.TW");
assert.strictEqual(taiwan50.dn, "元大台灣50 · 0050");

console.log("file mode data source test passed");
