#!/bin/bash
cd /root/solana_trader
/usr/bin/python3 backup_to_github.py >> /root/solana_trader/logs/github_backup.log 2>&1
