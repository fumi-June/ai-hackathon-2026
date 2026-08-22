# ai-hackathon-2026 — ハッカソン提出用の公開ページ

提出物（Web作品）の置き場。**`docs/` の中身を差し替えて push するだけ**で公開される。

## 公開URL（提出用）

- 本命: https://fumi-june.github.io/ai-hackathon-2026/ （GitHub Pages, main:/docs）
- 予備: https://ai-hackathon-2026-697.pages.dev/ （Cloudflare Pages, 同じ docs/ を手動デプロイ）

## 当日の載せ替え手順

1. `docs/` に作品一式を置く（`index.html` ほか）。**アセット参照はすべて `./` 相対パス**
   （`/main.js` のような絶対パスは GitHub Pages のサブパス配信で 404 になる）
   - `presen.html` は消さない。作品の隅に `<a href="./presen.html">▶ プレゼン</a>` を1本入れる（同一URLでプレゼン⇔作品を行き来）
2. `git add -A && git commit -m "作品" && git push` → 数分で GitHub Pages に反映
3. 予備を更新する場合: `npx wrangler pages deploy docs --project-name=ai-hackathon-2026`

## 注意

- `docs/.nojekyll` は消さない（`_` 始まりのファイルが無視されるのを防ぐ）
- AIをバックエンドで使う場合は公開API/公開サーバーのみ（tailnet限定は不可）
- **APIキーはフロントに置かない**。Workerの `wrangler secret put ANTHROPIC_API_KEY` のみ。`.wrangler/` はコミット禁止（.gitignore済み）
- Cloudflare Workers のバックエンドが必要になったら `flood-map/worker/` の構成を流用
  （アカウント・workers.dev サブドメイン `fumi-june` は設定済み）
- ロールバックは Cloudflare 側が速い（ダッシュボードで前デプロイに即復帰）
