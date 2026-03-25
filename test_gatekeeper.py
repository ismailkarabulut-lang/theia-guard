"""
Theia Guard — Risk Classifier Unit Tests
Çalıştır: python3 -m pytest test_gatekeeper.py -v
"""

import pytest
from gatekeeper import RiskClassifier, RiskLevel


@pytest.fixture
def clf():
    return RiskClassifier()


# ─── CRITICAL ─────────────────────────────────────────────────────────────────

class TestCritical:
    def test_rm_rf_root(self, clf):
        assert clf.classify("rm -rf /") == RiskLevel.CRITICAL

    def test_rm_rf_root_with_space(self, clf):
        assert clf.classify("rm -rf / ") == RiskLevel.CRITICAL

    def test_rm_rf_wildcard(self, clf):
        assert clf.classify("rm -rf /*") == RiskLevel.CRITICAL

    def test_dd_zero(self, clf):
        assert clf.classify("dd if=/dev/zero of=/dev/sda") == RiskLevel.CRITICAL

    def test_dd_random(self, clf):
        assert clf.classify("dd if=/dev/random of=/dev/sda") == RiskLevel.CRITICAL

    def test_mkfs_ext4(self, clf):
        assert clf.classify("mkfs.ext4 /dev/sda1") == RiskLevel.CRITICAL

    def test_rm_rf_etc(self, clf):
        assert clf.classify("rm -rf /etc") == RiskLevel.HIGH

    def test_rm_rf_home(self, clf):
        assert clf.classify("rm -rf /home") == RiskLevel.HIGH

    def test_rm_rf_boot(self, clf):
        assert clf.classify("rm -rf /boot") == RiskLevel.CRITICAL

    def test_rm_rf_usr(self, clf):
        assert clf.classify("rm -rf /usr") == RiskLevel.HIGH

    def test_chmod_000_root(self, clf):
        assert clf.classify("chmod -R 000 /") == RiskLevel.CRITICAL


# ─── HIGH ─────────────────────────────────────────────────────────────────────

class TestHigh:
    def test_rm_rf_project(self, clf):
        assert clf.classify("rm -rf /home/user/myproject") == RiskLevel.HIGH

    def test_sudo_rm(self, clf):
        assert clf.classify("sudo rm important_file.txt") == RiskLevel.HIGH

    def test_shred(self, clf):
        assert clf.classify("shred -u secrets.txt") == RiskLevel.HIGH

    def test_drop_table(self, clf):
        assert clf.classify("DROP TABLE users") == RiskLevel.HIGH

    def test_drop_database(self, clf):
        assert clf.classify("DROP DATABASE production") == RiskLevel.HIGH

    def test_delete_from(self, clf):
        assert clf.classify("DELETE FROM orders WHERE id > 0") == RiskLevel.HIGH

    def test_chmod_777(self, clf):
        assert clf.classify("chmod 777 /var/www/html") == RiskLevel.HIGH

    def test_injection_pipe_bash(self, clf):
        assert clf.classify("cat file.txt | bash") == RiskLevel.HIGH

    def test_injection_semicolon_rm(self, clf):
        assert clf.classify("echo hello; rm -rf mydir") == RiskLevel.HIGH

    def test_injection_and_sudo(self, clf):
        assert clf.classify("ls && sudo apt remove python3") == RiskLevel.HIGH


# ─── MEDIUM ───────────────────────────────────────────────────────────────────

class TestMedium:
    def test_rm_rf_tmp(self, clf):
        """Safe path istisnası: /tmp altındaki rm -rf MEDIUM olmalı"""
        assert clf.classify("rm -rf /tmp/test_folder") == RiskLevel.MEDIUM

    def test_apt_install(self, clf):
        assert clf.classify("sudo apt install vim") == RiskLevel.MEDIUM

    def test_pip_install(self, clf):
        assert clf.classify("pip install requests") == RiskLevel.MEDIUM

    def test_pip_uninstall(self, clf):
        assert clf.classify("pip uninstall flask") == RiskLevel.MEDIUM

    def test_npm_install(self, clf):
        assert clf.classify("npm install express") == RiskLevel.MEDIUM

    def test_systemctl_stop(self, clf):
        assert clf.classify("systemctl stop nginx") == RiskLevel.MEDIUM

    def test_systemctl_disable(self, clf):
        assert clf.classify("sudo systemctl disable apache2") == RiskLevel.MEDIUM

    def test_mv(self, clf):
        assert clf.classify("mv config.json config.json.bak") == RiskLevel.MEDIUM

    def test_apt_upgrade(self, clf):
        assert clf.classify("sudo apt upgrade") == RiskLevel.MEDIUM

    def test_rm_rf_var_cache(self, clf):
        """Safe path: /var/cache altındaki rm -rf MEDIUM olmalı"""
        assert clf.classify("rm -rf /var/cache/apt/archives") == RiskLevel.MEDIUM


# ─── LOW ──────────────────────────────────────────────────────────────────────

class TestLow:
    def test_ls(self, clf):
        assert clf.classify("ls") == RiskLevel.LOW

    def test_ls_la(self, clf):
        assert clf.classify("ls -la") == RiskLevel.LOW

    def test_pwd(self, clf):
        assert clf.classify("pwd") == RiskLevel.LOW

    def test_cat(self, clf):
        assert clf.classify("cat README.md") == RiskLevel.LOW

    def test_echo(self, clf):
        assert clf.classify("echo hello world") == RiskLevel.LOW

    def test_grep(self, clf):
        assert clf.classify("grep -r 'TODO' ./src") == RiskLevel.LOW

    def test_git_status(self, clf):
        assert clf.classify("git status") == RiskLevel.LOW

    def test_git_log(self, clf):
        assert clf.classify("git log --oneline") == RiskLevel.LOW

    def test_python_version(self, clf):
        assert clf.classify("python3 --version") == RiskLevel.LOW

    def test_empty_command(self, clf):
        assert clf.classify("  ") == RiskLevel.LOW


# ─── EDGE CASES ───────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_case_insensitive_drop(self, clf):
        """Büyük/küçük harf farkı önemli olmamalı"""
        assert clf.classify("drop table users") == RiskLevel.HIGH

    def test_whitespace_padding(self, clf):
        """Başında/sonunda boşluk olsa da doğru sınıflandırılmalı"""
        assert clf.classify("  ls -la  ") == RiskLevel.LOW

    def test_rm_rf_var_tmp(self, clf):
        """/var/tmp safe path sayılmalı"""
        assert clf.classify("rm -rf /var/tmp/old_logs") == RiskLevel.MEDIUM

    def test_truncate_sql(self, clf):
        assert clf.classify("TRUNCATE TABLE sessions") == RiskLevel.HIGH
