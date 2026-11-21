const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const site = path.join(__dirname, '..', 'site');
const source = fs.readFileSync(path.join(site, 'app.js'), 'utf8');
const curriculum = JSON.parse(fs.readFileSync(path.join(site, 'curriculum.json'), 'utf8'));
const context = vm.createContext({
  curriculum,
  document: {querySelector: () => null},
  localStorage: {getItem: () => null},
  location: {hash: ''},
  window: {addEventListener() {}}
});
vm.runInContext(source.slice(0, source.lastIndexOf("fetch('curriculum.json')")), context);
vm.runInContext('db = curriculum', context);

function checkHeadingOrder(html, route) {
  const headings = Array.from(html.matchAll(/<h([1-6])(?:\s[^>]*)?>/g), match => Number(match[1]));
  assert.equal(headings[0], 1, route);
  assert.equal(headings.filter(level => level === 1).length, 1, route);
  assert.equal(headings[1], 2, route);
  for (let i = 1; i < headings.length; i++) {
    assert(headings[i] <= headings[i - 1] + 1, `${route} skips from h${headings[i - 1]} to h${headings[i]}`);
  }
}

for (const {id} of curriculum.lessons) {
  checkHeadingOrder(vm.runInContext(`lesson(${id})`, context), `Lesson ${id}`);
}
checkHeadingOrder(vm.runInContext('final()', context), 'Patch practice');

console.log('Passed: lesson and patch practice heading levels.');
