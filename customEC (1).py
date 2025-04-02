import os
import sys
import time
import ccxt
from bit.network import NetworkAPI
from bit import PrivateKey
from bip_utils import (
    Bip39SeedGenerator,
    Bip44,
    Bip44Coins,
    Bip44Changes,
    Bip39MnemonicGenerator,
    Bip39MnemonicValidator,
    Bip39WordsNum,
)

# Constants
WALLETS_FILE_NAME = "bitcoin_wallets_with_balance.txt"
BTC_PRICE_UPDATE_INTERVAL = 3600  # Update BTC price every hour (in seconds)

class BitcoinWalletGenerator:
    def __init__(self):
        self.processed = 0
        self.found = 0
        self.start_time = time.time()
        self.last_price_update = self.start_time
        self.btc_price = 0
        self.total_btc_value = 0.0
        self.exchange = ccxt.binance()  # Using Binance for BTC price data
        self.update_btc_price()  # Initial price update

        # Initialize output file
        open(WALLETS_FILE_NAME, 'a').close()

    def update_btc_price(self):
        """Fetch current BTC price in USD using CCXT"""
        try:
            ticker = self.exchange.fetch_ticker('BTC/USDT')
            self.btc_price = float(ticker['last'])
            self.last_price_update = time.time()
            print(f"\nUpdated BTC price: ${self.btc_price:,.2f}")
        except Exception as e:
            print(f"\nPrice fetch error: {e}")
            self.btc_price = 50000  # Default to $50,000 if API fails

    def generate_secure_mnemonic(self):
        """Generate cryptographically secure BIP39 mnemonic"""
        while True:
            try:
                mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
                Bip39MnemonicValidator().Validate(mnemonic)
                return str(mnemonic)
            except ValueError:
                continue

    def get_btc_address_and_private_key(self, seed):
        """Generate BTC address and private key from seed"""
        bip44_ctx = (
            Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
            .Purpose()
            .Coin()
            .Account(0)
            .Change(Bip44Changes.CHAIN_EXT)
            .AddressIndex(0)
        )
        address = bip44_ctx.PublicKey().ToAddress()
        private_key = bip44_ctx.PrivateKey().ToWif()
        return address, private_key

    def check_btc_balance(self, btc_address):
        """Check BTC balance using NetworkAPI"""
        try:
            return NetworkAPI.get_balance(btc_address) / 1e8
        except Exception as e:
            print(f"\nBTC balance check error for {btc_address}: {e}")
            return 0

    def save_wallet(self, mnemonic, btc_address, private_key, btc_balance, total_usd):
        """Save wallet details to file only if it has balance"""
        if btc_balance > 0:
            with open(WALLETS_FILE_NAME, "a", encoding='utf-8') as f:
                f.write(
                    f"Timestamp: {time.ctime()}\n"
                    f"Seed: {mnemonic}\n"
                    f"BTC Address: {btc_address}\n"
                    f"Private Key (WIF): {private_key}\n"
                    f"BTC Balance: {btc_balance:.8f}\n"
                    f"USD Value: ${total_usd:,.2f}\n"
                    f"{'='*80}\n\n"
                )

    def run(self):
        """Main execution loop"""
        print("BitcoinCracker Pro - Bitcoin Wallet Generator")
        print("Generating BIP39 wallets and checking for balances")
        print("Only saving wallets with positive balances")
        print("Press Ctrl+C to stop\n")
        print("Starting search...\n")

        try:
            while True:
                # Update BTC price periodically
                if time.time() - self.last_price_update > BTC_PRICE_UPDATE_INTERVAL:
                    self.update_btc_price()

                # Generate wallet
                mnemonic = self.generate_secure_mnemonic()
                seed = Bip39SeedGenerator(mnemonic).Generate()
                btc_address, private_key = self.get_btc_address_and_private_key(seed)
                btc_balance = self.check_btc_balance(btc_address)
                total_usd = btc_balance * self.btc_price

                self.processed += 1
                if btc_balance > 0:
                    self.total_btc_value += btc_balance
                    self.found += 1
                    self.save_wallet(mnemonic, btc_address, private_key, btc_balance, total_usd)
                    print(f"\nFOUND WALLET WITH BALANCE! {btc_balance:.8f} BTC (${total_usd:,.2f})")
                    print(f"Address: {btc_address}")
                    print(f"Private Key: {private_key}")
                    print(f"Mnemonic: {mnemonic}\n")

                # Display stats
                elapsed = time.time() - self.start_time
                speed = self.processed / elapsed if elapsed > 0 else 0
                stats = (
                    f"Checked: {self.processed:,} | "
                    f"Found: {self.found:,} | "
                    f"Speed: {speed:.2f} w/s | "
                    f"Elapsed: {time.strftime('%H:%M:%S', time.gmtime(elapsed))}"
                )
                print(stats, end='\r')

        except KeyboardInterrupt:
            print("\n\nStopping gracefully...")
            print(f"Total wallets checked: {self.processed:,}")
            print(f"Wallets with balance found: {self.found:,}")
            print(f"Total BTC found: {self.total_btc_value:.8f}")
            print(f"Total USD value: ${self.total_btc_value * self.btc_price:,.2f}")
            print(f"\nWallets with balance saved to: {WALLETS_FILE_NAME}")

if __name__ == "__main__":
    try:
        wallet_generator = BitcoinWalletGenerator()
        wallet_generator.run()
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)