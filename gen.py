#!/usr/bin/env python3
"""Builds index.html for PavanVibe/ganesh from data.json + head.html.

data.json
  collections: [name, note, promised, received, mode, date]
  expenses:    [item, note, cost|null, paid, date, mode, paid_by]
"""
import json, html, datetime

UPDATED = "22 September 2026"
UNNOTED_CASH = 1600   # 13 Sep door collections: recorded as a lump, not per person

D = json.load(open("data.json", encoding="utf-8"))
COLLECTIONS = D["collections"]
EXPENSES = D["expenses"]

MONTHS = {m: i for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], 1)}
def date_key(d):
    if not d: return (0, 0, 0)
    try:
        day, mon = d.split()[:2]
        return (1, MONTHS.get(mon[:3], 0), int(day))
    except Exception:
        return (2, 0, 0)
COLLECTIONS.sort(key=lambda c: date_key(c[5]))
EXPENSES.sort(key=lambda e: date_key(e[4]))

R = "\u20b9"
def money(n):
    n = int(round(n)); neg = n < 0; s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]; parts = []
        while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
        if head: parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + R + s
def esc(s): return html.escape(str(s))

# ---------------- totals ----------------
pledged    = sum(c[2] for c in COLLECTIONS)
received   = sum(c[3] for c in COLLECTIONS)
to_collect = pledged - received
cash   = sum(c[3] for c in COLLECTIONS if c[4].lower() == "cash")
online = sum(c[3] for c in COLLECTIONS if c[4].lower() == "online")
other  = received - cash - online

unnoted_note = ""
if other > 0:
    unnoted_online = other - UNNOTED_CASH
    cash += UNNOTED_CASH; online += unnoted_online
    unnoted_note = ('<p class="sub">Includes the 13 Sep door collections \u2014 '
                    + money(UNNOTED_CASH) + ' cash and ' + money(unnoted_online)
                    + ' online \u2014 recorded as a total rather than per person.</p>')
    other = 0

cost   = sum((e[2] if e[2] is not None else e[3]) for e in EXPENSES)
spent  = sum(e[3] for e in EXPENSES)
unpaid = cost - spent
rahul_out  = sum(e[3] for e in EXPENSES if e[6])
cash_out   = sum(e[3] for e in EXPENSES if e[5].lower() == "cash" and not e[6])
online_out = sum(e[3] for e in EXPENSES if e[5].lower() == "online" and not e[6])
committee_out = spent - rahul_out
other_out  = committee_out - cash_out - online_out
cash_box   = cash - cash_out
in_hand    = received - committee_out

# ---------------- rows ----------------
def tag(paid, total, is_exp):
    if total is None: return '<span class="tag t-part">Advance paid</span>'
    if paid <= 0: return '<span class="tag t-due">%s</span>' % ("Unpaid" if is_exp else "Not yet")
    if total - paid > 0: return '<span class="tag t-part">%s due</span>' % money(total - paid)
    return '<span class="tag t-paid">%s</span>' % ("Settled" if is_exp else "Paid")

def rows(items, is_exp):
    out = []
    for it in items:
        if is_exp: name, note, total, paid, date, mode, by = it
        else:      name, note, total, paid, mode, date = it; by = ""
        due = 0 if total is None else total - paid
        sub = ""
        if date: sub += '<small class="when">%s</small>' % esc(date)
        if note: sub += "<small>%s</small>" % esc(note)
        if mode:
            sub += ('<small>Paid %s%s</small>' % (esc(mode.lower()), (' by %s' % esc(by)) if by else '')) \
                   if is_exp else ('<span class="mode">%s</span>' % esc(mode))
        out.append('<tr><td class="who">%s%s</td><td class="num">%s</td><td class="num">%s</td>'
                   '<td class="num hide-sm">%s</td><td>%s</td></tr>'
                   % (esc(name), sub, "cost TBC" if total is None else money(total), money(paid),
                      money(due) if due > 0 else "&mdash;", tag(paid, total, is_exp)))
    return "\n".join(out)

def cell(v):
    return '<td class="num"><span%s>%s</span></td>' % (' class="neg"' if v < 0 else "", money(v))

split_rows  = '<tr><td>Cash</td>' + cell(cash) + cell(cash_out) + cell(cash - cash_out) + '</tr>'
split_rows += '<tr><td>Online</td>' + cell(online) + cell(online_out) + cell(online - online_out) + '</tr>'
if other > 0 or other_out > 0:
    split_rows += '<tr><td>Not yet noted</td>' + cell(other) + cell(other_out) + cell(other - other_out) + '</tr>'
split_table = ('<table class="split"><thead><tr><th></th><th class="num">Came in</th>'
               '<th class="num">Paid out</th><th class="num">In hand</th></tr></thead><tbody>'
               + split_rows + '</tbody><tfoot><tr><td>Total</td>'
               + cell(received) + cell(committee_out) + cell(in_hand) + '</tr></tfoot></table>')

owed_block = ""
if rahul_out > 0:
    owed_block = ('<div class="notice owed"><h3>Owed to Rahul &mdash; ' + money(rahul_out) + '</h3>'
        '<p>Rahul paid for the items marked <em>paid by Rahul</em> from his own account. '
        'That money has not come out of the committee fund and is still owed back to him.</p>'
        '<p>After repaying him the committee would hold ' + money(in_hand - rahul_out) + '.</p></div>')

gap = (unpaid + rahul_out) - (in_hand + to_collect)
notice = ""
if gap > 0:
    notice = ('<div class="notice"><h3>We need more collections</h3><p>Bills and repayments still due come to '
              '<span class="big-due">%s</span>. Against that we have %s in hand and %s promised &mdash; '
              'a shortfall of <span class="big-due">%s</span>.</p></div>'
              % (money(unpaid + rahul_out), money(in_hand), money(to_collect), money(gap)))
elif to_collect > 0:
    notice = ('<div class="notice"><h3>%s still to be collected</h3>'
              '<p>Those marked pending above, please settle when you can.</p></div>' % money(to_collect))

BODY = """<body>
<header class="banner">
  <h1>Ganesh Chaturthi<span class="year">Accounts &middot; 2026</span></h1>
  <p class="stamp">Updated __UPDATED__</p>
</header>
<div class="garland" aria-hidden="true"></div>
<div class="wrap">

  <dl class="totals">
    <div class="in"><dt>Collected</dt><dd>__RECEIVED__</dd></div>
    <div class="out"><dt>Spent</dt><dd>__SPENT__</dd></div>
    <div class="wide"><dt>Money in hand</dt><dd>__INHAND__</dd></div>
  </dl>

  <h2>Cash and online</h2>
  <p class="sub">Where the money sits right now.</p>
  __SPLIT__
  __UNNOTED__

  <h2>Collections</h2>
  <p class="sub">__NDONORS__ contributors so far. __COLLNOTE__</p>
  <table>
    <thead><tr><th>Name</th><th class="num">Promised</th><th class="num">Received</th>
      <th class="num hide-sm">Due</th><th>Status</th></tr></thead>
    <tbody>
__COLLROWS__
    </tbody>
    <tfoot><tr><td>Total</td><td class="num">__PLEDGED__</td><td class="num">__RECEIVED__</td>
      <td class="num hide-sm">__TOCOLLECT__</td><td></td></tr></tfoot>
  </table>

  <h2>Expenses</h2>
  <p class="sub">__COST__ committed. __EXPNOTE__</p>
  <table>
    <thead><tr><th>Item</th><th class="num">Cost</th><th class="num">Paid</th>
      <th class="num hide-sm">Balance</th><th>Status</th></tr></thead>
    <tbody>
__EXPROWS__
    </tbody>
    <tfoot><tr><td>Total</td><td class="num">__COST__</td><td class="num">__SPENT__</td>
      <td class="num hide-sm">__UNPAID__</td><td></td></tr></tfoot>
  </table>
  <p class="sub">__CASHOUT__ paid in cash, __ONLINEOUT__ paid online from the committee fund, __RAHULOUT__ paid by Rahul.</p>

  __OWED__

  __NOTICE__

  <footer>Every rupee received and spent is listed above. Something looks wrong? Tell the committee and it will be corrected.</footer>
</div>
</body>
</html>
"""

repl = {
    "__UPDATED__": UPDATED, "__RECEIVED__": money(received), "__SPENT__": money(spent),
    "__INHAND__": money(in_hand), "__SPLIT__": split_table, "__UNNOTED__": unnoted_note,
    "__NDONORS__": str(len(COLLECTIONS)),
    "__COLLNOTE__": (money(to_collect) + " still to come in.") if to_collect > 0 else "Everyone has paid in full.",
    "__COLLROWS__": rows(COLLECTIONS, False), "__PLEDGED__": money(pledged), "__TOCOLLECT__": money(to_collect),
    "__COST__": money(cost),
    "__EXPNOTE__": (money(unpaid) + " of it is still unpaid.") if unpaid > 0 else "All bills settled.",
    "__EXPROWS__": rows(EXPENSES, True), "__UNPAID__": money(unpaid),
    "__CASHOUT__": money(cash_out), "__ONLINEOUT__": money(online_out), "__RAHULOUT__": money(rahul_out),
    "__OWED__": owed_block, "__NOTICE__": notice,
}
out = BODY
for k, v in repl.items(): out = out.replace(k, v)
open("index.html", "w", encoding="utf-8").write(open("head.html", encoding="utf-8").read() + out)

if __name__ == "__main__":
    print("received", received, "| spent", spent, "| rahul", rahul_out, "| committee_out", committee_out)
    print("cash_box", cash_box, "| online_bal", online - online_out, "| in_hand", in_hand,
          "| unpaid", unpaid, "| to_collect", to_collect)
