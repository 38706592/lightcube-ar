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

- `depth`：分層深度倍率，1 是預設，2 是兩倍立體
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
