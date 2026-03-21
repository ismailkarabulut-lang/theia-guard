import subprocess
import sys

DANGEROUS_COMMANDS = ["rm", "sudo", "dd", "mkfs", "chmod", "chown"]

def ask_approval(command):
    print("\n⚠️  THEIA GUARD - ONAY GEREKİYOR")
    print(f"   Komut: {command}")
    response = input("   Onaylıyor musun? (evet/hayır): ").strip().lower()
    return response == "evet"

def run(command):
    parts = command.strip().split()
    if not parts:
        return

    if parts[0] in DANGEROUS_COMMANDS:
        if not ask_approval(command):
            print("❌ Reddedildi. Komut çalıştırılmadı.")
            return
        print("✅ Onaylandı. Çalıştırılıyor...")
    
    subprocess.run(command, shell=True)

if __name__ == "__main__":
    print("🛡️  Theia Guard aktif. Çıkmak için Ctrl+C")
    while True:
        try:
            cmd = input("\n> ")
            run(cmd)
        except KeyboardInterrupt:
            print("\nTheia Guard kapatıldı.")
            sys.exit(0)
