#!/bin/sh
cd '/home/leejaeik/Projects/ksat-10000' || exit 1
export PYTHONUTF8='1'
export HERMES_HOME='/home/leejaeik/.hermes'
exec '/home/leejaeik/.hermes/hermes-agent/.hermes/bin/hermes' '--profile' 'ksat-administrator' '--tui' '--resume' 'local-199f550acc55245af3b19eb9f395fe72f4662539346325200b75aea862b24604'
