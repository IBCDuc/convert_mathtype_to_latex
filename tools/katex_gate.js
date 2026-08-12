// Cổng kiểm định KaTeX — throwOnError:true, NGƯỢC với pipeline/katex_render.js.
//
// katex_render.js dùng throwOnError:false nên KaTeX không bao giờ ném lỗi; nó
// âm thầm trả HTML chứa class="katex-error" màu đỏ và pipeline coi là thành
// công. Cổng này tồn tại để một công thức sai có thể LÀM FAIL BUILD.
//
// Dùng:  echo '["\\frac{1}{2}", "\\frac{1{2}"]' | node tools/katex_gate.js
// Vào :  JSON array các chuỗi LaTeX trên stdin
// Ra  :  JSON array cùng độ dài — null = ĐẠT, string = thông báo lỗi
//
// LƯU Ý: Node phân giải require("katex") theo VỊ TRÍ FILE SCRIPT, không theo
// cwd. File này phải nằm trong project (cạnh node_modules/), không phải /tmp.

const katex = require("katex");

// strict:false  -> chỉ bắt lỗi cú pháp cứng (khuyến nghị cho cổng phát hành)
// strict:"error" -> bắt thêm cảnh báo Unicode/ligature (nghiêm hơn ~1.5x)
const STRICT = process.env.KATEX_STRICT === "1" ? "error" : false;
const DISPLAY = process.env.KATEX_DISPLAY === "1";

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (c) => { input += c; });
process.stdin.on("end", () => {
  let list;
  try {
    list = JSON.parse(input);
  } catch (e) {
    process.stderr.write("katex_gate: stdin không phải JSON array hợp lệ\n");
    process.exit(2);
  }
  const out = list.map((tex) => {
    try {
      katex.renderToString(tex, {
        throwOnError: true,
        strict: STRICT,
        displayMode: DISPLAY,
      });
      return null;
    } catch (e) {
      return String((e && e.message) || e).slice(0, 200);
    }
  });
  process.stdout.write(JSON.stringify(out));
});
