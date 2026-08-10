# Application Domain Rules

This document is the source of truth for your TDD loop. Fill in each section **before** you write any code — every rule you write here becomes at least one test.

There are no wrong answers, but there are inconsistent ones. Once you decide a rule, your code has to match it.

---

## 1. Currency Symbol

*What currency does your application use, and how is money formatted when it's displayed?*

> $

---

## 2. Standard Categories

*Which expense categories are allowed? Limit yourself to 3–5. What happens if someone uses a category that isn't on your list?*

> Only Food and Transport should be allowed. All other categories should give me an error.

---

## 3. Overspending Behaviour (Total Balance)

*What happens when an expense is larger than the total balance? Does your app allow the balance to go negative, or does it block the transaction? If it blocks, what does the caller get back?*

> Block and Give an error message.

---

## 4. Budget Limits (Category Budgets)

*What happens when an expense exceeds a category's budget limit, but the balance could still cover it? Is it blocked, or is it recorded with a warning?*

> Transaction is blocked and the error message is displayed.

---

## TDD Blueprint

Now turn each rule above into the test you will write **before** the implementation exists. Name the behaviour you'd assert.

- [ ] Rule 1 (Currency) → Only dollar should be allowed, all the others should give an error.
- [ ] Rule 2 (Categories) →Only Food and Transport should be allowed. All other categories should give me an error.
- [ ] Rule 3 (Overspending) → Display error message
- [ ] Rule 4 (Budget Limits) → Block the transaction and display error message.
