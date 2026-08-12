// Render 1 batch LaTeX -> KaTeX HTML, gọi từ Python qua subprocess (xem
// mathrender.py). Input: JSON array các chuỗi LaTeX trên stdin.
//
// Output: JSON array cùng độ dài, mỗi phần tử là object:
//     { "html": string|null, "error": string|null }
//   html  = HTML để nhúng (null nếu KaTeX chết hẳn -> mathrender fallback <code>)
//   error = null nếu công thức ĐẠT ở chế độ nghiêm; ngược lại là thông báo lỗi
//
// VÌ SAO CÓ TRƯỜNG "error":
//   Trước đây file này chỉ dùng throwOnError:false, nên KaTeX không bao giờ ném
//   lỗi — nó âm thầm trả HTML chứa class="katex-error" màu đỏ và pipeline coi
//   là thành công. Không có bước nào trong hệ thống có thể fail vì công thức sai.
//
//   Nay mỗi công thức được thử HAI LẦN:
//     1. throwOnError:true  -> chỉ để PHÁT HIỆN lỗi (không dùng kết quả)
//     2. throwOnError:false -> render thật, giữ nguyên hành vi hiển thị như cũ
//   Nhờ vậy HTML xuất ra KHÔNG ĐỔI, nhưng lỗi trở nên quan sát được.

const katex = require("katex");

const _NEG_MAP = {
  "=": "≠", "⊂": "⊄", "∈": "∉", "⊆": "⊈", "≡": "≢", "∥": "∦", "<": "≮", ">": "≯"
};

// Gộp ký tự phủ định (KaTeX dựng bằng vbox + ký tự Private Use Area) thành 1 ký
// tự Unicode thật. Dùng RegExp constructor để dải - được escape rõ
// ràng thay vì nhúng ký tự PUA vô hình vào source.
const _NEG_RE = new RegExp(
  '<span class="mrel">(?:<span class="mrel">)?<span class="mord katex-vbox">' +
  '.*?[\\uE000-\\uF8FF].*?<\\/span><span class="mspace nobreak"><\\/span>' +
  '<span class="mrel">(.)<\\/span>(?:<\\/span>)?',
  "g"
);

function postprocess(html) {
  if (!html) return html;
  return html.replace(_NEG_RE, (m, sym) => `<span class="mrel">${_NEG_MAP[sym] || sym}</span>`);
}

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  const list = JSON.parse(input);
  const out = list.map((tex) => {
    // (1) PHÁT HIỆN — nghiêm ngặt, không dùng kết quả render
    let error = null;
    try {
      katex.renderToString(tex, { throwOnError: true, strict: false, displayMode: false });
    } catch (e) {
      error = String((e && e.message) || e).slice(0, 200);
    }
    // (2) RENDER THẬT — khoan dung, giữ nguyên hành vi cũ
    let html = null;
    try {
      html = postprocess(katex.renderToString(tex, {
        throwOnError: false, displayMode: false, output: "html",
      }));
    } catch {
      html = null;
    }
    return { html, error };
  });
  process.stdout.write(JSON.stringify(out));
});
