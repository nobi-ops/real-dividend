from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sys
import os

# 既存のStockAnalyzerクラスをインポート
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from stock_analysis import StockAnalyzer

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)