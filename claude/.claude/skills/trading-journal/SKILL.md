---
name: trading-journal
description: Elyes' ICT backtesting journal at trading.elyesghazel.ch, written with the `tj` CLI on the VPS. Use whenever he sends a chart / trade screenshot (FX Replay, TradingView, MT5, cTrader, a position-tool screenshot) or says "trag den trade ein", "log this trade", "backtest trade", "journal", "wie läuft mein backtest", "analysier mein journal", "meine trading regeln", or asks about his winrate, expectancy, R, drawdown or rules. Also for editing trades, rules or the analysis.
---

# trading journal

Web UI: https://trading.elyesghazel.ch (passkey). Code and README: `~/src/trading-journal`.
`tj` writes the same SQLite db the site reads, so a `tj` write shows up on refresh.

## A screenshot arrives: enter the trade

1. Look at the image properly. Read what is actually on it: pair, timeframe, date/time on the
   time axis or in the FX Replay header, direction, entry / SL / TP from the position tool, where
   price went (TP hit, SL hit, still open). Times in the screenshot are often UTC or New York -
   convert to Swiss time for `time=` and `session=` (London KZ 08:00-11:00, NY AM 14:30-17:00 CET;
   one hour later in summer is wrong, Swiss and NY both shift, but check the DST gap weeks in March/Nov).
2. `tj rules` and check the trade against every active rule. Only mark a rule broken when the
   screenshot or his message shows it (e.g. entry outside the killzone, RR under 1:2, third trade
   of the day - `tj ls` shows the day). Unclear = ask, don't guess.
3. Unsure about a value that changes the result (exit, SL, direction)? Ask one short question
   before writing. Values that don't matter (exact time to the minute) can be estimated, say so.
4. Write it, screenshot attached (T3 attachments live in `~/.t3/userdata/attachments/`):
   ```sh
   tj add pair=EURUSD dir=long session=ny-am setup="Silver Bullet FVG" bias=bullish tf=1m \
          entry=1.0712 sl=1.0702 tp=1.0742 exit=1.0742 date=2025-03-12 time=15:10 broken=8 \
          mistakes="..." --shot /home/elyes/.t3/userdata/attachments/<file>.png
   ```
   `mode=` defaults to `backtest`; `paper` / `live` only when he says so. No exit yet -> leave it,
   outcome stays `open`, later `tj set <id> exit=...` (or `r=-1` / `outcome=be`).
5. `tj review <id> "..."`: 2-4 sentences in German. What was good per the rules, what broke them,
   one concrete thing for next time. Honest, no hype - a winning trade that broke rules is a bad
   trade.
6. Reply short: the result in R, which rules broke (if any), the review line, the link
   `https://trading.elyesghazel.ch/#trade/<id>`.

Several screenshots of one trade (entry + result) = one trade with several `--shot`.
Several trades in one message = several `tj add` calls.

## "analysier mein journal"

`tj stats` (add `--mode backtest` to split modes) and `tj ls 100`. Look at expectancy and sample
size first: under ~30 closed trades say clearly that nothing is proven yet. Then: clean vs broken
trades, most broken rules, setups/sessions that lose, loss streaks, days over 2 trades. Write the
result with `tj analysis -` (stdin, German, short sections, numbers first) and reply with the
two or three points that matter most plus `https://trading.elyesghazel.ch/#stats`.

## Context

He wants to trade a prop-firm account later and give the first payout to his mom. Agreed plan
(2026-11-10): rules fixed first, 100 backtest trades on one pair, then paper in real time, earliest
a small challenge in Feb 2027, no spending on trading before that. Don't encourage skipping steps;
if stats are bad, say so.
