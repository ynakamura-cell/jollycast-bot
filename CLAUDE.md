# JollyCast Support Bot — CLAUDE.md

## プロジェクト概要
フィリピン人キャスト向け英語サポートチャットbot（Streamlit製）。
ローカルパス: `C:\Users\y.nakamura\OneDrive - 株式会社CaSy\ドキュメント\Claude\Projects\jollycast-bot\`

## Zendeskキャッシュ再構築（確立済み手順）

APIトークンなし・Sophos環境下でも動作する唯一の確実な手順。

**前提条件:** Chrome で `casy.zendesk.com/hc/ja` が開いており、ログイン済みであること。

```
1. Chrome MCP で新タブを作成し https://casy.zendesk.com/hc/ja にナビゲート

2. JavaScript で全記事取得:
(async () => {
  const htmlToText = (html) => {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return (tmp.textContent || tmp.innerText || '').replace(/\s+/g, ' ').trim();
  };
  let articles = [], url = '/api/v2/help_center/ja/articles.json?per_page=100&sort_by=created_at&sort_order=asc';
  while (url) {
    const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
    const d = await r.json();
    for (const art of (d.articles || [])) {
      if (art.draft) continue;
      const content = htmlToText(art.body || '').substring(0, 8000);
      if (content.length > 80)
        articles.push({ url: `https://casy.zendesk.com/hc/ja/articles/${art.id}`, title: art.title || '', content });
    }
    url = d.next_page ? d.next_page.replace('https://casy.zendesk.com', '') : null;
  }
  window._zdArticles = articles;
  window._zdJson = JSON.stringify(articles, null, 2);
  return { total: articles.length };
})()

3. JSONをダウンロード:
const blob = new Blob([window._zdJson], {type: 'application/json'});
const a = document.createElement('a');
a.href = URL.createObjectURL(blob);
a.download = 'zendesk_cache_new.json';
document.body.appendChild(a); a.click(); document.body.removeChild(a);

4. PowerShell でコピー:
Copy-Item "$env:USERPROFILE\Downloads\zendesk_cache_new.json" ".\zendesk_cache.json"
```

**注意:**
- JavaScriptのツール結果から直接JSONを読もうとすると、記事内容にクエリ文字列に見えるパターンが含まれセキュリティフィルタでブロックされる → ダウンロード経由が唯一の方法
- `browser_cookie3` によるCookie直接読み取りはSophosに脅威認定されブロックされる
- ローカルHTTPサーバー経由（localhost POSTレシーブ）はChromeのPrivate Network Accessで接続タイムアウトになる

## テスト実行

```bash
# Spot20テスト（KNOWLEDGE検証20問 + Zendesk検証5問）
python run_test_spot20.py

# フルテスト150問（コスト約$30、複数改善まとめてから実行）
python run_test_full150.py
```

コスト管理: テストは$30超のため、複数のKNOWLEDGE改善をまとめてから実行すること。

## アーキテクチャ

- **TYPE A**（業務手順）: KNOWLEDGE → TROUBLE_FLOW → Zendeskキャッシュ の優先順
- **TYPE B**（日本の常識・ナビ）: Claudeの一般知識で回答、末尾に `*(General knowledge)*` 付与
- **プロンプトキャッシング**: `cache_control: ephemeral` でZendesk全文をキャッシュ
- **ストリーミング**: `client.messages.stream` で逐次表示

## 重要ファイル

| ファイル | 用途 |
|---|---|
| app.py | メインbot（KNOWLEDGE/TROUBLE_FLOWが埋め込まれている） |
| zendesk_cache.json | Zendeskキャッシュ（209記事、8000字切り捨て） |
| zendesk_loader.py | キャッシュローダー（APIトークン方式とクローラー方式の両対応） |
| run_test_spot20.py | Spot20テスト |
| run_test_full150.py | 150問フルテスト |
| jollycast_bot_test_questions.xlsx | Q1-Q150問題集 |
| jollycast_bot_test_results_v2.xlsx | テスト結果（Round1-7 + Spot-A/B） |
