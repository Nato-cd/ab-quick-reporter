# 🚀 AB Quick Reporter

**AB Quick Reporter** is your one-stop toolkit for transforming raw [Apache Bench (ab)](https://httpd.apache.org/docs/2.4/programs/ab.html) HTTP benchmarking results into clean summaries and beautiful charts—perfect for performance analysis and sharing.

<div align="center">
  <img src="https://img.shields.io/badge/License-MIT-1abc9c?style=for-the-badge&logo=github" alt="MIT License">
</div>

---

## ✨ Features

- **Automated Summaries:** Parse and summarize Apache Bench results in seconds.
- **Instant Visualizations:** Generate charts for requests/sec, latency, and more.
- **Effortless Export:** Save charts as image files—ready for your reports or presentations.

---

> **Note:** All scripts in this project were generated with the help of AI.

---

## ⚡️ Quick Start

### 1. Install Requirements

**Python 3.10+** and **matplotlib** are required.

#### Install matplotlib via apt:

```bash
sudo apt update
sudo apt install python3-matplotlib
```

#### Or use pip (recommended with a virtual environment):

```bash
python3 -m venv venv
source venv/bin/activate
pip install matplotlib
```

---

### 2. Run Apache Bench

Test your server and save the results:

```bash
ab -n 100 -c 5 https://example.com/ > ab-result.txt
```

---

### 3. Summarize Results

First, make the shell script executable:

```bash
sudo chmod +x summary.sh
```

Then run it to extract the summary:

```bash
./summary.sh ab-result.txt > ab-summary.txt
```

---

### 4. Generate Charts

Create beautiful charts from the summary:

```bash
python3 charts.py ab-summary.txt
```

- This script will generate image files (e.g., `ab-summary.png`) with clear, informative charts using matplotlib.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

:star: **If you found this useful, please star the repo!**

</div>
