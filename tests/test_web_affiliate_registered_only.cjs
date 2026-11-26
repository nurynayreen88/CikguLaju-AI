"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const html = fs.readFileSync("web_v1_static_preview/index.html", "utf8");
const script = fs.readFileSync("web_v1_static_preview/web-referral.js", "utf8");
const select = html.match(/<select id="affiliate-members-filter">([\s\S]*?)<\/select>/)[1];
assert.deepEqual([...select.matchAll(/<option value="([^"]+)"/g)].map(m => m[1]), ["registered", "unpaid", "paid"]);
assert.match(select, /value="registered" selected/);
assert.match(html, /id="affiliate-admin-clear-member" type="button">Lihat Semua Tuntutan/);
const resolve = script.match(/const referralStatus = (.*);/)[1];
for (const value of ["all", "none", "", "registered", "unpaid", "paid"]) {
  const actual = Function("membersFilter", "return " + resolve)({value});
  assert.equal(actual, ["registered", "unpaid", "paid"].includes(value) ? value : "registered");
}
const predicate = script.match(/const registeredMembers = data\.items\.filter\((.*)\);/)[1];
const members = [{registered_count:0}, {registered_count:"1"}, {registered_count:2}, {registered_count:null}];
assert.deepEqual(members.filter(Function("return " + predicate)()), members.slice(1,3));
assert.match(script, /referral_status:referralStatus/);
assert.match(script, /for \(const item of registeredMembers\)/);
assert.match(script, /\/api\/web\/admin\/affiliate\/claims\?\$\{query\}/);
console.log("Affiliate admin registered-only filter and independent claims path PASS");
