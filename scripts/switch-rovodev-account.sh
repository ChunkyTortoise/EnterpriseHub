#!/bin/bash

# Rovo Dev Account Switcher
# This script helps you switch between different Rovo Dev accounts when credits run out

set -e  # Exit on error

echo "╭────────────────────────────────────────────╮"
echo "│   Rovo Dev Account Switcher               │"
echo "╰────────────────────────────────────────────╯"
echo ""

# Function to show current account
show_current_account() {
    echo "Current Account Status:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    acli rovodev auth status
    echo ""
}

# Function to logout
logout_account() {
    echo "Logging out from current account..."
    acli rovodev auth logout
    echo "✓ Logout successful"
    echo ""
}

# Function to login
login_account() {
    local email=$1
    local token=$2

    echo "Logging in as: $email"
    echo "$token" | acli rovodev auth login --email "$email" --token
    echo ""
    echo "✓ Login successful!"
    echo ""
}

# Main menu
echo "What would you like to do?"
echo ""
echo "1) Show current account status"
echo "2) Switch to Personal Account (chunkytortoise2@gmail.com)"
echo "3) Switch to Work Account (YOUR_WORK_EMAIL)"
echo "4) Manual login (enter credentials)"
echo "5) Logout only"
echo "6) Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        show_current_account
        ;;
    2)
        echo ""
        echo "Switching to Personal Account..."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        logout_account
        read -sp "Enter API token for chunkytortoise2@gmail.com: " token
        echo ""
        login_account "chunkytortoise2@gmail.com" "$token"
        show_current_account
        ;;
    3)
        echo ""
        echo "Switching to Work Account..."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        logout_account
        read -p "Enter work email: " work_email
        read -sp "Enter API token for $work_email: " token
        echo ""
        login_account "$work_email" "$token"
        show_current_account
        ;;
    4)
        echo ""
        echo "Manual Login"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        logout_account
        read -p "Enter email: " email
        read -sp "Enter API token: " token
        echo ""
        login_account "$email" "$token"
        show_current_account
        ;;
    5)
        echo ""
        logout_account
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac

echo ""
echo "Done!"
