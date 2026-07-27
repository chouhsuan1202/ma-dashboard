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

const taiwanMarketLabels = Object.fromEntries(
  watchlist.market_holdings
    .filter((item) => item.s.endsWith(".TW"))
    .map((item) => [item.s, { dn: item.dn, note: item.note }]),
);
assert.deepStrictEqual(taiwanMarketLabels, {
  "0050.TW": { dn: "元大台灣50", note: "0050" },
  "006208.TW": { dn: "富邦台50", note: "006208" },
  "0056.TW": { dn: "元大高股息", note: "0056" },
  "00646.TW": { dn: "元大S&P500", note: "00646" },
});

console.log("file mode data source test passed");
