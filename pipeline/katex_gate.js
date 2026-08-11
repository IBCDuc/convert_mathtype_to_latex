// Gate 1: Strict KaTeX Validation Tool (throwOnError: true)
// Called by test harness (tests/test_katex_gate.py)
const katex = require("katex");

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  const list = JSON.parse(input);
  const out = list.map((tex) => {
    if (!tex || typeof tex !== "string" || !tex.strip ? !tex.trim() : !tex.trim()) {
      return null;
    }
    try {
      katex.renderToString(tex, {
        throwOnError: true,
        strict: false,
        displayMode: false,
        output: "html",
      });
      return null; // Null means success (0 errors)
    } catch (e) {
      return String(e.message || e).slice(0, 200); // Return error message
    }
  });
  process.stdout.write(JSON.stringify(out));
});
