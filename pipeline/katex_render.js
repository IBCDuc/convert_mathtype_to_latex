
// Render 1 batch LaTeX -> KaTeX HTML, gọi từ Python qua subprocess (xem
// mathrender.py). Input: JSON array các chuỗi LaTeX trên stdin.
// Output: JSON array cùng độ dài, mỗi phần tử là HTML string (null nếu lỗi).
const katex = require("katex");

const _NEG_MAP = {
  "=": "≠", "⊂": "⊄", "∈": "∉", "⊆": "⊈", "≡": "≢", "∥": "∦", "<": "≮", ">": "≯"
};

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  const list = JSON.parse(input);
  const out = list.map((tex) => {
    try {
      let html = katex.renderToString(tex, {
        throwOnError: false, displayMode: false, output: "html",
      });
      if (html) {
        html = html.replace(/<span class="mrel">(?:<span class="mrel">)?<span class="mord katex-vbox">.*?[\uE000-\uF8FF].*?<\/span><span class="mspace nobreak"><\/span><span class="mrel">(.)<\/span>(?:<\/span>)?/g, (m, sym) => {
          return `<span class="mrel">${_NEG_MAP[sym] || sym}</span>`;
        });
      }
      return html;
    } catch {
      return null;
    }
  });
  process.stdout.write(JSON.stringify(out));
});
