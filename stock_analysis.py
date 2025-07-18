#!/usr/bin/env python3
import yfinance as yf
import requests
import json
from datetime import datetime, timedelta
import pandas as pd

class StockAnalyzer:
    """株式の配当と自社株買いを分析するクラス"""
    
    def __init__(self):
        pass
    
    def get_stock_data(self, ticker):
        """ティッカーコードから株式データを取得"""
        try:
            # 国際株対応: .JKなどのサフィックス自動検索
            possible_tickers = [ticker, f"{ticker}.JK", f"{ticker}.T", f"{ticker}.L", f"{ticker}.HK"]
            
            stock = None
            working_ticker = ticker
            
            for test_ticker in possible_tickers:
                try:
                    test_stock = yf.Ticker(test_ticker)
                    test_info = test_stock.info
                    if test_info.get('longName') or test_info.get('shortName'):
                        stock = test_stock
                        working_ticker = test_ticker
                        break
                except:
                    continue
            
            if not stock:
                stock = yf.Ticker(ticker)
                
            info = stock.info
            
            # 基本情報を取得
            market_cap = info.get('marketCap', 0)
            current_price = info.get('currentPrice', 0)
            shares_outstanding = info.get('sharesOutstanding', 0)
            
            # 配当情報
            dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
            dividend_rate = info.get('dividendRate', 0)
            
            return {
                'ticker': working_ticker,  # 実際に使用されたティッカー
                'original_ticker': ticker,  # 元のティッカー
                'company_name': info.get('longName', 'N/A'),
                'market_cap': market_cap,
                'current_price': current_price,
                'shares_outstanding': shares_outstanding,
                'dividend_yield': dividend_yield,
                'dividend_rate': dividend_rate,
                'country': info.get('country', 'N/A'),
                'currency': info.get('currency', 'USD'),
                'info': info
            }
        except Exception as e:
            print(f"エラー: {ticker}のデータ取得に失敗しました - {e}")
            return None
    
    def get_financial_statements(self, ticker):
        """財務諸表から自社株買い情報を取得"""
        try:
            stock = yf.Ticker(ticker)
            
            # キャッシュフロー計算書を取得
            cashflow = stock.cashflow
            
            if cashflow is not None and not cashflow.empty:
                print(f"  キャッシュフロー計算書の利用可能な期間:")
                print(f"    カラム数: {len(cashflow.columns)}")
                print(f"    期間: {cashflow.columns.tolist()}")
                
                # 自社株買い（Repurchase Of Stock）を探す
                repurchase_keys = [
                    'Repurchase Of Capital Stock',
                    'Repurchase Of Stock',
                    'Purchase Of Stock', 
                    'Common Stock Repurchased',
                    'Stock Repurchased',
                    'Purchase of Stock'
                ]
                
                repurchase_data = {
                    'latest': 0,
                    'three_year_avg': 0,
                    'annual_data': []
                }
                
                found_key = None
                for key in repurchase_keys:
                    if key in cashflow.index:
                        found_key = key
                        
                        # 過去3年分のデータを取得
                        annual_amounts = []
                        print(f"  '{key}' の過去3年のデータ:")
                        
                        for i, (date, value) in enumerate(cashflow.loc[key].items()):
                            if i < 3:  # 過去3年分
                                if pd.notna(value):
                                    amount = abs(value)
                                    annual_amounts.append(amount)
                                    repurchase_data['annual_data'].append({
                                        'year': date.year,
                                        'amount': amount
                                    })
                                    print(f"    {date.year}: ${amount:,.0f}")
                                else:
                                    print(f"    {date.year}: データなし")
                        
                        if annual_amounts:
                            repurchase_data['latest'] = annual_amounts[0]  # 最新年
                            repurchase_data['three_year_avg'] = sum(annual_amounts) / len(annual_amounts)
                            
                            print(f"  → 最新年: ${repurchase_data['latest']:,.0f}")
                            print(f"  → 3年平均: ${repurchase_data['three_year_avg']:,.0f}")
                        
                        break
                
                return repurchase_data
            
            return {'latest': 0, 'three_year_avg': 0, 'annual_data': []}
            
        except Exception as e:
            print(f"財務データの取得に失敗: {e}")
            return {'latest': 0, 'three_year_avg': 0, 'annual_data': []}
    
    def get_dividend_history(self, ticker):
        """過去3年分の配当履歴を取得"""
        try:
            stock = yf.Ticker(ticker)
            
            # キャッシュフロー計算書から配当支払額を取得
            cashflow = stock.cashflow
            
            dividend_data = {'annual_data': []}
            
            if cashflow is not None and not cashflow.empty:
                print(f"  配当履歴の取得:")
                
                # 配当支払い項目を探す
                dividend_keys = [
                    'Cash Dividends Paid',
                    'Common Stock Dividend Paid',
                    'Dividends Paid'
                ]
                
                found_key = None
                for key in dividend_keys:
                    if key in cashflow.index:
                        found_key = key
                        print(f"    項目: '{key}' を使用")
                        
                        # 過去3年分の配当データを取得
                        for i, (date, value) in enumerate(cashflow.loc[key].items()):
                            if i < 3:  # 過去3年分
                                if pd.notna(value):
                                    dividend_amount = abs(value)  # 配当は負の値で記録されるため絶対値
                                    dividend_data['annual_data'].append({
                                        'year': date.year,
                                        'amount': dividend_amount
                                    })
                                    print(f"    {date.year}: ${dividend_amount:,.0f}")
                        break
                
                if not found_key:
                    print(f"    配当データが見つかりませんでした")
                    # フォールバック: 現在の配当レートを使用
                    current_info = stock.info
                    current_dividend = current_info.get('dividendRate', 0)
                    shares_outstanding = current_info.get('sharesOutstanding', 0)
                    
                    if current_dividend > 0 and shares_outstanding > 0:
                        estimated_annual_dividend = current_dividend * shares_outstanding
                        print(f"    フォールバック: 現在配当レート ${current_dividend} × 発行済株式数 {shares_outstanding:,.0f}")
                        print(f"    推定年間配当総額: ${estimated_annual_dividend:,.0f}")
                        
                        # 過去3年分に同じ値を設定（推定）
                        for year in [2024, 2023, 2022]:
                            dividend_data['annual_data'].append({
                                'year': year,
                                'amount': estimated_annual_dividend
                            })
            
            return dividend_data
            
        except Exception as e:
            print(f"配当データの取得に失敗: {e}")
            return {'annual_data': []}
    
    def calculate_dividend_yield(self, stock_data):
        """配当利回りを計算"""
        dividend_rate = stock_data.get('dividend_rate', 0)
        current_price = stock_data.get('current_price', 0)
        
        if current_price > 0 and dividend_rate > 0:
            return (dividend_rate / current_price) * 100
        else:
            # フォールバックとしてYahoo Financeの値を使用
            dividend_yield = stock_data.get('dividend_yield', 0)
            return dividend_yield if dividend_yield < 100 else 0
    
    def calculate_buyback_equivalent_yield(self, stock_data, repurchase_data):
        """自社株買い相当配当率を計算（過去3年分個別）"""
        market_cap = stock_data.get('market_cap', 0)
        
        if market_cap == 0:
            return {'annual_yields': []}
        
        annual_yields = []
        
        # 計算詳細を表示
        print(f"  自社株買い相当利回り計算:")
        print(f"    現在の時価総額: ${market_cap:,.0f}")
        print(f"")
        
        for data in repurchase_data['annual_data']:
            year = data['year']
            amount = data['amount']
            yield_rate = (amount / market_cap) * 100
            
            annual_yields.append({
                'year': year,
                'amount': amount,
                'yield': yield_rate
            })
            
            print(f"    {year}年: ${amount:,.0f} ÷ ${market_cap:,.0f} × 100 = {yield_rate:.2f}%")
        
        return {'annual_yields': annual_yields}
    
    def calculate_total_shareholder_return(self, market_cap, dividend_data, buyback_yields):
        """総合株主還元率を計算（過去3年分個別）"""
        annual_returns = []
        
        for buyback_data in buyback_yields['annual_yields']:
            year = buyback_data['year']
            
            # その年の配当データを探す
            dividend_amount = 0
            for div_data in dividend_data['annual_data']:
                if div_data['year'] == year:
                    dividend_amount = div_data['amount']
                    break
            
            # 配当利回りを計算
            dividend_yield = (dividend_amount / market_cap) * 100 if market_cap > 0 else 0
            
            total_return = dividend_yield + buyback_data['yield']
            annual_returns.append({
                'year': year,
                'dividend_amount': dividend_amount,
                'dividend_yield': dividend_yield,
                'buyback_yield': buyback_data['yield'],
                'total_return': total_return
            })
        
        return {'annual_returns': annual_returns}
    
    def analyze_stock(self, ticker):
        """株式の総合分析を実行"""
        print(f"\n=== {ticker} 株主還元分析 ===")
        
        # 基本データ取得
        stock_data = self.get_stock_data(ticker)
        if not stock_data:
            return None
        
        # 自社株買い情報取得
        repurchase_data = self.get_financial_statements(ticker)
        
        # 配当履歴取得
        dividend_data = self.get_dividend_history(ticker)
        
        # 各種利回り計算
        current_dividend_yield = self.calculate_dividend_yield(stock_data)
        buyback_yields = self.calculate_buyback_equivalent_yield(stock_data, repurchase_data)
        total_returns = self.calculate_total_shareholder_return(stock_data['market_cap'], dividend_data, buyback_yields)
        
        # 結果表示
        print(f"\n=== 基本情報 ===")
        print(f"企業名: {stock_data['company_name']}")
        print(f"ティッカー: {stock_data['ticker']} (入力: {stock_data['original_ticker']})")
        print(f"国: {stock_data['country']}")
        print(f"通貨: {stock_data['currency']}")
        print(f"現在株価: {stock_data['current_price']:.2f} {stock_data['currency']}")
        print(f"時価総額: {stock_data['market_cap']:,} {stock_data['currency']}")
        print(f"現在の年間配当額: {stock_data['dividend_rate']:.2f} {stock_data['currency']}")
        print(f"現在の配当利回り: {current_dividend_yield:.2f}%")
        
        print(f"\n=== 過去3年間の詳細分析 ===")
        
        for return_data in total_returns['annual_returns']:
            year = return_data['year']
            dividend_amount = return_data['dividend_amount']
            div_yield = return_data['dividend_yield']
            buyback_yield = return_data['buyback_yield']
            total = return_data['total_return']
            
            # その年の自社株買い額を取得
            buyback_amount = 0
            for buyback_data in buyback_yields['annual_yields']:
                if buyback_data['year'] == year:
                    buyback_amount = buyback_data['amount']
                    break
            
            print(f"\n【{year}年度】")
            print(f"  配当:")
            print(f"    年間配当総額: ${dividend_amount:,.0f}")
            print(f"    配当利回り: {div_yield:.2f}%")
            print(f"    計算根拠: ${dividend_amount:,.0f} ÷ ${stock_data['market_cap']:,.0f} × 100")
            print(f"  自社株買い:")
            print(f"    自社株買い額: ${buyback_amount:,.0f}")
            print(f"    自社株買い相当利回り: {buyback_yield:.2f}%")
            print(f"    計算根拠: ${buyback_amount:,.0f} ÷ ${stock_data['market_cap']:,.0f} × 100")
            print(f"  総合:")
            print(f"    総合株主還元率: {div_yield:.2f}% + {buyback_yield:.2f}% = {total:.2f}%")
        
        return {
            'ticker': ticker,
            'company_name': stock_data['company_name'],
            'current_price': stock_data['current_price'],
            'market_cap': stock_data['market_cap'],
            'dividend_rate': stock_data['dividend_rate'],
            'current_dividend_yield': current_dividend_yield,
            'dividend_data': dividend_data,
            'repurchase_data': repurchase_data,
            'buyback_yields': buyback_yields,
            'total_returns': total_returns
        }
    
    def analyze_stock_for_web(self, ticker):
        """Web用の株式分析（出力なし）"""
        # 基本データ取得
        stock_data = self.get_stock_data(ticker)
        if not stock_data:
            return None
        
        # 自社株買い情報取得（出力を抑制）
        repurchase_data = self.get_financial_statements_silent(ticker)
        
        # 配当履歴取得（出力を抑制）
        dividend_data = self.get_dividend_history_silent(ticker)
        
        # 各種利回り計算
        current_dividend_yield = self.calculate_dividend_yield(stock_data)
        buyback_yields = self.calculate_buyback_equivalent_yield_silent(stock_data, repurchase_data)
        total_returns = self.calculate_total_shareholder_return(stock_data['market_cap'], dividend_data, buyback_yields)
        
        return {
            'ticker': ticker,
            'company_name': stock_data['company_name'],
            'current_price': stock_data['current_price'],
            'market_cap': stock_data['market_cap'],
            'dividend_rate': stock_data['dividend_rate'],
            'current_dividend_yield': current_dividend_yield,
            'dividend_data': dividend_data,
            'repurchase_data': repurchase_data,
            'buyback_yields': buyback_yields,
            'total_returns': total_returns
        }
    
    def get_financial_statements_silent(self, ticker):
        """財務諸表から自社株買い情報を取得（出力なし）"""
        try:
            stock = yf.Ticker(ticker)
            cashflow = stock.cashflow
            
            repurchase_data = {
                'latest': 0,
                'three_year_avg': 0,
                'annual_data': []
            }
            
            if cashflow is not None and not cashflow.empty:
                repurchase_keys = [
                    'Repurchase Of Capital Stock',
                    'Repurchase Of Stock',
                    'Purchase Of Stock', 
                    'Common Stock Repurchased',
                    'Stock Repurchased',
                    'Purchase of Stock'
                ]
                
                for key in repurchase_keys:
                    if key in cashflow.index:
                        annual_amounts = []
                        
                        for i, (date, value) in enumerate(cashflow.loc[key].items()):
                            if i < 3:  # 過去3年分
                                if pd.notna(value):
                                    amount = abs(value)
                                    annual_amounts.append(amount)
                                    repurchase_data['annual_data'].append({
                                        'year': date.year,
                                        'amount': amount
                                    })
                        
                        if annual_amounts:
                            repurchase_data['latest'] = annual_amounts[0]
                            repurchase_data['three_year_avg'] = sum(annual_amounts) / len(annual_amounts)
                        
                        break
                
                return repurchase_data
            
            return {'latest': 0, 'three_year_avg': 0, 'annual_data': []}
            
        except Exception as e:
            return {'latest': 0, 'three_year_avg': 0, 'annual_data': []}
    
    def get_dividend_history_silent(self, ticker):
        """過去3年分の配当履歴を取得（出力なし）"""
        try:
            stock = yf.Ticker(ticker)
            cashflow = stock.cashflow
            
            dividend_data = {'annual_data': []}
            
            if cashflow is not None and not cashflow.empty:
                dividend_keys = [
                    'Cash Dividends Paid',
                    'Common Stock Dividend Paid',
                    'Dividends Paid'
                ]
                
                for key in dividend_keys:
                    if key in cashflow.index:
                        for i, (date, value) in enumerate(cashflow.loc[key].items()):
                            if i < 3:  # 過去3年分
                                if pd.notna(value):
                                    dividend_amount = abs(value)
                                    dividend_data['annual_data'].append({
                                        'year': date.year,
                                        'amount': dividend_amount
                                    })
                        break
                
                if not dividend_data['annual_data']:
                    # フォールバック
                    current_info = stock.info
                    current_dividend = current_info.get('dividendRate', 0)
                    shares_outstanding = current_info.get('sharesOutstanding', 0)
                    
                    if current_dividend > 0 and shares_outstanding > 0:
                        estimated_annual_dividend = current_dividend * shares_outstanding
                        
                        for year in [2024, 2023, 2022]:
                            dividend_data['annual_data'].append({
                                'year': year,
                                'amount': estimated_annual_dividend
                            })
            
            return dividend_data
            
        except Exception as e:
            return {'annual_data': []}
    
    def calculate_buyback_equivalent_yield_silent(self, stock_data, repurchase_data):
        """自社株買い相当配当率を計算（出力なし）"""
        market_cap = stock_data.get('market_cap', 0)
        
        if market_cap == 0:
            return {'annual_yields': []}
        
        annual_yields = []
        
        for data in repurchase_data['annual_data']:
            year = data['year']
            amount = data['amount']
            yield_rate = (amount / market_cap) * 100
            
            annual_yields.append({
                'year': year,
                'amount': amount,
                'yield': yield_rate
            })
        
        return {'annual_yields': annual_yields}

def demo():
    """デモ実行関数"""
    analyzer = StockAnalyzer()
    
    print("株主還元率計算プログラム - デモモード")
    print("配当 + 自社株買いによる総合的な株主還元を分析します")
    
    # いくつかの代表的な銘柄で分析をデモ
    demo_tickers = ['AAPL']
    
    for ticker in demo_tickers:
        try:
            print(f"\n{'='*50}")
            result = analyzer.analyze_stock(ticker)
            if result:
                print(f"分析完了: {result['ticker']}")
            print(f"{'='*50}")
        except Exception as e:
            print(f"エラーが発生しました ({ticker}): {e}")

def main():
    """メイン実行関数"""
    analyzer = StockAnalyzer()
    
    print("株主還元率計算プログラム")
    print("配当 + 自社株買いによる総合的な株主還元を分析します")
    
    while True:
        ticker = input("\nティッカーコードを入力してください（終了するには 'quit' と入力）: ").upper().strip()
        
        if ticker == 'QUIT':
            print("プログラムを終了します。")
            break
        
        if not ticker:
            print("有効なティッカーコードを入力してください。")
            continue
        
        try:
            result = analyzer.analyze_stock(ticker)
            if result:
                print(f"\n分析完了: {result['ticker']}")
        except Exception as e:
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    # デモモードで実行
    demo()