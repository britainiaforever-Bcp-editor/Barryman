import os
import shutil
import struct
import sys
import time

VERSION = "3.8.1"
AUTHOR = "Barrythethird's script (BCSFE POP Mod)"

VALID_CATS = {
    0: "Mohawk Cat", 1: "Wall Cat", 2: "Brave Cat", 3: "Sexy Legs Cat", 4: "Giraffe Cat",
    5: "UFO Cat", 6: "Whale Cat", 7: "Dragon Cat", 8: "Mythical Titan Cat",
    23: "Ninja Cat", 24: "Zombie Cat", 25: "Samurai Cat",
    91: "Ice Cat", 92: "Cat Machine", 93: "Greater Demon Cat", 94: "Berserker Cat",
    95: "Baby Cat", 96: "Nurse Cat", 
    134: "Thundia", 135: "Windy", 136: "Kuukuu", 137: "Cohoho", 
    171: "Kaguya", 172: "Jizo", 173: "Grateful Crane", 174: "Momotaro", 
    183: "Cat Kart R"
}

BANNERS = {
    "1": {"name": "The Dynamites (All)", "ids":},
    "2": {"name": "Galaxy Gals (All)", "ids":},
    "3": {"name": "Ultra Souls (All)", "ids":},
    "4": {"name": "Vajiras (JP Excl)", "ids":},
    "5": {"name": "Dragon Emperors (All)", "ids":}
}

BASE_CFG = {
    "1": {"offset": 0x10C, "name": "Cat Wallet"},
    "2": {"offset": 0x108, "name": "Worker Cat Efficiency"},
    "3": {"offset": 0x104, "name": "Cat Base HP"}
}

CONFIG = {
    "catfood": {"offset": 0xA1, "max": 45000, "name": "Cat Food"},
    "xp":       {"offset": 0xB5, "max": 99999999, "name": "XP"},
    "tickets":  {"offset": 0xC2, "max": 299, "name": "Rare Tickets"},
    "g_tickets":{"offset": 0xC8, "max": 299, "name": "Gold Tickets"},
    "flags":    {"offset": 0xD0, "max": 99, "name": "Leadership Flags"}
}

def print_rainbow(text):
    colors = ["\033[31m", "\033[91m", "\033[33m", "\033[32m", "\033[36m", "\033[34m", "\033[35m"]
    for i, c in enumerate(text):
        sys.stdout.write(f"{colors[i % len(colors)]}{c}")
        sys.stdout.flush()
        time.sleep(0.01)
    print("\033[0m")

def patch(file_path, offset, name, val, max_cap=99999999):
    val = min(val, max_cap)
    bak = file_path + ".bak"
    if not os.path.exists(bak):
        shutil.copyfile(file_path, bak)
    with open(file_path, "r+b") as f:
        f.seek(offset)
        f.write(struct.pack("<I", val))
    print(f"[+] Injected {val} into {name}.")

def unlock_cat(file_path, cid):
    patch(file_path, 0x2A0 + (cid * 4), f"Cat ID {cid}", 1, max_cap=1)

def verify_safety(cid, lock=False):
    safe = all(c in VALID_CATS for c in cid) if isinstance(cid, list) else cid in VALID_CATS
    if not safe or lock:
        return input("\n\033[91m[!] This cat might brick your save. Proceed? Y/N: \033[0m").strip().upper() == 'Y'
    return True

def parse_lvl(inp):
    inp = inp.lower().strip()
    if inp == "max+max": return 30
    if "max+" in inp:
        try:
            plus_part = inp.replace("max+", "").strip()
            return min(20 + (int(plus_part) if plus_part.isdigit() else 10), 30)
        except:
            return 30
    if "+" in inp:
        try:
            parts = inp.split("+")
            return min(int(parts) + int(parts), 30)
        except:
            return 20
    return min(int(inp) if inp.isdigit() else 20, 30)

def menu_cats(save_file, region):
    while True:
        print("\n=== ADD CATS ===\n1) By ID\n2) By Banners\n3) By Name\n4) Back")
        ch = input("Choice: ").strip()
        if ch == "1":
            try:
                cid = int(input("Enter Cat ID: "))
                if verify_safety(cid): unlock_cat(save_file, cid)
            except: print("[!] Invalid.")
        elif ch == "2":
            for k, b in BANNERS.items(): print(f"  {k}) {b['name']}")
            b_ch = input("Select Banner: ").strip()
            if b_ch in BANNERS:
                b = BANNERS[b_ch]
                if verify_safety(b["ids"], b_ch == "4" and region != "jp"):
                    for cid in b["ids"]: unlock_cat(save_file, cid)
        elif ch == "3":
            q = input("Search Name: ").strip().lower()
            fid = next((cid for cid, n in VALID_CATS.items() if q in n.lower()), None)
            if fid is not None and verify_safety(fid): unlock_cat(save_file, fid)
            elif verify_safety(-1): print("[*] Canceled.")
        elif ch == "4": break

def menu_upgrades(save_file):
    while True:
        print("\n=== BASE UPGRADES ===\n1) Cat Wallet\n2) Efficiency\n3) Base HP\n4) All")
        sub = input("Choice: ").strip()
        if sub not in ["1", "2", "3", "4"]: return
        if input("Done selecting? (y/n): ").strip().lower() != 'y': continue
        if sub in ["1", "2", "3"]:
            t = BASE_CFG[sub]
            lvl = parse_lvl(input(f"Pattern for {t['name']} (e.g. max+max, 20+5): "))
            patch(save_file, t["offset"], t["name"], lvl, max_cap=30)
            break
        elif sub == "4":
            style = input("Edit levels individually or all at once? (indiv/all): ").strip().lower()
            if style == "all":
                lvl = parse_lvl(input("Enter universal style selection (e.g., max+max): "))
                for t in BASE_CFG.values(): patch(save_file, t["offset"], t["name"], lvl, max_cap=30)
                break
            elif style == "indiv":
                for t in BASE_CFG.values():
                    lvl = parse_lvl(input(f"Enter level for {t['name']}: "))
                    patch(save_file, t["offset"], t["name"], lvl, max_cap=30)
                break

def main():
    print(f"=== {AUTHOR} ===\nVersion: {VERSION}")
    reg = input("Region (en/eu/jp): ").strip().lower()
    save_file = input("Save file name (e.g. main): ").strip()
    if not os.path.exists(save_file):
        print("[!] File not found.")
        return
    while True:
        print(f"\n=== TARGET: {save_file} ===\n1) Cat Food\n2) Max XP\n3) Rare Tickets\n4) Gold Tickets\n5) Leadership\n6) Base Upgrades\n7) Add Cats\n8) Batch Items (1-5)\n9) Restore Backup\n10) Save & Exit")
        ch = input("Select (1-10): ").strip()
        if ch == "1":
            try: patch(save_file, CONFIG["catfood"]["offset"], "Cat Food", int(input("Quantity: ")), CONFIG["catfood"]["max"])
            except: pass
        elif ch == "2": patch(save_file, CONFIG["xp"]["offset"], "XP", CONFIG["xp"]["max"])
        elif ch == "3":
            try: patch(save_file, CONFIG["tickets"]["offset"], "Rare Tickets", int(input("Quantity: ")), CONFIG["tickets"]["max"])
            except: pass
        elif ch == "4": patch(save_file, CONFIG["g_tickets"]["offset"], "Gold Tickets", CONFIG["g_tickets"]["max"])
        elif ch == "5": patch(save_file, CONFIG["flags"]["offset"], "Leadership", CONFIG["flags"]["max"])
        elif ch == "6": menu_upgrades(save_file)
        elif ch == "7": menu_cats(save_file, reg)
        elif ch == "8":
            for m in CONFIG.values(): patch(save_file, m["offset"], m["name"], m["max"])
        elif ch == "9":
            if os.path.exists(save_file + ".bak"):
                shutil.copyfile(save_file + ".bak", save_file)
                print("[+] Restored.")
        elif ch == "10":
            print_rainbow("Thanks for using Bcp editor!")
            break

if __name__ == "__main__":
    main()
          
