#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime
import os

class StockDatabase:
    """株式分析データベースクラス"""
    
    def __init__(self, db_path="stock_analysis.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベースとテーブルを初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 銘柄基本情報テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT UNIQUE NOT NULL,
                company_name TEXT NOT NULL,
                country TEXT,
                currency TEXT,
                current_price REAL,
                market_cap REAL,
                current_dividend_yield REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 年次分析データテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annual_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER,
                year INTEGER,
                total_revenue REAL,
                operating_cash_flow REAL,
                ocf_ratio REAL,
                dividend_amount REAL,
                dividend_yield REAL,
                buyback_amount REAL,
                buyback_yield REAL,
                capex_amount REAL,
                capex_yield REAL,
                debt_issuance REAL,
                debt_repayment REAL,
                roi REAL,
                total_return_without_capex REAL,
                total_return_with_capex REAL,
                net_income REAL,
                total_assets REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_id) REFERENCES stocks (id)
            )
        ''')
        
        # インデックス作成
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON stocks(ticker)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_year ON annual_data(stock_id, year)')
        
        conn.commit()
        conn.close()
    
    def save_stock_analysis(self, analysis_data):
        """分析データをデータベースに保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 銘柄基本情報を保存または更新
            cursor.execute('''
                INSERT OR REPLACE INTO stocks 
                (ticker, company_name, country, currency, current_price, market_cap, current_dividend_yield, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis_data['ticker'],
                analysis_data['company_name'],
                analysis_data.get('country', 'N/A'),
                analysis_data.get('currency', 'USD'),
                analysis_data['current_price'],
                analysis_data['market_cap'],
                analysis_data['current_dividend_yield'],
                datetime.now()
            ))
            
            # 銘柄IDを取得
            cursor.execute('SELECT id FROM stocks WHERE ticker = ?', (analysis_data['ticker'],))
            stock_id = cursor.fetchone()[0]
            
            # 既存の年次データを削除（更新のため）
            cursor.execute('DELETE FROM annual_data WHERE stock_id = ?', (stock_id,))
            
            # 年次データを保存
            for return_data in analysis_data['total_returns']['annual_returns']:
                year = return_data['year']
                
                # 対応する年度の各種データを取得
                revenue_data = None
                if analysis_data.get('revenue_cashflow_data'):
                    revenue_data = next((r for r in analysis_data['revenue_cashflow_data']['annual_data'] if r['year'] == year), None)
                
                buyback_data = None
                if analysis_data.get('buyback_yields'):
                    buyback_data = next((b for b in analysis_data['buyback_yields']['annual_yields'] if b['year'] == year), None)
                
                capex_data = None
                if analysis_data.get('capex_yields'):
                    capex_data = next((c for c in analysis_data['capex_yields']['annual_yields'] if c['year'] == year), None)
                
                debt_issuance_data = None
                debt_repayment_data = None
                if analysis_data.get('debt_data'):
                    debt_issuance_data = next((d for d in analysis_data['debt_data']['issuance']['annual_data'] if d['year'] == year), None)
                    debt_repayment_data = next((d for d in analysis_data['debt_data']['repayment']['annual_data'] if d['year'] == year), None)
                
                roi_data = None
                if analysis_data.get('roi_data'):
                    roi_data = next((r for r in analysis_data['roi_data']['annual_data'] if r['year'] == year), None)
                
                cursor.execute('''
                    INSERT INTO annual_data (
                        stock_id, year, total_revenue, operating_cash_flow, ocf_ratio,
                        dividend_amount, dividend_yield, buyback_amount, buyback_yield,
                        capex_amount, capex_yield, debt_issuance, debt_repayment, roi,
                        total_return_without_capex, total_return_with_capex,
                        net_income, total_assets
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock_id,
                    year,
                    revenue_data['total_revenue'] if revenue_data else 0,
                    revenue_data['operating_cash_flow'] if revenue_data else 0,
                    revenue_data['ocf_ratio'] if revenue_data else 0,
                    return_data['dividend_amount'],
                    return_data['dividend_yield'],
                    buyback_data['amount'] if buyback_data else 0,
                    return_data['buyback_yield'],
                    capex_data['amount'] if capex_data else 0,
                    capex_data['yield'] if capex_data else 0,
                    debt_issuance_data['amount'] if debt_issuance_data else 0,
                    debt_repayment_data['amount'] if debt_repayment_data else 0,
                    roi_data['roi'] if roi_data else 0,
                    return_data.get('total_return_without_capex', 0),
                    return_data.get('total_return_with_capex', return_data['total_return']),
                    roi_data['net_income'] if roi_data else 0,
                    roi_data['total_assets'] if roi_data else 0
                ))
            
            conn.commit()
            print(f"✅ {analysis_data['ticker']} のデータをデータベースに保存しました")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ データベース保存エラー: {e}")
            raise
        finally:
            conn.close()
    
    def get_all_stocks(self):
        """保存されている全銘柄を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ticker, company_name, country, current_price, market_cap, 
                   current_dividend_yield, last_updated
            FROM stocks 
            ORDER BY last_updated DESC
        ''')
        
        columns = ['ticker', 'company_name', 'country', 'current_price', 
                  'market_cap', 'current_dividend_yield', 'last_updated']
        stocks = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return stocks
    
    def get_stock_analysis(self, ticker):
        """特定銘柄の分析データを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 銘柄基本情報を取得
        cursor.execute('SELECT * FROM stocks WHERE ticker = ?', (ticker,))
        stock_row = cursor.fetchone()
        
        if not stock_row:
            conn.close()
            return None
        
        # 年次データを取得
        cursor.execute('''
            SELECT * FROM annual_data 
            WHERE stock_id = (SELECT id FROM stocks WHERE ticker = ?)
            ORDER BY year DESC
        ''', (ticker,))
        
        annual_rows = cursor.fetchall()
        conn.close()
        
        if not annual_rows:
            return None
        
        # データを構造化
        stock_data = {
            'ticker': stock_row[1],
            'company_name': stock_row[2],
            'country': stock_row[3],
            'currency': stock_row[4],
            'current_price': stock_row[5],
            'market_cap': stock_row[6],
            'current_dividend_yield': stock_row[7],
            'last_updated': stock_row[8],
            'annual_data': []
        }
        
        for row in annual_rows:
            annual_data = {
                'year': row[2],
                'total_revenue': row[3],
                'operating_cash_flow': row[4],
                'ocf_ratio': row[5],
                'dividend_amount': row[6],
                'dividend_yield': row[7],
                'buyback_amount': row[8],
                'buyback_yield': row[9],
                'capex_amount': row[10],
                'capex_yield': row[11],
                'debt_issuance': row[12],
                'debt_repayment': row[13],
                'roi': row[14],
                'total_return_without_capex': row[15],
                'total_return_with_capex': row[16],
                'net_income': row[17],
                'total_assets': row[18]
            }
            stock_data['annual_data'].append(annual_data)
        
        return stock_data
    
    def delete_stock(self, ticker):
        """銘柄をデータベースから削除"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 年次データを削除
            cursor.execute('''
                DELETE FROM annual_data 
                WHERE stock_id = (SELECT id FROM stocks WHERE ticker = ?)
            ''', (ticker,))
            
            # 銘柄基本情報を削除
            cursor.execute('DELETE FROM stocks WHERE ticker = ?', (ticker,))
            
            conn.commit()
            print(f"✅ {ticker} をデータベースから削除しました")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ データベース削除エラー: {e}")
            raise
        finally:
            conn.close()
    
    def get_database_stats(self):
        """データベースの統計情報を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM stocks')
        stock_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM annual_data')
        annual_data_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT country) FROM stocks')
        country_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT MAX(last_updated) FROM stocks')
        last_updated = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'stock_count': stock_count,
            'annual_data_count': annual_data_count,
            'country_count': country_count,
            'last_updated': last_updated
        }