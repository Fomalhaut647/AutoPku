-- callout.lua（增强版）
-- 将 > [!tip] / [!note] / [!warning] / [!example] 转为带样式、可跨页的 tcolorbox

local callout_config = {
  tip     = {color = "teal!75!black",   icon = "技巧"},
  note    = {color = "blue!65!black",    icon = "直觉"},
  warning = {color = "orange!85!black",  icon = "易错"},
  example = {color = "violet!70!black",  icon = "例"},
}

-- 用 pandoc 的 LaTeX writer 渲染标题 inlines：纯文本自动转义，行内数学（如 $<\tfrac12$）
-- 保留为 \(...\) 正常排版。勿用 stringify + 手写转义：会把 \tfrac12 打成字面 \{}tfrac12。
local function render_title(inlines)
  local doc = pandoc.Pandoc({pandoc.Plain(inlines)})
  local s = pandoc.write(doc, "latex")
  return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

function BlockQuote(el)
  local first = el.content[1]
  if not first or first.t ~= "Para" then return nil end

  local inlines = first.content
  if not inlines or #inlines == 0 then return nil end

  local tag_idx = nil
  for i, inline in ipairs(inlines) do
    if inline.t == "Str" and inline.text:match("^%[! ?%w+ ?%]$") then
      tag_idx = i
      break
    end
  end
  if not tag_idx then return nil end

  local ctype = inlines[tag_idx].text:match("^%[! ?(%w+) ?%]$")
  if not ctype then return nil end
  ctype = ctype:lower()

  local cfg = callout_config[ctype]
  if not cfg then return nil end

  local break_idx = nil
  for i = tag_idx + 1, #inlines do
    if inlines[i].t == "SoftBreak" or inlines[i].t == "LineBreak" then
      break_idx = i
      break
    end
  end

  local title_inlines = {}
  local body_inlines = {}

  if break_idx then
    for i = tag_idx + 1, break_idx - 1 do
      table.insert(title_inlines, inlines[i])
    end
    for i = break_idx + 1, #inlines do
      table.insert(body_inlines, inlines[i])
    end
  else
    for i = tag_idx + 1, #inlines do
      table.insert(title_inlines, inlines[i])
    end
  end

  local title_str = pandoc.utils.stringify(title_inlines)
  title_str = title_str:gsub("^%s+", ""):gsub("%s+$", "")   -- 仅用于与图标名比对
  local heading
  if not title_str or title_str == "" or title_str == cfg.icon then
    heading = cfg.icon          -- 标题为空或与图标同名时不重复
  elseif title_str:sub(1, #cfg.icon) == cfg.icon then
    -- 标题已以类型名开头（如「易错（final2025 真题）」「例 mid2024」）→ 直接用标题，
    -- 不再前缀「类型：」，否则成「易错：易错（…）」。#cfg.icon 是字节数，UTF-8 前缀比对安全。
    heading = render_title(title_inlines)
  else
    heading = cfg.icon .. "：" .. render_title(title_inlines)
  end

  local latex_begin = string.format(
    "\\begin{tcolorbox}[breakable, enhanced, colback=%s!4!white, colframe=%s, left=2mm, right=2mm, top=1mm, bottom=1mm, boxrule=0.4mm, arc=1.2mm, fonttitle=\\bfseries, coltitle=white, title={%s}]",
    cfg.color, cfg.color, heading
  )

  local result = {pandoc.RawBlock("latex", latex_begin)}

  if #body_inlines > 0 then
    table.insert(result, pandoc.Para(body_inlines))
  end

  for i = 2, #el.content do
    table.insert(result, el.content[i])
  end

  table.insert(result, pandoc.RawBlock("latex", "\\end{tcolorbox}"))
  return result
end
