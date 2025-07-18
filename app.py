from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sys
import os

# 既存のStockAnalyzerクラスをインポート
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from stock_analysis import StockAnalyzer
from database import StockDatabase

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """ヘルスチェック用エンドポイント"""
    from datetime import datetime
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'message': 'Stock analysis app is running'
    })

@app.route('/test')
def test_route():
    """デプロイテスト用エンドポイント"""
    return "Deploy test successful"

@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    try:
        data = request.get_json()
        ticker = data.get('ticker', '').upper().strip()
        
        if not ticker:
            return jsonify({'error': 'ティッカーコードが必要です'}), 400
        
        analyzer = StockAnalyzer()
        
        # プログレス情報を無効化するために、一時的にprintを無効化
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            result = analyzer.analyze_stock_for_web(ticker)
        
        if result is None:
            return jsonify({'error': f'{ticker}のデータを取得できませんでした'}), 404
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'エラーが発生しました: {str(e)}'}), 500

@app.route('/api/database/stocks', methods=['GET'])
def get_database_stocks():
    """データベースに保存されている全銘柄を取得"""
    try:
        db = StockDatabase()
        stocks = db.get_all_stocks()
        return jsonify({'stocks': stocks})
    except Exception as e:
        return jsonify({'error': f'データベースエラー: {str(e)}'}), 500

@app.route('/api/database/stats', methods=['GET'])
def get_database_stats():
    """データベースの統計情報を取得"""
    try:
        db = StockDatabase()
        stats = db.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'データベースエラー: {str(e)}'}), 500

@app.route('/api/database/stock/<ticker>', methods=['GET'])
def get_stock_from_database(ticker):
    """データベースから特定銘柄の分析データを取得"""
    try:
        db = StockDatabase()
        stock_data = db.get_stock_analysis(ticker.upper())
        if stock_data:
            return jsonify(stock_data)
        else:
            return jsonify({'error': f'{ticker}のデータが見つかりません'}), 404
    except Exception as e:
        return jsonify({'error': f'データベースエラー: {str(e)}'}), 500

@app.route('/api/database/stock/<ticker>', methods=['DELETE'])
def delete_stock_from_database(ticker):
    """データベースから特定銘柄を削除"""
    try:
        db = StockDatabase()
        db.delete_stock(ticker.upper())
        return jsonify({'message': f'{ticker}を削除しました'})
    except Exception as e:
        return jsonify({'error': f'データベースエラー: {str(e)}'}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)