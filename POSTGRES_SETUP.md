# PostgreSQL設定手順

## 🚀 Renderでの PostgreSQL 設定

### 1. Renderダッシュボードにアクセス
- https://dashboard.render.com にログイン

### 2. PostgreSQLデータベースを作成
1. **「New」ボタン** → **「PostgreSQL」** を選択
2. 設定項目:
   - **Name**: `stock-analysis-db` (任意の名前)
   - **Database**: `stockanalysis` (任意のDB名)
   - **User**: `stockuser` (任意のユーザー名)
   - **Region**: `Oregon (US West)` 推奨
   - **PostgreSQL Version**: `15` (最新安定版)
   - **Plan**: **Free** を選択 ✅
3. **「Create Database」** をクリック

### 3. データベース情報を確認
作成後、以下の情報が表示されます：
```
Host: dpg-xxxxx-a.oregon-postgres.render.com
Database: stockanalysis
Username: stockuser
Password: xxxxxxxxxxxxxxxxxx
Port: 5432
```

**Internal Database URL** をコピー（例）:
```
postgres://stockuser:xxxxx@dpg-xxxxx-a/stockanalysis
```

### 4. Web Service に環境変数を設定
1. **Web Service** ページに移動
2. **「Environment」** タブを選択
3. **環境変数を追加**:
   - **Key**: `DATABASE_URL`
   - **Value**: コピーしたInternal Database URL
4. **「Save Changes」** をクリック
5. 自動デプロイが開始されます

### 5. 確認
デプロイ完了後、ログで以下のメッセージが表示されることを確認:
```
✅ PostgreSQLデータベースに接続中...
✅ データベース接続成功: postgresql://stockuser:***
```

## 🔄 移行手順

### 既存データがある場合
1. **移行前**: 💾データエクスポートでバックアップ作成
2. **PostgreSQL設定**: 上記手順でPostgreSQL設定
3. **移行後**: 📂データインポートで復元

### ローカル開発
環境変数 `DATABASE_URL` が設定されていない場合は、自動的にSQLiteを使用します。
本番環境のPostgreSQLに接続する場合は、ローカルでも同じ環境変数を設定してください。

## 🎯 完了後の利点
- ✅ **完全自動永続化**: データが永続的に保存
- ✅ **デプロイ安全**: デプロイ時にデータが消えない
- ✅ **バックアップ不要**: 手動操作が不要
- ✅ **スケーラブル**: 将来的な拡張にも対応
- ✅ **高信頼性**: PostgreSQLの安定性

## 🆘 トラブルシューティング

### エラー: データベース接続失敗
1. **DATABASE_URL** の設定を確認
2. PostgreSQLデータベースが作成されているか確認
3. ログで詳細エラーメッセージを確認

### フォールバック動作
接続に失敗した場合、自動的にSQLiteフォールバックが動作します:
```
SQLiteフォールバックデータベースを使用
```

この場合でも基本機能は使用できますが、永続化は保証されません。