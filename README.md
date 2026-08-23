# Berlin Transit Delay Predictor 🚆

Predicts how likely a Berlin (VBB) bus/train route is to be delayed, based on
route, day of week, and time — trained on real-time delay data I collected
myself, since no public dataset of actual (vs scheduled) transit times exists
for free.

## Why this project
Most beginner ML projects use the same 3-4 textbook datasets (Titanic, Iris,
Heart Disease). This one uses a real, messy, self-collected dataset from my
own city's public transit system.

## Project status
🚧 In progress — currently in the data collection phase.

## How it works
1. **Static schedule data** — VBB's free GTFS feed (routes, stops, planned times)
2. **Real delay data** — collected by polling VBB's live GTFS-Realtime feed
   automatically via a scheduled GitHub Action, logging scheduled vs. actual
   arrival times over several weeks
3. **Model** — scikit-learn classifier trained on the collected data, predicting
   delay risk for a given route + time + day
4. **App** — a Streamlit dashboard where a user picks a route/time and sees the
   predicted delay risk

## Repo structure
```
scripts/       # data collection & processing scripts
data/          # collected datasets (raw + processed)
notebooks/     # exploration & model training
.github/workflows/  # scheduled data-collection automation
```

## Tech stack
Python, pandas, scikit-learn, Streamlit, GTFS / GTFS-Realtime, GitHub Actions

## Author
Tirth Chovatiya
