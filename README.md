# 光影立方 LIGHT CUBE · WebAR

掃描酷卡背面的 QR Code，手機會打開這個網頁並開啟相機。鏡頭對準酷卡**正面**後，卡上的立方體會以 3D 方式浮出，同時有故障錯位、掃描光、數位粒子，以及展期資訊牌。

## 檔案

| 檔案 | 說明 |
|---|---|
| `index.html` | AR 網頁，不需要 build，three.js 和 MindAR 都從 CDN 載入 |
| `targets.mind` | **需要你自己產生**：用酷卡正面圖片編譯出來的辨識檔（見步驟 2） |

## 步驟

### 1. 匯出酷卡正面圖
從設計畫布匯出**定稿**的正面 PNG，寬度建議 1000px 以上。
辨識檔必須和實際印刷的正面一模一樣，正面之後只要有改動，就要重新做步驟 2。

### 2. 編譯辨識檔 `targets.mind`
1. 打開 MindAR 官方的 Image Targets Compiler：<https://hiukim.github.io/mind-ar-js-doc/tools/compile>
2. 上傳正面 PNG，按 **Start**。
3. 完成後按 **Download compiled**，把下載的檔案改名為 `targets.mind`，放進和 `index.html` 同一個資料夾。

### 3. 本機測試（電腦＋視訊鏡頭）
```bash
cd lightcube-ar
npx serve .
```
用電腦瀏覽器開 `http://localhost:3000`，再把手機螢幕上的正面圖拿到鏡頭前。
（手機的相機只允許在 https 網址下開啟，所以要用手機測試請直接做步驟 4。）

### 4. 部署到 Vercel
```bash
cd lightcube-ar
npx vercel --prod
```
你也可以把資料夾拖進 Vercel 網站。部署完成後取得 https 網址，用這個網址產生 QR Code，貼到酷卡背面左下角的 QR 框裡。

## 調整

`index.html` 裡的 `CONFIG` 可以直接修改：

- `depth`：分層深度倍率，目前是 1.8，1 是最初的版本
- `cubeSize`：立方體大小，以 1 為卡片寬度
- `cubeLift`：立方體浮出卡面的高度
- `sway`：立方體左右擺動的幅度
- `explodeEvery`：立方體爆開重組的間隔秒數
- `glitchEvery`：故障閃爍的間隔秒數
- `particles`：數位粒子數量

## 印刷與辨識小提醒

- 酷卡用**霧面**紙。亮面紙容易反光，會造成辨識失敗。
- 正面細節多、對比高，有利於辨識。之後如果改圖，避免大面積純色或大面積重複花紋。
- 在 LINE 或 IG 內建瀏覽器開啟時，可能無法使用相機，請改用 Safari 或 Chrome。可以在 QR 旁加註提醒。

## 海報（A1 主視覺）
- `targets.mind` 內含兩張辨識圖：第 0 張 = 酷卡正面（`targets/card.jpg`），第 1 張 = A1 海報（`poster/poster.jpg`）。掃到哪張就播哪張的分層效果。
- 海報圖層直接從海報原圖切出（`poster/*.png` + `poster/layers.json`），`poster/cover.jpg` 是抹掉浮起元素後的底圖。改了海報要重切：`python3 poster/split_poster.py 海報.jpg poster`
- 重新編譯辨識檔：`node targets/compile.cjs targets.mind targets/card.jpg poster/poster.jpg`（需要 Playwright；也可以到 https://hiukim.github.io/mind-ar-js-doc/tools/compile 依同樣順序上傳兩張圖）
- 桌機預覽（不開相機）：`index.html?preview=poster&tilt=0.9` 或 `?preview=card`

## 酷卡正面圖層（2026-11-12 起）
- 酷卡的浮起圖層是從**原始分層設計檔**（`光影立方_酷卡正面_分圖層.svg`）每個群組單獨輸出的透明 PNG（`card/*.png` + `card/layers.json`），所以和印刷完全一致；`card/cover.jpg` 是純紙色底，印刷上的立方體堆疊由 3D 立方體取代。
- 原始 SVG 是改版前的排版；輸出時已套用印刷定稿的位移：標語 +15 px、底部資訊列 +12.5 px（設計稿 600×888），整體再 −2 px 對齊印刷 PDF。
- 重做步驟（改了酷卡正面就要重做）：
  1. `python card/build_card_layers.py svgs <分圖層.svg> <svg 資料夾>`
  2. 啟動 `node card/ar_server.cjs`（需要把 svg / png 資料夾放在它旁邊的 `svg_layers/`、`png_layers/`），用 Chrome 開 `/_render.html`，執行 `renderAll([...])` 輸出 PNG（MuPDF 畫不出網紋與裁切，要用 Chrome）
  3. `python card/build_card_layers.py pack <分圖層.svg> <png 資料夾> card`
