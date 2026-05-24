# Deployment Guide

This project is ready for GitHub and Streamlit Community Cloud.

## 1. GitHub Setup

Create an empty GitHub repository named something like:

```text
ucl-final-predictor
```

Do not initialize it with a README, `.gitignore`, or license because this local
project already has those files.

After creating the repository, GitHub will show a remote URL. It will look like one
of these:

```text
https://github.com/<your-username>/ucl-final-predictor.git
git@github.com:<your-username>/ucl-final-predictor.git
```

Add the remote locally:

```powershell
git remote add origin https://github.com/<your-username>/ucl-final-predictor.git
```

Push the branch:

```powershell
git push -u origin codex/ucl-predictor
```

If you want the branch to be `main`, run:

```powershell
git branch -M main
git push -u origin main
```

## 2. Streamlit Community Cloud

1. Go to Streamlit Community Cloud.
2. Sign in with GitHub.
3. Select **New app**.
4. Pick the GitHub repository.
5. Set the branch:

```text
main
```

or:

```text
codex/ucl-predictor
```

depending on what you pushed.

6. Set the app entry file:

```text
app.py
```

7. Deploy.

Streamlit will install packages from:

```text
requirements.txt
```

## 3. Files Required For Deployment

These files must be committed:

```text
app.py
requirements.txt
.streamlit/config.toml
src/
data/raw/
data/processed/
```

The app uses repo-relative paths, so it should run in cloud deployment without
access to your local `D:\Projects\...` folders.

## 4. Local Production Check

Before pushing, run:

```powershell
python main.py
python -m py_compile app.py main.py src\data_loader.py src\team_model.py src\player_model.py src\predict.py src\simulator.py
streamlit run app.py
```

## 5. Updating The App Later

After making changes:

```powershell
git status
git add .
git commit -m "Describe the change"
git push
```

Streamlit Cloud will usually redeploy automatically after a push.

## 6. Troubleshooting

If Streamlit says a package is missing, add it to:

```text
requirements.txt
```

If data is missing, confirm the files exist under:

```text
data/raw/
data/processed/
```

If the app starts locally but not in the cloud, check Streamlit Cloud logs first.
Most failures will be missing dependencies, missing data files, or incorrect file
paths.
