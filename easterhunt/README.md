## Acknowledgment

This README was edited for grammatical accuracy with the assistance of AI to ensure clarity and readability. English is not my first language, but I have ensured that all content edited is correct.

# Easter Hunt - Egg Rarity System README

Welcome to the Easter Hunt! This cog lets you hunt for Easter eggs, work for the Easter Bunny, trade shards for credits, and compete on a leaderboard. One of the core mechanics is the egg hunting system, where you can find eggs of varying rarity. This README explains how the egg rarity system works, so you can understand your chances of finding those elusive rare eggs and how to improve your odds.

## Overview of Egg Types
There are six types of eggs you can find while hunting, each with increasing rarity:

- **Common Egg**: The most frequent egg, easy to find.
- **Silver Egg**: A shiny, uncommon egg that’s a bit harder to get.
- **Gold Egg**: A rare egg that feels like a jackpot when you find it.
- **Shiny Egg**: An extremely rare egg that sparkles with a dazzling glow.
- **Legendary Egg**: An ultra-rare egg, a mythical find for dedicated hunters.
- **Mythical Egg**: The rarest egg, an otherworldly treasure that requires a Legendary Egg to even have a chance of finding.

## How Hunting Works
The `[p]easterhunt hunt` command lets you go on an Easter egg hunt. Here’s the basic flow:

1. **Cooldown**: You can hunt once every 5 minutes. This cooldown ensures that rare eggs remain special by limiting how often you can hunt.
2. **Hunt Duration**: Each hunt takes 1 minute to complete, during which you’re searching the fields for eggs.
3. **Outcome**: After the hunt, you’ll either find an egg (Common, Silver, Gold, Shiny, Legendary, or Mythical) or return empty-handed. The outcome is determined by a combination of base probabilities, pity timers, hunt streaks, and specific conditions.

## Rarity Mechanics
Unlike a purely random system, the egg rarity system uses a combination of mechanics inspired by games like Pokémon to make rare eggs harder to obtain while rewarding persistence and dedication. Here’s how it works:

### 1. Base Probabilities
The system starts with base probabilities for each outcome, measured out of 1000 for fine control:

- **Nothing**: 50% (500/1000) - You might return empty-handed.
- **Common Egg**: 40% (400/1000) - The most likely egg to find.
- **Silver Egg**: 5% (50/1000) - Uncommon, but achievable with some effort.
- **Gold Egg**: 3% (30/1000) - Rare, a nice surprise.
- **Shiny Egg**: 0.012% (0.12/1000) - Extremely rare, a major achievement.
- **Legendary Egg**: 0.5% (5/1000) - Ultra-rare, but only if you meet specific conditions (see below).
- **Mythical Egg**: 0.01% (1/1000) - The rarest egg, only available if you meet specific conditions (see below).

These base probabilities are adjusted dynamically based on other mechanics, so your actual chances may be higher depending on your progress.

### 2. Pity Timer
To ensure you’re not stuck with bad luck forever, the system uses a **pity timer** for each egg type (Silver, Gold, Shiny, Legendary, Mythical). The pity timer tracks how many hunts you’ve done without finding a specific egg type and increases your chances over time. It also guarantees a drop after a certain number of hunts.

- **How It Works**:
  - Each hunt increments a pity counter for each egg type (Silver, Gold, Shiny, Legendary, Mythical) if you don’t find that egg.
  - The pity counter boosts your chances of finding that egg:
    - **Silver**: +0.5% per hunt without a Silver Egg.
    - **Gold**: +0.3% per hunt without a Gold Egg.
    - **Shiny**: +0.01% per hunt without a Shiny Egg.
    - **Legendary**: +0.1% per hunt without a Legendary Egg (if you meet the conditions).
    - **Mythical**: +0.02% per hunt without a Mythical Egg (if you meet the conditions).
  - If you find an egg of a certain rarity, the pity counter for that rarity (and all lower rarities) resets to 0. For example, finding a Gold Egg resets the pity counters for Silver and Gold but not for Shiny, Legendary, or Mythical.

- **Guaranteed Drops**:
  - **Silver Egg**: Guaranteed after 50 hunts without finding one (about 4.2 hours of hunting with the 5-minute cooldown).
  - **Gold Egg**: Guaranteed after 75 hunts without finding one (about 6.25 hours of hunting).
  - **Shiny Egg**: Guaranteed after 150 hunts without finding one (about 12.5 hours of hunting).
  - **Legendary Egg**: Guaranteed after 150 hunts without finding one (about 12.5 hours of hunting), but only if you meet the Legendary Egg conditions (see below).
  - **Mythical Egg**: Guaranteed after 500 hunts without finding one (about 41.7 hours of hunting), but only if you meet the Mythical Egg conditions (see below).

Please note that the hours may not be accurate.

### 3. Hunt Streak
The **hunt streak** rewards players who hunt consistently by increasing their chances of finding rare eggs. If you hunt as soon as your cooldown ends, your streak increases, giving you a bonus to your rare egg chances.

- **How It Works**:
  - Your hunt streak increases by 1 each time you hunt within 1 minute of your cooldown ending (5 minutes + 1 minute grace period).
  - If you miss this window (e.g., you wait too long to hunt again), your streak resets to 1.
  - For every 5 hunts in your streak, your chances of finding a rare egg increase by 1% (10/1000). For example:
    - After 5 hunts in a streak: +1% to Silver, Gold, Shiny, Legendary, and Mythical chances.
    - After 10 hunts in a streak: +2% to Silver, Gold, Shiny, Legendary, and Mythical chances.
  - The streak bonus applies to all rare eggs (Silver, Gold, Shiny, Legendary, and Mythical, if eligible).

- **Example**:
  - Base chance for a Silver Egg: 5%.
  - After 10 hunts in a streak: +2% bonus, so the chance becomes 7%.
  - This bonus stacks with the pity timer, so if you’ve also done 20 hunts without a Silver Egg (+10% from pity), your total chance for a Silver Egg would be 17%.

### 4. Legendary Egg Conditions
Legendary Eggs are ultra-rare, and you can’t even roll for them unless you meet specific conditions. This ensures that only dedicated players who have already collected a significant number of other rare eggs can obtain a Legendary Egg.

- **Conditions**:
  - You must have at least:
    - 20 Silver Eggs
    - 10 Gold Eggs
    - 1 Shiny Egg
  - If you don’t meet these conditions, your chance of finding a Legendary Egg is 0%, even with the pity timer or hunt streak.

- **Why This Matters**:
  - This requirement forces players to hunt extensively and collect other rare eggs before they can even dream of a Legendary Egg.
  - It makes Legendary Eggs a true endgame goal, rewarding long-term dedication.

### 5. Mythical Egg Conditions
Mythical Eggs are the rarest of all, and you can’t even roll for them unless you meet specific conditions. This ensures that only the most dedicated players who have already obtained a Legendary Egg can obtain a Mythical Egg.

- **Conditions**:
  - You must first meet the Legendary Egg conditions (20 Silver, 10 Gold, 1 Shiny).
  - Additionally, you must have at least:
    - 1 Legendary Egg
  - If you don’t meet these conditions, your chance of finding a Mythical Egg is 0%, even with the pity timer or hunt streak.

- **Why This Matters**:
  - This requirement ensures that Mythical Eggs are the ultimate endgame goal, only achievable after significant effort and dedication.

### 6. Dynamic Probability Adjustment
The system dynamically adjusts the probabilities to ensure the total adds up to 100% (1000/1000). As your chances of finding rare eggs increase (due to pity timers and hunt streaks), the chances of finding Common Eggs or nothing decrease slightly.

- **How It Works**:
  - The total probability of rare eggs (Silver + Gold + Shiny + Legendary + Mythical) is calculated.
  - The chance of finding a Common Egg is reduced to balance the increase in rare egg chances, but it’s always at least 10% (100/1000) to ensure Common Eggs remain frequent.
  - The chance of finding nothing takes up the remaining probability.

- **Example**:
  - Base chances: Nothing (50%), Common (40%), Silver (5%), Gold (3%), Shiny (0.012%), Legendary (0.5%), Mythical (0.01%).
  - After 20 hunts without a Silver Egg (+10% to Silver) and a streak of 10 (+2% to all rares):
    - Silver: 5% + 10% + 2% = 17%
    - Gold: 3% + 2% = 5%
    - Shiny: 0.012% + 2% = 2.012%
    - Legendary: 0.5% + 2% = 2.5%
    - Mythical: 0.01% + 2% = 2.01%
    - Total rare: 17% + 5% + 2.012% + 2.5% + 2.01% = 28.522%
    - Common: Reduced to 40% - (28.522% / 2) = 25.739% (but at least 10%)
    - Nothing: 100% - (25.739% + 28.522%) = 45.739%

## Expected Drop Rates
Here’s an estimate of how often you might find each egg type, we will be assuming you hunt as soon as the cooldown ends (every 5 minutes):

- **Common Egg**: Very frequent, about 40% base chance per hunt. You’ll find these often, even with adjustments.
- **Silver Egg**: Base 5% chance, but increases with pity and streak. On average, you might get one every 20-30 hunts (1.7-2.5 hours), but guaranteed after 50 hunts (4.2 hours).
- **Gold Egg**: Base 3% chance, increasing with pity and streak. On average, every 33-50 hunts (2.75-4.2 hours), guaranteed after 75 hunts (6.25 hours).
- **Shiny Egg**: Base 0.012% chance, increasing with pity and streak. On average, every 500-1000 hunts (41.7-83.3 hours), guaranteed after 150 hunts (12.5 hours).
- **Legendary Egg**: Base 0.5% chance (if eligible), increasing with pity and streak. On average, every 200 hunts (16.7 hours), guaranteed after 150 hunts (12.5 hours), but only if you meet the conditions (20 Silver, 10 Gold, 1 Shiny).
- **Mythical Egg**: Base 0.01% chance (if eligible), increasing with pity and streak. On average, every 1000 hunts (83.3 hours), guaranteed after 500 hunts (41.7 hours), but only if you meet the conditions (1 Legendary Egg).

## Tips to Improve Your Chances
- **Hunt Consistently**: Keep your hunt streak high by hunting as soon as your cooldown ends. The streak bonus can significantly boost your chances of rare eggs over time.
- **Be Patient**: The pity timer ensures you’ll eventually get rare eggs, even if you’re unlucky. Keep hunting, and your chances will improve with each hunt.
- **Aim for Legendary and Mythical Conditions**: Collect 20 Silver, 10 Gold, and 1 Shiny Egg to unlock the chance to find a Legendary Egg. After obtaining a Legendary Egg, you can start rolling for a Mythical Egg.
- **Check Your Progress**: Use the `[p]easterhunt progress` command to see your pity counters, hunt streak, and egg collection. This will help you track how close you are to guaranteed drops or Legendary/Mythical eligibility.

## Why This System?
The rarity system is designed to make rare eggs feel like a true achievement while ensuring players aren’t stuck with endless bad luck. The combination of pity timers, hunt streaks, and conditions for Legendary and Mythical Eggs creates a balanced experience where:

- **Casual Players**: Can enjoy finding Common Eggs and the occasional Silver Egg without much effort.
- **Dedicated Players**: Are rewarded for their persistence with guaranteed rare drops and increased chances over time.
- **Endgame Players**: Have long-term goals (Legendary and Mythical Eggs) that require significant effort and dedication.

Happy hunting, and may the Easter Bunny bring you a Mythical Egg! 🐰🥚✨
