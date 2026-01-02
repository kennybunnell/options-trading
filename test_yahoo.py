#!/usr/bin/env python3
"""
Test Tradier-based Technical Indicators
"""

from utils.yahoo_finance import test_tradier_indicators

def main():
    print("\n" + "="*70)
    print("Tradier Technical Indicators Test")
    print("="*70 + "\n")
    
    # Test with 5 stocks first
    test_symbols = ['AAPL', 'MSFT', 'NVDA', 'SOFI', 'AMD']
    
    print(f"Testing with {len(test_symbols)} symbols: {', '.join(test_symbols)}")
    print("\nThis may take 30-60 seconds...\n")
    
    results = test_tradier_indicators(test_symbols)
    
    # Show results
    successful = [sym for sym, success in results if success]
    failed = [sym for sym, success in results if not success]
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"✅ Successful: {len(successful)}/{len(test_symbols)}")
    if successful:
        print(f"   {', '.join(successful)}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}/{len(test_symbols)}")
        print(f"   {', '.join(failed)}")
    
    print("\n" + "="*70 + "\n")
    
    if len(successful) == len(test_symbols):
        print("🎉 All tests passed! Tradier indicators are working correctly.")
    elif len(successful) > 0:
        print("⚠️  Partial success. Some symbols failed.")
    else:
        print("❌ All tests failed. Check Tradier API key and connection.")
    
    print()

if __name__ == "__main__":
    main()
