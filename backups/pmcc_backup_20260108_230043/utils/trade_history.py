"""
Tastytrade Transaction History Import
Fetches historical trades and converts them to our data model
"""

import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import uuid
import streamlit as st

from utils.data_models import Trade, StockPosition, data_store


class TradeHistoryImporter:
    """Imports historical trades from Tastytrade API"""
    
    def __init__(self, api):
        """
        Initialize with a TastytradeAPI instance
        
        Args:
            api: TastytradeAPI instance with valid session
        """
        self.api = api
        self.base_url = api.base_url
        self.session_token = api.session_token
    
    def fetch_transactions(self, account_id: str, start_date: str, end_date: str, 
                          page: int = 0, per_page: int = 250) -> Dict:
        """
        Fetch transactions from Tastytrade API
        
        Args:
            account_id: Tastytrade account ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            page: Page number for pagination
            per_page: Results per page (max 250)
        
        Returns:
            API response dict
        """
        url = f'{self.base_url}/accounts/{account_id}/transactions'
        headers = {'Authorization': self.session_token}
        params = {
            'start-date': start_date,
            'end-date': end_date,
            'per-page': per_page,
            'page-offset': page * per_page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching transactions: {response.status_code}")
                return {'data': {'items': []}}
        except Exception as e:
            print(f"Exception fetching transactions: {str(e)}")
            return {'data': {'items': []}}
    
    def fetch_all_transactions(self, account_id: str, start_date: str, end_date: str,
                               progress_callback=None) -> List[Dict]:
        """
        Fetch all transactions with pagination
        
        Args:
            account_id: Tastytrade account ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            progress_callback: Optional callback for progress updates
        
        Returns:
            List of all transaction dicts
        """
        all_transactions = []
        page = 0
        
        while True:
            response = self.fetch_transactions(account_id, start_date, end_date, page)
            items = response.get('data', {}).get('items', [])
            
            if not items:
                break
            
            all_transactions.extend(items)
            
            if progress_callback:
                progress_callback(f"Fetched {len(all_transactions)} transactions...")
            
            # Check if we got less than a full page (last page)
            if len(items) < 250:
                break
            
            page += 1
        
        return all_transactions
    
    def categorize_transaction(self, txn: Dict) -> str:
        """
        Categorize a transaction by type
        
        Returns one of:
        - CSP_OPEN: Sell to Open Put
        - CSP_CLOSE: Buy to Close Put
        - CC_OPEN: Sell to Open Call
        - CC_CLOSE: Buy to Close Call
        - ASSIGNMENT: Put assignment (stock received)
        - EXERCISE: Call exercise (stock called away)
        - STOCK_BUY: Stock purchase
        - STOCK_SELL: Stock sale
        - OTHER: Other transaction type
        """
        action = txn.get('action', '')
        description = txn.get('description', '')
        instrument_type = txn.get('instrument-type', '')
        
        # Handle options
        if instrument_type == 'Equity Option':
            option_type = txn.get('option-type', '')
            
            if action == 'Sell to Open':
                return 'CSP_OPEN' if option_type == 'P' else 'CC_OPEN'
            elif action == 'Buy to Close':
                return 'CSP_CLOSE' if option_type == 'P' else 'CC_CLOSE'
            elif action == 'Buy to Open':
                return 'OTHER'  # Long options not tracked
            elif action == 'Sell to Close':
                return 'OTHER'  # Long options not tracked
        
        # Handle assignments and exercises
        if 'Assignment' in description or 'Assigned' in description:
            return 'ASSIGNMENT'
        if 'Exercise' in description or 'Called' in description:
            return 'EXERCISE'
        
        # Handle stock transactions
        if instrument_type == 'Equity':
            if action == 'Buy':
                return 'STOCK_BUY'
            elif action == 'Sell':
                return 'STOCK_SELL'
        
        return 'OTHER'
    
    def parse_option_symbol(self, symbol: str) -> Dict:
        """
        Parse OCC option symbol to extract components
        
        Example: NVDA  250822P00200000
        - Underlying: NVDA
        - Expiration: 2025-08-22
        - Type: P (Put)
        - Strike: 200.00
        """
        try:
            # Remove spaces and get base symbol
            symbol = symbol.strip()
            
            # Find where the date starts (6 digits after underlying)
            # Format: SYMBOL + spaces + YYMMDD + P/C + Strike*1000
            parts = symbol.split()
            if len(parts) >= 2:
                underlying = parts[0]
                rest = parts[1] if len(parts) > 1 else parts[0][len(underlying):]
            else:
                # Try to find the date pattern
                underlying = ''
                rest = symbol
                for i, char in enumerate(symbol):
                    if char.isdigit():
                        underlying = symbol[:i].strip()
                        rest = symbol[i:]
                        break
            
            if len(rest) >= 15:
                date_str = rest[:6]
                option_type = rest[6]
                strike_str = rest[7:]
                
                # Parse date (YYMMDD)
                year = 2000 + int(date_str[:2])
                month = int(date_str[2:4])
                day = int(date_str[4:6])
                expiration = f"{year}-{month:02d}-{day:02d}"
                
                # Parse strike (remove leading zeros, divide by 1000)
                strike = float(strike_str) / 1000
                
                return {
                    'underlying': underlying,
                    'expiration': expiration,
                    'option_type': option_type,
                    'strike': strike
                }
        except Exception as e:
            print(f"Error parsing option symbol {symbol}: {e}")
        
        return None
    
    def build_trade_from_transaction(self, txn: Dict, category: str, account_id: str) -> Optional[Trade]:
        """
        Build a Trade object from a transaction
        
        Args:
            txn: Transaction dict from API
            category: Transaction category
            account_id: Account ID
        
        Returns:
            Trade object or None
        """
        if category not in ['CSP_OPEN', 'CSP_CLOSE', 'CC_OPEN', 'CC_CLOSE']:
            return None
        
        # Parse the option symbol
        symbol_data = self.parse_option_symbol(txn.get('symbol', ''))
        if not symbol_data:
            # Try to get data from transaction fields directly
            symbol_data = {
                'underlying': txn.get('underlying-symbol', ''),
                'expiration': txn.get('expiration-date', ''),
                'option_type': txn.get('option-type', ''),
                'strike': txn.get('strike-price', 0)
            }
        
        # Determine trade type and action
        trade_type = 'CSP' if 'CSP' in category else 'CC'
        action = 'STO' if 'OPEN' in category else 'BTC'
        
        # Get premium (absolute value, as credits are negative in API)
        net_value = abs(float(txn.get('net-value', 0)))
        quantity = abs(int(float(txn.get('quantity', 1))))
        premium_per_contract = net_value / quantity if quantity > 0 else net_value
        
        # Get trade date
        executed_at = txn.get('executed-at', '')
        trade_date = executed_at[:10] if executed_at else datetime.now().strftime('%Y-%m-%d')
        
        # Generate unique trade ID
        trade_id = str(txn.get('id', uuid.uuid4()))
        
        return Trade(
            trade_id=trade_id,
            account_id=account_id,
            symbol=symbol_data['underlying'],
            trade_type=trade_type,
            action=action,
            strike=float(symbol_data['strike']),
            expiration=symbol_data['expiration'],
            quantity=quantity,
            premium_per_contract=premium_per_contract,
            total_premium=net_value,
            trade_date=trade_date,
            status='OPEN' if action == 'STO' else 'CLOSED',
            tastytrade_order_id=str(txn.get('id', ''))
        )
    
    def match_opens_with_closes(self, trades: List[Trade]) -> List[Trade]:
        """
        Match STO trades with their corresponding BTC trades
        
        Args:
            trades: List of all trades
        
        Returns:
            Updated list of trades with matched status
        """
        # Separate opens and closes
        opens = [t for t in trades if t.action == 'STO']
        closes = [t for t in trades if t.action == 'BTC']
        
        # Sort by date
        opens.sort(key=lambda t: t.trade_date)
        closes.sort(key=lambda t: t.trade_date)
        
        # Match closes to opens (FIFO)
        for close in closes:
            for open_trade in opens:
                if (open_trade.status == 'OPEN' and
                    open_trade.symbol == close.symbol and
                    open_trade.strike == close.strike and
                    open_trade.expiration == close.expiration and
                    open_trade.trade_type == close.trade_type):
                    
                    # Match found - update open trade
                    open_trade.status = 'CLOSED'
                    open_trade.close_date = close.trade_date
                    open_trade.close_price = close.premium_per_contract
                    open_trade.realized_pnl = open_trade.total_premium - close.total_premium
                    break
        
        # Return only STO trades (closes are now merged into opens)
        return opens
    
    def check_for_expirations(self, trades: List[Trade]) -> List[Trade]:
        """
        Mark expired options that weren't closed
        
        Args:
            trades: List of trades
        
        Returns:
            Updated list with expired trades marked
        """
        today = datetime.now().date()
        
        for trade in trades:
            if trade.status == 'OPEN':
                exp_date = datetime.strptime(trade.expiration, '%Y-%m-%d').date()
                if exp_date < today:
                    trade.status = 'EXPIRED'
                    trade.realized_pnl = trade.total_premium  # Full premium kept
        
        return trades
    
    def process_assignments(self, transactions: List[Dict], trades: List[Trade], 
                           account_id: str) -> Tuple[List[Trade], List[StockPosition]]:
        """
        Process assignment transactions and create stock positions
        
        Args:
            transactions: Raw transactions from API
            trades: Processed trades
            account_id: Account ID
        
        Returns:
            Tuple of (updated trades, new stock positions)
        """
        positions = []
        
        for txn in transactions:
            category = self.categorize_transaction(txn)
            
            if category == 'ASSIGNMENT':
                # Find the corresponding CSP trade
                underlying = txn.get('underlying-symbol', '')
                
                # Look for matching open CSP
                for trade in trades:
                    if (trade.trade_type == 'CSP' and 
                        trade.symbol == underlying and
                        trade.status == 'OPEN'):
                        
                        # Mark CSP as assigned
                        trade.status = 'ASSIGNED'
                        
                        # Create stock position
                        # Cost basis = Strike - Premium received per share
                        premium_per_share = trade.premium_per_contract / 100
                        cost_basis = trade.strike - premium_per_share
                        quantity = trade.quantity * 100  # Options = 100 shares
                        
                        position = StockPosition(
                            position_id=str(uuid.uuid4()),
                            account_id=account_id,
                            symbol=underlying,
                            quantity=quantity,
                            cost_basis_per_share=cost_basis,
                            total_cost_basis=cost_basis * quantity,
                            acquisition_date=txn.get('executed-at', '')[:10],
                            acquisition_method='ASSIGNMENT',
                            linked_csp_trade_id=trade.trade_id
                        )
                        positions.append(position)
                        break
            
            elif category == 'EXERCISE':
                # Find the corresponding CC trade and mark as called away
                underlying = txn.get('underlying-symbol', '')
                
                for trade in trades:
                    if (trade.trade_type == 'CC' and 
                        trade.symbol == underlying and
                        trade.status == 'OPEN'):
                        
                        trade.status = 'CALLED_AWAY'
                        break
        
        return trades, positions
    
    def process_stock_purchases(self, transactions: List[Dict], account_id: str) -> List[StockPosition]:
        """
        Process direct stock purchases (not from assignments)
        
        Args:
            transactions: Raw transactions from API
            account_id: Account ID
        
        Returns:
            List of stock positions from purchases
        """
        positions = []
        
        for txn in transactions:
            category = self.categorize_transaction(txn)
            
            if category == 'STOCK_BUY':
                symbol = txn.get('underlying-symbol', txn.get('symbol', ''))
                quantity = abs(int(float(txn.get('quantity', 0))))
                value = abs(float(txn.get('net-value', 0)))
                cost_per_share = value / quantity if quantity > 0 else 0
                
                position = StockPosition(
                    position_id=str(uuid.uuid4()),
                    account_id=account_id,
                    symbol=symbol,
                    quantity=quantity,
                    cost_basis_per_share=cost_per_share,
                    total_cost_basis=value,
                    acquisition_date=txn.get('executed-at', '')[:10],
                    acquisition_method='PURCHASE'
                )
                positions.append(position)
        
        return positions
    
    def import_history(self, account_id: str, start_date: str, end_date: str,
                      progress_callback=None) -> Dict:
        """
        Main import function - fetches and processes all historical trades
        
        Args:
            account_id: Tastytrade account ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            progress_callback: Optional callback for progress updates
        
        Returns:
            Dict with import statistics
        """
        stats = {
            'total_transactions': 0,
            'csp_trades': 0,
            'cc_trades': 0,
            'stock_positions': 0,
            'assignments': 0,
            'expirations': 0,
            'errors': []
        }
        
        try:
            # Step 1: Fetch all transactions
            if progress_callback:
                progress_callback("Fetching transactions from Tastytrade...")
            
            transactions = self.fetch_all_transactions(account_id, start_date, end_date, progress_callback)
            stats['total_transactions'] = len(transactions)
            
            if progress_callback:
                progress_callback(f"Processing {len(transactions)} transactions...")
            
            # Step 2: Build trade objects
            trades = []
            for txn in transactions:
                category = self.categorize_transaction(txn)
                trade = self.build_trade_from_transaction(txn, category, account_id)
                if trade:
                    trades.append(trade)
            
            # Step 3: Match opens with closes
            if progress_callback:
                progress_callback("Matching open and close transactions...")
            trades = self.match_opens_with_closes(trades)
            
            # Step 4: Check for expirations
            trades = self.check_for_expirations(trades)
            
            # Step 5: Process assignments
            if progress_callback:
                progress_callback("Processing assignments and exercises...")
            trades, assigned_positions = self.process_assignments(transactions, trades, account_id)
            
            # Step 6: Process direct stock purchases
            purchased_positions = self.process_stock_purchases(transactions, account_id)
            
            # Combine positions
            all_positions = assigned_positions + purchased_positions
            
            # Step 7: Consolidate positions by symbol (combine multiple purchases)
            consolidated_positions = self.consolidate_positions(all_positions)
            
            # Step 8: Save to data store
            if progress_callback:
                progress_callback("Saving to database...")
            
            # Clear existing data first
            data_store.delete_all_trades()
            data_store.delete_all_positions()
            data_store.delete_all_summaries()
            
            # Save new data
            data_store.save_trades(trades)
            data_store.save_positions(consolidated_positions)
            
            # Recalculate summaries
            data_store.recalculate_summaries()
            
            # Update stats
            stats['csp_trades'] = len([t for t in trades if t.trade_type == 'CSP'])
            stats['cc_trades'] = len([t for t in trades if t.trade_type == 'CC'])
            stats['stock_positions'] = len(consolidated_positions)
            stats['assignments'] = len([t for t in trades if t.status == 'ASSIGNED'])
            stats['expirations'] = len([t for t in trades if t.status == 'EXPIRED'])
            
            if progress_callback:
                progress_callback("Import complete!")
            
        except Exception as e:
            stats['errors'].append(str(e))
            if progress_callback:
                progress_callback(f"Error: {str(e)}")
        
        return stats
    
    def consolidate_positions(self, positions: List[StockPosition]) -> List[StockPosition]:
        """
        Consolidate multiple positions in same symbol into one
        Uses average cost basis
        
        Args:
            positions: List of positions
        
        Returns:
            Consolidated list
        """
        by_symbol = {}
        
        for pos in positions:
            key = (pos.account_id, pos.symbol)
            if key not in by_symbol:
                by_symbol[key] = pos
            else:
                existing = by_symbol[key]
                # Calculate weighted average cost basis
                total_qty = existing.quantity + pos.quantity
                total_cost = existing.total_cost_basis + pos.total_cost_basis
                avg_cost = total_cost / total_qty if total_qty > 0 else 0
                
                existing.quantity = total_qty
                existing.total_cost_basis = total_cost
                existing.cost_basis_per_share = avg_cost
                # Keep earliest acquisition date
                if pos.acquisition_date < existing.acquisition_date:
                    existing.acquisition_date = pos.acquisition_date
        
        return list(by_symbol.values())


def calculate_premium_realization(trade: Trade, current_price: float) -> float:
    """
    Calculate what percentage of premium has been realized for an open position
    
    For a sold option:
    - If current price is lower than sold price, we've "realized" profit
    - Premium Realized % = (Sold Price - Current Price) / Sold Price * 100
    
    Args:
        trade: The open trade
        current_price: Current option price (mid or last)
    
    Returns:
        Percentage of premium realized (0-100+)
    """
    if trade.status != 'OPEN':
        return 100.0  # Closed trades are 100% realized
    
    sold_price = trade.premium_per_contract
    if sold_price <= 0:
        return 0.0
    
    # Premium realized = what we sold for - what it costs to buy back
    realized = sold_price - current_price
    pct = (realized / sold_price) * 100
    
    return max(0, min(100, pct))  # Clamp between 0-100


def get_close_recommendation(premium_realized_pct: float, dte: int) -> str:
    """
    Get recommendation for whether to close a position
    
    Args:
        premium_realized_pct: Percentage of premium realized
        dte: Days to expiration
    
    Returns:
        'CLOSE', 'HOLD', or 'WATCH'
    """
    # Close at 80%+ profit
    if premium_realized_pct >= 80:
        return 'CLOSE'
    
    # Close if near expiration with decent profit
    if dte <= 3 and premium_realized_pct >= 50:
        return 'CLOSE'
    
    # Watch if getting close to target
    if premium_realized_pct >= 60:
        return 'WATCH'
    
    return 'HOLD'