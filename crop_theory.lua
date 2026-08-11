-- crop_theory.lua
local function fold(str)
    if not str then return "" end
    str = str:gsub("đ", "d"):gsub("Đ", "d")
    local vmap = {
        ["à"]="a", ["á"]="a", ["ả"]="a", ["ã"]="a", ["ạ"]="a",
        ["ă"]="a", ["ằ"]="a", ["ắ"]="a", ["ẳ"]="a", ["ẵ"]="a", ["ặ"]="a",
        ["â"]="a", ["ầ"]="a", ["ấ"]="a", ["ẩ"]="a", ["ẫ"]="a", ["ậ"]="a",
        ["À"]="a", ["Á"]="a", ["Ả"]="a", ["Ã"]="a", ["Ạ"]="a",
        ["Ă"]="a", ["Ằ"]="a", ["Ắ"]="a", ["Ẳ"]="a", ["Ẵ"]="a", ["Ặ"]="a",
        ["Â"]="a", ["Ầ"]="a", ["Ấ"]="a", ["Ẩ"]="a", ["Ẫ"]="a", ["Ậ"]="a",
        ["è"]="e", ["é"]="e", ["ẻ"]="e", ["ẽ"]="e", ["ẹ"]="e",
        ["ê"]="e", ["ề"]="e", ["ế"]="e", ["ể"]="e", ["ễ"]="e", ["ệ"]="e",
        ["È"]="e", ["É"]="e", ["Ẻ"]="e", ["Ẽ"]="e", ["Ẹ"]="e",
        ["Ê"]="e", ["Ề"]="e", ["Ế"]="e", ["Ể"]="e", ["Ễ"]="e", ["Ệ"]="e",
        ["ì"]="i", ["í"]="i", ["ỉ"]="i", ["ĩ"]="i", ["ị"]="i",
        ["Ì"]="i", ["Í"]="i", ["Ỉ"]="i", ["Ĩ"]="i", ["Ị"]="i",
        ["ò"]="o", ["ó"]="o", ["ỏ"]="o", ["õ"]="o", ["ọ"]="o",
        ["ô"]="o", ["ồ"]="o", ["ố"]="o", ["ổ"]="o", ["ỗ"]="o", ["ộ"]="o",
        ["ơ"]="o", ["ờ"]="o", ["ớ"]="o", ["ở"]="o", ["ỡ"]="o", ["ợ"]="o",
        ["Ò"]="o", ["Ó"]="o", ["Ỏ"]="o", ["Õ"]="o", ["Ọ"]="o",
        ["Ô"]="o", ["Ồ"]="o", ["Ố"]="o", ["Ổ"]="o", ["Ỗ"]="o", ["Ộ"]="o",
        ["Ơ"]="o", ["Ờ"]="o", ["Ớ"]="o", ["Ở"]="o", ["Ỡ"]="o", ["Ợ"]="o",
        ["ù"]="u", ["ú"]="u", ["ủ"]="u", ["ũ"]="u", ["ụ"]="u",
        ["ư"]="u", ["ừ"]="u", ["ứ"]="u", ["ử"]="u", ["ữ"]="u", ["ự"]="u",
        ["Ù"]="u", ["Ú"]="u", ["Ủ"]="u", ["Ũ"]="u", ["Ụ"]="u",
        ["Ư"]="u", ["Ừ"]="u", ["Ứ"]="u", ["Ử"]="u", ["Ữ"]="u", ["Ự"]="u",
        ["ỳ"]="y", ["ý"]="y", ["ỷ"]="y", ["ỹ"]="y", ["ỵ"]="y",
        ["Ỳ"]="y", ["Ý"]="y", ["Ỷ"]="y", ["Ỹ"]="y", ["Ỵ"]="y",
    }
    local res = ""
    for p, c in utf8.codes(str) do
        local char = utf8.char(c)
        res = res .. (vmap[char] or char)
    end
    return res:lower()
end

local function is_start_marker(t)
    t = t:match("^%s*(.-)%s*$")
    return t:find("kien thuc trong tam") or t:find("ly thuyet") or t:find("tom tat ly thuyet") or t:find("phan li thuyet") or t:find("phan ly thuyet")
end

local function is_end_marker(t)
    t = t:match("^%s*(.-)%s*$")
    -- Check if it contains "bai tap" and matches exercise section header variations
    if t:find("bai tap") then
        if t:find("^b%s*[%.%-%–%:]%s*bai tap") or t:find("^phan%s+bai tap") or t:find("^bai tap") or t:find("b%.%s*bai tap") then
            return true
        end
    end
    return false
end

local function is_roman_numeral(str)
    return str:find("^%s*[IVX]+%s*[%.%-%–%:]") ~= nil
end

local function is_upper_alpha(str)
    return str:find("^%s*[A-Z]%s*[%.%-%–%:]") ~= nil
end

local function is_major_keyword(t)
    return t:find("tong ket") ~= nil or t:find("ghi nho") ~= nil or t:find("doc van ban") ~= nil or t:find("kham pha van ban") ~= nil or t:find("ly thuyet") ~= nil
end

local function is_arabic_heading(raw)
    return raw:find("^%s*%d+%.%s+") ~= nil or raw:find("^%s*Hoạt động%s+%d+") ~= nil or raw:find("^%s*Câu hỏi%s+%d+") ~= nil
end

local function is_alpha_lower_heading(raw)
    return raw:find("^%s*[a-z]%)%s+") ~= nil or raw:find("^%s*[a-z]%.%s+") ~= nil
end

local function is_star_heading(raw)
    return raw:find("^%s*%*%s*") ~= nil and raw:find(":%s*$") ~= nil
end

local function clean_str_leading_bullet(s)
    if not s then return "" end
    s = s:gsub("^%s*[%-%+%*]%s*", "")
    -- Safely strip multi-byte UTF8 bullet symbols (•, –, —) without byte class corruption
    if s:sub(1, 3) == "•" or s:sub(1, 3) == "–" or s:sub(1, 3) == "—" then
        s = s:sub(4):gsub("^%s*", "")
    end
    return s
end

local function clean_inlines_dash(inlines)
    if not inlines or #inlines == 0 then return inlines end
    local first = inlines[1]
    if first.t == "Str" then
        first.text = clean_str_leading_bullet(first.text)
        if #first.text == 0 then
            table.remove(inlines, 1)
            if #inlines > 0 and inlines[1].t == "Space" then
                table.remove(inlines, 1)
            end
        end
    elseif first.t == "Strong" or first.t == "Emph" then
        first.content = clean_inlines_dash(first.content)
    end
    return inlines
end

local function clean_item_blocks(blocks)
    for _, b in ipairs(blocks) do
        if b.t == "Para" or b.t == "Plain" then
            b.content = clean_inlines_dash(b.content)
        end
    end
    return blocks
end

local function transform_block(block)
    if block.t == "BulletList" then
        for _, item in ipairs(block.content) do
            clean_item_blocks(item)
        end
        return block
    end

    local raw = pandoc.utils.stringify(block)
    local t = fold(raw)
    if #t == 0 or #t > 250 then
        return block
    end

    local inlines = (block.t == "Para" and block.content) or (block.t == "Header" and block.content) or { pandoc.Str(raw) }

    -- 1. Mục lớn (I., II., III., IV., A., B., TỔNG KẾT, GHI NHỚ) -> Header 2
    if is_roman_numeral(raw) or is_upper_alpha(raw) or is_major_keyword(t) then
        return pandoc.Header(2, inlines)
    end

    -- 2. Mục con cấp 2 (1. Tác giả, 2. Văn bản, 1. Thiên nhiên..., Hoạt động 1) -> Header 3
    if is_arabic_heading(raw) then
        return pandoc.Header(3, inlines)
    end

    -- 3. Mục con cấp 3 (a. Mạch cảm xúc, b. Thiên nhiên, a) Đồ thị) -> Header 4
    if is_alpha_lower_heading(raw) then
        return pandoc.Header(4, inlines)
    end

    -- 4. Mục chú thích/bố cục (* Bố cục:, * Nghệ thuật:) -> Header 5
    if is_star_heading(raw) then
        return pandoc.Header(5, inlines)
    end

    return block
end

function Pandoc(doc)
    local has_start = false
    -- Pass 1: Check if there is an explicit theory start header in the document
    for _, block in ipairs(doc.blocks) do
        local raw = pandoc.utils.stringify(block)
        local t = fold(raw)
        if #t <= 100 and is_start_marker(t) then
            has_start = true
            break
        end
    end

    local in_theory = not has_start -- If no start marker, assume theory starts from top
    local new_blocks = {}

    for _, block in ipairs(doc.blocks) do
        local raw = pandoc.utils.stringify(block)
        local t = fold(raw)

        if #t <= 100 then
            if not in_theory and is_start_marker(t) then
                in_theory = true
                -- Skip the theory header line itself
                goto continue
            elseif in_theory and is_end_marker(t) then
                in_theory = false
                break -- Stop processing further blocks!
            end
        end

        if in_theory then
            if block.t == "BlockQuote" then
                for _, sub in ipairs(block.content) do
                    table.insert(new_blocks, transform_block(sub))
                end
            else
                table.insert(new_blocks, transform_block(block))
            end
        end

        ::continue::
    end

    return pandoc.Pandoc(new_blocks, doc.meta)
end
