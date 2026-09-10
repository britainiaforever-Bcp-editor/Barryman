import os
import shutil
import struct
import sys
import time

VERSION = "3.10.0"

# Verified Database mapping ALL native Cat IDs inside Battle Cats POP! on the 3DS
# Max character registry ID cap is 183. Anything higher breaks save layout structures.
VALID_CATS = {
    # Normal Cats
    0: "Mohawk Cat", 1: "Wall Cat", 2: "Brave Cat", 3: "Sexy Legs Cat", 4: "Giraffe Cat",
    5: "UFO Cat", 6: "Whale Cat", 7: "Dragon Cat", 8: "Mythical Titan Cat",
    # Special / EX Units
    9: "Ninja Cat", 10: "Sumo Cat", 11: "Knight Cat", 12: "Devil Cat", 13: "Cat Gang",
    14: "Samba Cat", 15: "Bondage Cat", 16: "Executioner Cat", 17: "Zombie Cat",
    18: "Laser Cat", 19: "Dom Cat", 20: "Kung Fu Cat", 21: "Crazed Yuki",
    22: "Valkyrie Cat", 23: "Awakened Valkyrie", 24: "Crazed Bahamut Cat",
    25: "Bean Cats", 26: "Moneko", 27: "Bicycle Cat", 28: "Cat Kart R",
    # Rare Units
    29: "Paisen Cat", 30: "Solar Cat", 31: "Paris Cat", 32: "Jurassic Cat", 33: "Thor Cat",
    34: "Captain Cat", 35: "Phantom Thief Cat", 36: "Monk Cat", 37: "Fisherman Cat",
    38: "Necromancer Cat", 39: "Sorceress Cat", 40: "Archer Cat", 41: "Swordsman Cat",
    42: "Cat Gunslinger", 43: "Stilts Cat", 44: "Tin Cat", 45: "Rocker Cat", 46: "Mer-Cat",
    47: "Psychocat", 48: "Onmyoji Cat",
    # Super Rare Units
    49: "Dancing Flasher Cat", 50: "Fried Chicken Cat", 51: "Delinquent Cat",
    52: "Avalokitesvara Cat", 53: "Drama Cats", 54: "Cat Projector", 55: "Castaway Cat",
    # Crazed Variants
    56: "Crazed Cat", 57: "Crazed Tank Cat", 58: "Crazed Axe Cat", 59: "Crazed Gross Cat",
    60: "Crazed Cow Cat", 61: "Crazed Bird Cat", 62: "Crazed Fish Cat", 63: "Crazed Lizard Cat",
    64: "Crazed Titan Cat",
    # The Dynamites Uber Banners
    91: "Ice Cat", 92: "Cat Machine", 93: "Greater Demon Cat", 94: "Berserker Cat",
    95: "Baby Cat", 96: "Nurse Cat",
    # Sengoku Wargods Vajiras
    102: "Sanada Yukimura", 103: "Maeda Keiji", 104: "Oda Nobunaga",
    105: "Date Masamune", 106: "Takeda Shingen", 107: "Uesugi Kenshin",
    # Lords of Destruction: Dragon Emperors
    124: "Megidora", 125: "Sodom", 126: "Vars", 127: "Kamukura", 128: "Raiden", 129: "Dioramos",
    # Cyber Academy: Galaxy Gals
    134: "Thundia", 135: "Windy", 136: "Kuukuu", 137: "Cohoho", 138: "Myrcia",
    # Ancient Heroes: Ultra Souls
    171: "Kaguya", 172: "Jizo", 173: "Grateful Crane", 174: "Momotaro", 175: "Urashima Taro",
    183: "Cat Kart R (Special Drop)"
}

# Rarity Groups mapped precisely according to early engine structural boundaries
RARITY_MAP = {
    "normal": list(range(0, 9)),
    "special": list(range(9, 29)),
    "rare": list(range(29, 49)),
    "super_rare": list(range(49, 65)),
    "uber": list(range(91, 97)) + list(range(102, 108)) + list(range(124, 130)) + list(range(134, 139)) + list(range(171, 176))
}

BANNERS = {
    "1": {"name": "The Dynamites", "ids": list(range(91, 97))},
    "2": {"name": "Cyber Academy: Galaxy Gals", "ids": list(range(134, 139))},
    "3": {"name": "Ancient Heroes: Ultra Souls", "ids": list(range(171, 176))},
    "4": {"name": "Sengoku Wargods Vajiras (JP Excl)", "ids": list(range(102, 108))},
    "5": {"name": "Lords of Destruction: Dragon Emperors", "ids": list(range(124, 130))}
}

BASE_CFG = {
    "1": {"offset": 0x10C, "name": "Cat Wallet"},
    "2": {"offset": 0x108, "name": "Worker Cat Efficiency"},
    "3": {"offset": 0x104, "name": "Cat Base HP"},
    "4": {"offset": 0x100, "name": "Cat Cannon Power"},
    "5": {"offset": 0x0FC, "name": "Cat Cannon Range"},
    "6": {"offset": 0x0F8, "name": "Cat Cannon Charge Time"},
    "7": {"offset": 0x0F4, "name": "Study (XP Boost)"},
    "8": {"offset": 0x0F0, "name": "Accountant (Start Money)"},
    "9": {"offset": 0x0EC, "name": "Health Up"},
    "10": {"offset": 0x0E8, "name": "Research (Recharge Speed)"}
}

CONFIG = {
    "catfood": {"offset": 0xA1, "max": 45000, "name": "Cat Food"},
    "xp":       {"offset": 0xB5, "max": 99999999, "name": "XP"},
    "tickets":  {"offset": 0xC2, "max": 299, "name": "Rare Tickets"},
    "g_tickets":{"offset": 0xC8, "max": 299, "name": "Gold Tickets"},
    "flags":    {"offset": 0xD0, "max": 99, "name": "Leadership Flags"}
}

def print_credits():
    orange = "\033[38;5;208m"
    reset = "\033[0m"
    print("\n=======================================================")
    print(" CREDITS PANEL ")
    print("=======================================================")
    print(" Lead Developer: Barrythethird")
    print(f" {orange}Contributor:{reset} salomao67")
    print("=======================================================")

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
            return min(int(parts[0]) + int(parts[1]), 30)
        except:
            return 20
    try:
        val = int(inp)
        if val > 30:
            print("[!] Level out of bounds. Applying maximum possible level configuration limit.")
            return 30
        return min(val, 30)
    except:
        return 20

def get_currently_owned_cats(file_path):
    owned = []
    if not os.path.exists(file_path): return owned
    with open(file_path, "rb") as f:
        for cid in VALID_CATS.keys():
            f.seek(0x2A0 + (cid * 4))
            data = f.read(4)
            if data and struct.unpack("<I", data)[0] == 1:
                owned.append(cid)
    return owned

def apply_cat_level(file_path, cid, lvl):
    level_base_offset = 0x000600
    patch(file_path, level_base_offset + (cid * 4), f"Cat ID {cid} Level", lvl, max_cap=30)

def menu_cats(save_file, region):
    while True:
        print("\n=== ADD CATS ===\n1) By ID\n2) By Banners\n3) By Name\n4) Add All Cats\n5) Back")
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
        elif ch == "4":
            jp_ids = [102, 103, 104, 105, 106, 107]
            if verify_safety(list(VALID_CATS.keys())):
                print("[*] Processing full roster batch loops...")
                for cid in VALID_CATS.keys():
                    if cid in jp_ids:
                        if region == "jp": unlock_cat(save_file, cid)
                    else:
                        unlock_cat(save_file, cid)
                print("[+] Roster generated successfully.")
        elif ch == "5": break

def menu_upgrade_cats(save_file):
    while True:
        print("\n=== UPGRADE CATS ===")
        print("1) Upgrade cats by rarity\n2) Upgrade cats by name\n3) Upgrade cats by ID\n4) Upgrade currently owned cats\n5) Upgrade all cats\n6) Back")
        ch = input("Choice: ").strip()
        if ch == "6": break
        if ch not in ["1", "2", "3", "4", "5"]: continue
        
        target_cats = []
        if ch == "1":
            print("\nRarities: normal | special | rare | super_rare | uber")
            r = input("Select target rarity group string: ").strip().lower()
            if r in RARITY_MAP: target_cats = RARITY_MAP[r]
            else: print("[!] Unknown group.")
        elif ch == "2":
            q = input("Search Cat Name string: ").strip().lower()
            target_cats = [cid for cid, n in VALID_CATS.items() if q in n.lower()]
            for cid in target_cats: print(f" -> Found match: {VALID_CATS[cid]} (ID {cid})")
        elif ch == "3":
            try:
                cid = int(input("Enter Cat ID to configure: "))
                if cid in VALID_CATS: target_cats = [cid]
            except: print("[!] Invalid format.")
        elif ch == "4":
            target_cats = get_currently_owned_cats(save_file)
            print(f"[*] Identified {len(target_cats)} unlocked units sitting inside data buffers.")
        elif ch == "5":
            target_cats = list(VALID_CATS.keys())

        if not target_cats:
            print("[!] No active characters match entry settings.")
            continue

        if input("\nAre you done selecting cats? Y/N: ").strip().upper() != 'Y': continue
        lvl_input = input("Enter target power tier configuration values (e.g., 20, max+max, 999): ")
        target_level = parse_lvl(lvl_input)
        
        print(f"[*] Applying matrix write operations to {len(target_cats)} units...")
        for cid in target_cats:
            apply_cat_level(save_file, cid, target_level)
        print("[+] Level modifications written into active binary segment streams.")
        break

def menu_upgrades(save_file):
    while True:
        print("\n=== BASE UPGRADES ===")
        print("1) Cat Wallet\n2) Efficiency\n3) Base HP\n4) Cannon Power\n5) Cannon Range")
        print("6) Charge Time\n7) Study\n8) Accountant\n9) Health Up\n10) Research\n11) All\n12) Back")
        sub = input("Choice: ").strip()
        if sub == "12": break
        if sub not in [str(i) for i in range(1, 13)]: return
        if input("Done selecting? (y/n): ").strip().lower() != 'y': continue
        
        if sub in [str(i) for i in range(1, 11)]:
            t = BASE_CFG[sub]
            lvl = parse_lvl(input(f"Pattern for {t['name']} (e.g. max+max, 20+5): "))
            patch(save_file, t["offset"], t["name"], lvl, max_cap=30)
            break
        elif sub == "11":
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
    print(f"=======================================================")
    print(f" Barrythethird's script (BCSFE POP Mod) ")
    print(f" Core Engine Terminal Version Framework v3.10.0 ")
    print(f"=======================================================")
    
    reg = input("Region (en/eu/jp): ").strip().lower()
    save_file = input("Save file name (e.g. main, editSaveData.bin): ").strip()
    if not os.path.exists(save_file):
        print("[!] File not found.")
        return
    while True:
        print(f"\n=== TARGET: {save_file} ===\n1) Cat Food\n2) Max XP\n3) Rare Tickets\n4) Gold Tickets\n5) Leadership\n6) Base Upgrades Menu\n7) Add Cats Menu\n8) Upgrade Cats Menu\n9) Batch Items (1-5)\n10) View Credits\n11) Restore Backup\n12) Save & Exit")
        ch = input("Select (1-12): ").strip()
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
        elif ch == "8": menu_upgrade_cats(save_file)
        elif ch == "9":
            for m in CONFIG.values(): patch(save_file, m["offset"], m["name"], m["max"])
        elif ch == "10": print_credits()
        elif ch == "11":
            if os.path.exists(save_file + ".bak"):
                shutil.copyfile(save_file + ".bak", save_file)
                print("[+] Restored.")
        elif ch == "12":
            print_rainbow("Thanks for using Bcp editor!")
            break

if __name__ == "__main__":
    main()
    
          
