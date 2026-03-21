import subprocess
import shlex
import json
import hashlib
import datetime
import os
import time
from enum import Enum
from pathlib import Path

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskClassifier:
    # CRITICAL: Sistem genelini etkiler, geri dönüşü yok
    CRITICAL_PATTERNS = [
        "rm -rf /",
        "rm -rf /*",
        "dd if=/dev/zero",
        "dd if=/dev/random",
        "mkfs.ext4 /dev/",
        "mkfs.ntfs /dev/",
        "> /dev/sda",
        "> /dev/nvme",
        "chmod -R 000 /",
        "chown -R root /",
        "rm -rf /home",
        "rm -rf /etc",
        "rm -rf /usr",
        "rm -rf /var",
        "rm -rf /boot",
    ]

    # HIGH: Tehlikeli ama hedefli — onay + ikinci onay
    HIGH_PATTERNS = [
        "rm -rf",
        "rm -r",
        "shred",
        "dd if=",
        "fdisk",
        "mkfs",
        "sudo rm",
        "sudo dd",
        "sudo mkfs",
        "DROP TABLE",
        "DROP DATABASE",
        "DELETE FROM",
        "TRUNCATE",
        "chmod 777",
        "chmod -R 777",
        "> /dev/sda",
    ]

    # MEDIUM: Sistem değiştirir ama geri alınabilir — tek onay
    MEDIUM_PATTERNS = [
        "sudo apt install",
        "sudo apt remove",
        "sudo apt purge",
        "sudo apt upgrade",
        "sudo systemctl stop",
        "sudo systemctl disable",
        "sudo systemctl enable",
        "sudo",
        "su -",
        "apt install",
        "apt remove",
        "apt purge",
        "apt upgrade",
        "pip install",
        "pip uninstall",
        "npm install",
        "npm uninstall",
        "yum install",
        "dnf install",
        "systemctl stop",
        "systemctl disable",
        "UPDATE ",
        "INSERT INTO",
        "mv ",
        "cp -r",
    ]

    # SAFE_PATHS: Bu yollardaki rm komutları HIGH değil MEDIUM
    SAFE_PATHS = ["/tmp/", "/var/tmp/", "/var/cache/", "~/.cache/"]

    def classify(self, command):
        cmd_stripped = command.strip()
        cmd_lower = cmd_stripped.lower()

        # 1. CRITICAL kontrolü — önce en tehlikeliler
        for pattern in self.CRITICAL_PATTERNS:
            if pattern.lower() in cmd_lower:
                return RiskLevel.CRITICAL

        # 2. HIGH kontrolü — ama safe path istisnası var
        for pattern in self.HIGH_PATTERNS:
            if pattern.lower() in cmd_lower:
                # rm -rf /tmp/... gibi güvenli yol istisnası
                if "rm" in cmd_lower:
                    if any(safe in cmd_lower for safe in self.SAFE_PATHS):
                        return RiskLevel.MEDIUM
                return RiskLevel.HIGH

        # 3. MEDIUM kontrolü — daha uzun/spesifik pattern'lar önce
        # sudo apt install gibi kombinasyonları önce yakala
        sorted_medium = sorted(self.MEDIUM_PATTERNS, key=len, reverse=True)
        for pattern in sorted_medium:
            if pattern.lower() in cmd_lower:
                return RiskLevel.MEDIUM

        # 4. Injection riski kontrolü
        if self._has_injection_risk(command):
            return RiskLevel.HIGH

        return RiskLevel.LOW

    def _has_injection_risk(self, command):
        indicators = [
            "; rm", "; sudo", "; dd",
            "&& rm", "&& sudo", "&& dd",
            "|| rm", "|| sudo",
            "| bash", "| sh"
        ]
        return any(ind in command.lower() for ind in indicators)


class SandboxExecutor:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run

    def execute(self, command):
        try:
            parts = shlex.split(command)
            if not parts:
                return {"success": False, "output": "", "error": "Empty command"}
            if self.dry_run:
                return {"success": True, "output": "[DRY RUN] Would execute: " + command, "error": ""}
            needs_interactive = any(x in command for x in ["sudo", "su -"])
            if needs_interactive:
                result = subprocess.run(
                    command,
                    text=True,
                    timeout=120,
                    shell=True
                )
                return {
                    "success": result.returncode == 0,
                    "output": "",
                    "error": ""
                }
            else:
                result = subprocess.run(
                    parts,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    shell=False
                )
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr
                }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": "Timeout (30s)"}
        except FileNotFoundError:
            return {"success": False, "output": "", "error": "Command not found: " + parts[0]}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}


class AuditLog:
    def __init__(self, log_path="theia_guard_log.json"):
        self.log_path = Path(log_path)

    def log(self, command, risk, decision, output=""):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "command": command,
            "risk_level": risk.value,
            "decision": decision,
            "output_summary": output[:200] if output else "",
            "command_hash": hashlib.sha256(command.encode()).hexdigest()[:12]
        }
        entries = []
        if self.log_path.exists():
            try:
                entries = json.loads(self.log_path.read_text())
            except json.JSONDecodeError:
                entries = []
        entries.append(entry)
        self.log_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False))

    def get_stats(self):
        if not self.log_path.exists():
            return {"total": 0}
        entries = json.loads(self.log_path.read_text())
        return {
            "total": len(entries),
            "approved": sum(1 for e in entries if "approved" in e["decision"]),
            "denied": sum(1 for e in entries if e["decision"] == "denied"),
            "high_risk_count": sum(1 for e in entries if e["risk_level"] in ["high", "critical"])
        }


class ApprovalGate:
    def __init__(self, dry_run=False):
        self.classifier = RiskClassifier()
        self.executor = SandboxExecutor(dry_run=dry_run)
        self.audit = AuditLog()
        self.use_telegram = (
            os.environ.get("TELEGRAM_BOT_TOKEN") is not None or
            Path(".env").exists()
        )

    def process(self, command):
        risk = self.classifier.classify(command)

        print("")
        print("=" * 50)
        print("THEIA GUARD")
        print("=" * 50)
        print("Komut:      " + command)
        print("Risk:       " + risk.value.upper())
        print("=" * 50)

        if risk == RiskLevel.LOW:
            print("Dusuk risk. Otomatik calistiriliyor...")
            result = self.executor.execute(command)
            self.audit.log(command, risk, "auto_approved", result["output"])
            self._print_result(result)
            return result

        elif risk == RiskLevel.MEDIUM:
            print("Orta risk. Onay gerekiyor.")
            approved = self._get_approval(command, risk)
            if approved:
                result = self.executor.execute(command)
                decision = "approved_telegram" if self.use_telegram else "approved"
                self.audit.log(command, risk, decision, result["output"])
                self._print_result(result)
                return result
            else:
                decision = "denied_telegram" if self.use_telegram else "denied"
                self.audit.log(command, risk, decision)
                print("Komut iptal edildi.")
                return {"success": False, "output": "", "error": "Denied by user"}

        elif risk == RiskLevel.HIGH:
            print("YUKSEK RISK! Dikkatli olun.")
            approved = self._get_approval(command, risk)
            if approved:
                print("Ilk onay alindi. Ikinci onay isteniyor...")
                confirmed = self._get_approval(command, risk, confirm=True)
                if confirmed:
                    result = self.executor.execute(command)
                    decision = "explicitly_approved_telegram" if self.use_telegram else "explicitly_approved"
                    self.audit.log(command, risk, decision, result["output"])
                    self._print_result(result)
                    return result
                else:
                    self.audit.log(command, risk, "denied_second_check")
                    print("Ikinci onay reddedildi. Komut iptal edildi.")
                    return {"success": False, "output": "", "error": "Denied on second check"}
            else:
                self.audit.log(command, risk, "denied")
                print("Komut iptal edildi.")
                return {"success": False, "output": "", "error": "Denied by user"}

        elif risk == RiskLevel.CRITICAL:
            print("KRITIK RISK. Bu komut engellendi.")
            print("Eger gercekten yapmak istiyorsaniz:")
            print("Manuel olarak terminalden calistirin.")
            self.audit.log(command, risk, "blocked")
            return {"success": False, "output": "", "error": "Blocked: critical risk"}

    def _get_approval(self, command, risk, confirm=False):
        if self.use_telegram:
            return self._telegram_approval(command, risk, confirm=confirm)
        else:
            return self._ask_approval(command, risk, confirm=confirm)

    def _print_result(self, result):
        if result["output"]:
            print("")
            print("Cikti:")
            print(result["output"][:500])
        if result["error"]:
            print("Hata: " + result["error"][:200])

    def _telegram_approval(self, command, risk, confirm=False):
        approval_path = Path("pending_approval.json")
        label = "confirm" if confirm else "initial"
        request = {
            "command": command,
            "risk_level": risk.value,
            "status": "pending",
            "timestamp": datetime.datetime.now().isoformat(),
            "label": label
        }
        approval_path.write_text(json.dumps(request, indent=2, ensure_ascii=False))
        print("Telegram'a onay talebi gonderildi...")
        print("Telefonunuzu kontrol edin. (120 saniye bekleniyor)")

        timeout = 120
        elapsed = 0
        while elapsed < timeout:
            time.sleep(1)
            elapsed += 1
            if approval_path.exists():
                try:
                    data = json.loads(approval_path.read_text())
                    status = data.get("status", "")
                    if status == "approved":
                        approval_path.unlink()
                        print("Telegram'dan onay alindi!")
                        return True
                    elif status == "denied":
                        approval_path.unlink()
                        print("Telegram'dan red alindi.")
                        return False
                except:
                    pass

        if approval_path.exists():
            approval_path.unlink()
        print("Zaman asimi. Onay alinamadi. Komut iptal edildi.")
        return False

    def _ask_approval(self, command, risk, confirm=False):
        if confirm:
            prompt = "   Kesin olarak onayliyor musunuz? (EVET/hayir): "
        else:
            prompt = "   Onayliyor musunuz? (evet/hayir): "
        try:
            response = input(prompt).strip().lower()
            if confirm:
                return response == "evet"
            return response in ("evet", "e", "yes", "y")
        except (EOFError, KeyboardInterrupt):
            return False


def main():
    import sys
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("DRY RUN MODE - Komutlar calistirilmayacak")
        print("")

    gate = ApprovalGate(dry_run=dry_run)

    print("THEIA GUARD v2.2")
    print("Approval-Based Execution Gate")
    print("-" * 40)
    if gate.use_telegram:
        print("Mod: Telegram Onay Kanali")
    else:
        print("Mod: Yerel Onay (stdin)")
    print("Cikmak icin: Ctrl+C")
    print("Istatistikler: /stats")
    print("")

    while True:
        try:
            cmd = input("> ").strip()
            if not cmd:
                continue
            if cmd == "/stats":
                stats = gate.audit.get_stats()
                print("")
                print("Istatistikler:")
                print("  Toplam:      " + str(stats.get("total", 0)))
                print("  Onaylanan:   " + str(stats.get("approved", 0)))
                print("  Reddedilen:  " + str(stats.get("denied", 0)))
                print("  Yuksek Risk: " + str(stats.get("high_risk_count", 0)))
                continue
            gate.process(cmd)
        except KeyboardInterrupt:
            print("")
            print("Theia Guard kapatildi.")
            stats = gate.audit.get_stats()
            print("Oturum: " + str(stats.get("total", 0)) + " komut islendi.")
            sys.exit(0)


if __name__ == "__main__":
    main()
