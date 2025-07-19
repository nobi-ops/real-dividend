#!/usr/bin/env python3
import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError

Base = declarative_base()

class Stock(Base):
    """株式基本情報テーブル"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), unique=True, nullable=False)
    company_name = Column(String(200), nullable=False)
    country = Column(String(50))
    currency = Column(String(10))
    current_price = Column(Float)
    market_cap = Column(Float)
    current_dividend_yield = Column(Float)
    last_updated = Column(DateTime, default=datetime.now)
    
    # リレーション
    annual_data = relationship("AnnualData", back_populates="stock", cascade="all, delete-orphan")

class AnnualData(Base):
    """年次分析データテーブル"""
    __tablename__ = 'annual_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    year = Column(Integer, nullable=False)
    total_revenue = Column(Float)
    operating_cash_flow = Column(Float)
    ocf_ratio = Column(Float)
    dividend_amount = Column(Float)
    dividend_yield = Column(Float)
    buyback_amount = Column(Float)
    buyback_yield = Column(Float)
    capex_amount = Column(Float)
    capex_yield = Column(Float)
    debt_issuance = Column(Float)
    debt_repayment = Column(Float)
    roi = Column(Float)
    total_return_without_capex = Column(Float)
    total_return_with_capex = Column(Float)
    net_income = Column(Float)
    total_assets = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    
    # リレーション
    stock = relationship("Stock", back_populates="annual_data")

class PostgreSQLDatabase:
    """PostgreSQL株式分析データベースクラス"""
    
    def __init__(self):
        self.engine = None
        self.Session = None
        self.init_database()
    
    def get_database_url(self):
        """データベースURLを取得（環境変数またはSQLite）"""
        # 本番環境のPostgreSQL URL
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # RenderのPostgreSQL URLは古い形式なので新しい形式に変換
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            print(f"PostgreSQLデータベースに接続中...")
            return database_url
        else:
            # ローカル開発用SQLite
            print(f"SQLiteデータベースを使用...")
            return 'sqlite:///stock_analysis.db'
    
    def init_database(self):
        """データベースとテーブルを初期化"""
        try:
            database_url = self.get_database_url()
            
            # SQLiteの場合のエンジン設定
            if database_url.startswith('sqlite'):
                self.engine = create_engine(database_url, echo=False)
            else:
                # PostgreSQLの場合のエンジン設定
                self.engine = create_engine(
                    database_url,
                    echo=False,
                    pool_pre_ping=True,
                    pool_recycle=300
                )
            
            # テーブル作成
            Base.metadata.create_all(self.engine)
            
            # セッション作成
            self.Session = sessionmaker(bind=self.engine)
            
            print(f"✅ データベース接続成功: {database_url.split('@')[0] if '@' in database_url else 'SQLite'}")
            
        except Exception as e:
            print(f"❌ データベース接続エラー: {e}")
            # フォールバック: SQLite
            self.engine = create_engine('sqlite:///stock_analysis_fallback.db', echo=False)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            print("SQLiteフォールバックデータベースを使用")
    
    def save_stock_analysis(self, analysis_data):
        """分析データをデータベースに保存"""
        session = self.Session()
        
        try:
            # 既存銘柄をチェック
            existing_stock = session.query(Stock).filter_by(ticker=analysis_data['ticker']).first()
            
            if existing_stock:
                # 既存銘柄を更新
                existing_stock.company_name = analysis_data['company_name']
                existing_stock.country = analysis_data.get('country', 'N/A')
                existing_stock.currency = analysis_data.get('currency', 'USD')
                existing_stock.current_price = analysis_data['current_price']
                existing_stock.market_cap = analysis_data['market_cap']
                existing_stock.current_dividend_yield = analysis_data['current_dividend_yield']
                existing_stock.last_updated = datetime.now()
                
                # 既存の年次データを削除
                session.query(AnnualData).filter_by(stock_id=existing_stock.id).delete()
                
                stock = existing_stock
            else:
                # 新規銘柄を作成
                stock = Stock(
                    ticker=analysis_data['ticker'],
                    company_name=analysis_data['company_name'],
                    country=analysis_data.get('country', 'N/A'),
                    currency=analysis_data.get('currency', 'USD'),
                    current_price=analysis_data['current_price'],
                    market_cap=analysis_data['market_cap'],
                    current_dividend_yield=analysis_data['current_dividend_yield'],
                    last_updated=datetime.now()
                )
                session.add(stock)
                session.flush()  # IDを取得するため
            
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
                
                annual_data = AnnualData(
                    stock_id=stock.id,
                    year=year,
                    total_revenue=revenue_data['total_revenue'] if revenue_data else 0,
                    operating_cash_flow=revenue_data['operating_cash_flow'] if revenue_data else 0,
                    ocf_ratio=revenue_data['ocf_ratio'] if revenue_data else 0,
                    dividend_amount=return_data['dividend_amount'],
                    dividend_yield=return_data['dividend_yield'],
                    buyback_amount=buyback_data['amount'] if buyback_data else 0,
                    buyback_yield=return_data['buyback_yield'],
                    capex_amount=capex_data['amount'] if capex_data else 0,
                    capex_yield=capex_data['yield'] if capex_data else 0,
                    debt_issuance=debt_issuance_data['amount'] if debt_issuance_data else 0,
                    debt_repayment=debt_repayment_data['amount'] if debt_repayment_data else 0,
                    roi=roi_data['roi'] if roi_data else 0,
                    total_return_without_capex=return_data.get('total_return_without_capex', 0),
                    total_return_with_capex=return_data.get('total_return_with_capex', return_data['total_return']),
                    net_income=roi_data['net_income'] if roi_data else 0,
                    total_assets=roi_data['total_assets'] if roi_data else 0
                )
                session.add(annual_data)
            
            session.commit()
            print(f"✅ {analysis_data['ticker']} のデータをPostgreSQLに保存しました")
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ PostgreSQLデータベース保存エラー: {e}")
            raise
        finally:
            session.close()
    
    def get_all_stocks(self):
        """保存されている全銘柄を取得"""
        session = self.Session()
        
        try:
            stocks = session.query(Stock).order_by(Stock.last_updated.desc()).all()
            
            result = []
            for stock in stocks:
                result.append({
                    'ticker': stock.ticker,
                    'company_name': stock.company_name,
                    'country': stock.country,
                    'current_price': stock.current_price,
                    'market_cap': stock.market_cap,
                    'current_dividend_yield': stock.current_dividend_yield,
                    'last_updated': stock.last_updated.isoformat() if stock.last_updated else None
                })
            
            return result
            
        except SQLAlchemyError as e:
            print(f"❌ 銘柄取得エラー: {e}")
            return []
        finally:
            session.close()
    
    def get_stock_analysis(self, ticker):
        """特定銘柄の分析データを取得"""
        session = self.Session()
        
        try:
            stock = session.query(Stock).filter_by(ticker=ticker).first()
            
            if not stock:
                return None
            
            annual_data = session.query(AnnualData).filter_by(stock_id=stock.id).order_by(AnnualData.year.desc()).all()
            
            result = {
                'ticker': stock.ticker,
                'company_name': stock.company_name,
                'country': stock.country,
                'currency': stock.currency,
                'current_price': stock.current_price,
                'market_cap': stock.market_cap,
                'current_dividend_yield': stock.current_dividend_yield,
                'last_updated': stock.last_updated.isoformat() if stock.last_updated else None,
                'annual_data': []
            }
            
            for data in annual_data:
                result['annual_data'].append({
                    'year': data.year,
                    'total_revenue': data.total_revenue,
                    'operating_cash_flow': data.operating_cash_flow,
                    'ocf_ratio': data.ocf_ratio,
                    'dividend_amount': data.dividend_amount,
                    'dividend_yield': data.dividend_yield,
                    'buyback_amount': data.buyback_amount,
                    'buyback_yield': data.buyback_yield,
                    'capex_amount': data.capex_amount,
                    'capex_yield': data.capex_yield,
                    'debt_issuance': data.debt_issuance,
                    'debt_repayment': data.debt_repayment,
                    'roi': data.roi,
                    'total_return_without_capex': data.total_return_without_capex,
                    'total_return_with_capex': data.total_return_with_capex,
                    'net_income': data.net_income,
                    'total_assets': data.total_assets
                })
            
            return result
            
        except SQLAlchemyError as e:
            print(f"❌ 銘柄分析データ取得エラー: {e}")
            return None
        finally:
            session.close()
    
    def delete_stock(self, ticker):
        """銘柄をデータベースから削除"""
        session = self.Session()
        
        try:
            stock = session.query(Stock).filter_by(ticker=ticker).first()
            
            if stock:
                session.delete(stock)  # カスケード削除で年次データも削除
                session.commit()
                print(f"✅ {ticker} をPostgreSQLから削除しました")
            else:
                print(f"⚠️ {ticker} が見つかりませんでした")
                
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ 削除エラー: {e}")
            raise
        finally:
            session.close()
    
    def get_database_stats(self):
        """データベースの統計情報を取得"""
        session = self.Session()
        
        try:
            stock_count = session.query(Stock).count()
            annual_data_count = session.query(AnnualData).count()
            
            # 国数を取得
            country_count = session.query(Stock.country).distinct().count()
            
            # 最終更新日を取得
            latest_stock = session.query(Stock).order_by(Stock.last_updated.desc()).first()
            last_updated = latest_stock.last_updated.isoformat() if latest_stock and latest_stock.last_updated else None
            
            return {
                'stock_count': stock_count,
                'annual_data_count': annual_data_count,
                'country_count': country_count,
                'last_updated': last_updated
            }
            
        except SQLAlchemyError as e:
            print(f"❌ 統計情報取得エラー: {e}")
            return {
                'stock_count': 0,
                'annual_data_count': 0,
                'country_count': 0,
                'last_updated': None
            }
        finally:
            session.close()
    
    def export_database(self):
        """データベース全体をJSONファイルとしてエクスポート"""
        session = self.Session()
        
        try:
            stocks = session.query(Stock).order_by(Stock.ticker).all()
            
            export_data = {
                'export_info': {
                    'export_date': datetime.now().isoformat(),
                    'total_stocks': len(stocks),
                    'format_version': '1.0'
                },
                'stocks': []
            }
            
            for stock in stocks:
                annual_data = session.query(AnnualData).filter_by(stock_id=stock.id).order_by(AnnualData.year.desc()).all()
                
                stock_data = {
                    'ticker': stock.ticker,
                    'company_name': stock.company_name,
                    'country': stock.country,
                    'currency': stock.currency,
                    'current_price': stock.current_price,
                    'market_cap': stock.market_cap,
                    'current_dividend_yield': stock.current_dividend_yield,
                    'last_updated': stock.last_updated.isoformat() if stock.last_updated else None,
                    'annual_data': []
                }
                
                for data in annual_data:
                    stock_data['annual_data'].append({
                        'year': data.year,
                        'total_revenue': data.total_revenue,
                        'operating_cash_flow': data.operating_cash_flow,
                        'ocf_ratio': data.ocf_ratio,
                        'dividend_amount': data.dividend_amount,
                        'dividend_yield': data.dividend_yield,
                        'buyback_amount': data.buyback_amount,
                        'buyback_yield': data.buyback_yield,
                        'capex_amount': data.capex_amount,
                        'capex_yield': data.capex_yield,
                        'debt_issuance': data.debt_issuance,
                        'debt_repayment': data.debt_repayment,
                        'roi': data.roi,
                        'total_return_without_capex': data.total_return_without_capex,
                        'total_return_with_capex': data.total_return_with_capex,
                        'net_income': data.net_income,
                        'total_assets': data.total_assets
                    })
                
                export_data['stocks'].append(stock_data)
            
            return export_data
            
        except SQLAlchemyError as e:
            raise Exception(f"エクスポートエラー: {str(e)}")
        finally:
            session.close()
    
    def import_database(self, import_data, clear_existing=False):
        """JSONデータからデータベースをインポート"""
        session = self.Session()
        
        try:
            if clear_existing:
                # 既存データを削除（カスケード削除）
                session.query(Stock).delete()
                session.commit()
                print("既存データを削除しました")
            
            imported_count = 0
            updated_count = 0
            
            for stock_data in import_data.get('stocks', []):
                ticker = stock_data.get('ticker')
                if not ticker:
                    continue
                
                # 既存銘柄をチェック
                existing_stock = session.query(Stock).filter_by(ticker=ticker).first()
                
                if existing_stock:
                    # 既存銘柄を更新
                    existing_stock.company_name = stock_data.get('company_name')
                    existing_stock.country = stock_data.get('country')
                    existing_stock.currency = stock_data.get('currency')
                    existing_stock.current_price = stock_data.get('current_price')
                    existing_stock.market_cap = stock_data.get('market_cap')
                    existing_stock.current_dividend_yield = stock_data.get('current_dividend_yield')
                    if stock_data.get('last_updated'):
                        existing_stock.last_updated = datetime.fromisoformat(stock_data['last_updated'])
                    
                    # 既存の年次データを削除
                    session.query(AnnualData).filter_by(stock_id=existing_stock.id).delete()
                    
                    stock = existing_stock
                    updated_count += 1
                else:
                    # 新規銘柄を追加
                    stock = Stock(
                        ticker=ticker,
                        company_name=stock_data.get('company_name'),
                        country=stock_data.get('country'),
                        currency=stock_data.get('currency'),
                        current_price=stock_data.get('current_price'),
                        market_cap=stock_data.get('market_cap'),
                        current_dividend_yield=stock_data.get('current_dividend_yield'),
                        last_updated=datetime.fromisoformat(stock_data['last_updated']) if stock_data.get('last_updated') else datetime.now()
                    )
                    session.add(stock)
                    session.flush()  # IDを取得するため
                    imported_count += 1
                
                # 年次データをインポート
                for annual_data in stock_data.get('annual_data', []):
                    data = AnnualData(
                        stock_id=stock.id,
                        year=annual_data.get('year'),
                        total_revenue=annual_data.get('total_revenue'),
                        operating_cash_flow=annual_data.get('operating_cash_flow'),
                        ocf_ratio=annual_data.get('ocf_ratio'),
                        dividend_amount=annual_data.get('dividend_amount'),
                        dividend_yield=annual_data.get('dividend_yield'),
                        buyback_amount=annual_data.get('buyback_amount'),
                        buyback_yield=annual_data.get('buyback_yield'),
                        capex_amount=annual_data.get('capex_amount'),
                        capex_yield=annual_data.get('capex_yield'),
                        debt_issuance=annual_data.get('debt_issuance'),
                        debt_repayment=annual_data.get('debt_repayment'),
                        roi=annual_data.get('roi'),
                        total_return_without_capex=annual_data.get('total_return_without_capex'),
                        total_return_with_capex=annual_data.get('total_return_with_capex'),
                        net_income=annual_data.get('net_income'),
                        total_assets=annual_data.get('total_assets')
                    )
                    session.add(data)
            
            session.commit()
            
            return {
                'success': True,
                'imported_count': imported_count,
                'updated_count': updated_count,
                'total_processed': imported_count + updated_count
            }
            
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"インポートエラー: {str(e)}")
        finally:
            session.close()

# 下位互換性のためのエイリアス
StockDatabase = PostgreSQLDatabase